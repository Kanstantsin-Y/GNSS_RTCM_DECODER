"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements classes:
    1. DecoderTop(). Top level of RTCM decoder. Implements 2 main tasks:
        1.1 Scans RTCM3 byte flow, extracts messages.
        2.2 Aggregates sub-decoders, finds and calls appropriate decoding method
        for each message.
    2. SubDecoderInterface().
        2.1 Specifies available sub-decoders.
        2.2 Specifies list of RTCM messages for each sub-decoder.
        2.3 Defines virtual methods and attributes to be implemented in sub-decoder.
"""

# pylint: disable = invalid-name

# --- Dependencies ---------------------------------------------------------------------------
from typing import Any

from gnss_types import *  # pylint: disable = unused-wildcard-import,wildcard-import
from logger import LOGGER_CF as logger
from utilities import Bits
from utilities import catch_bits_exceptions
from utilities import CRC24Q
from tests.test_utilities import TestDataGrabber as TDG

# Use this switch to cut and safe some messages from the
# input data flow. Set 'EPH' / 'BASE' / 'MSM7' / 'MSM5' / None (to disable).
TEST_DATA_GRABBER = None
# ----------------------------------------------------------------------------------------------


class SubDecoderInterface:
    """Sub decoder interface.

    Each instance of sub-decoder must implement an instance of
    'DecoderInterface' named for example 'io'. 'io' defines:
        1. Required subset of RTCM messages to be supported in the sub-decoder -'io_spec.keys()'.
        2. Appropriate data types returned as a result of decoding - 'io_spec.values()'.
        3. Set of actually implemented messages - 'actual_messages'.
        3. Virtual method 'decode' which must be redefined in
        sub-decoder implementation.
    """

    @staticmethod
    def __make_MSM47O_spec(bare: bool) -> dict:
        """Defines IN/OUT interface of sub-decoder"""

        messages: Any = (1074, 1075, 1076, 1077)
        messages = [m + i * 10 for i in range(7) for m in messages]
        output_format = BareObservablesMSM4567 if bare else ObservablesMSM
        rv = dict().fromkeys(messages, output_format)
        return rv

    @staticmethod
    def __make_MSM13O_spec(bare: bool) -> dict:
        """Defines IN/OUT interface of sub-decoder"""

        messages: Any = (1071, 1072, 1073)
        messages = [m + i * 10 for i in range(7) for m in messages]
        output_format = BareObservablesMSM123 if bare else ObservablesMSM
        rv = dict().fromkeys(messages, output_format)
        return rv

    @staticmethod
    def __make_EPH_spec(bare: bool) -> dict:
        """Defines IN/OUT interface of ephemeris decoder"""

        # Same types are used for bare/scaled data
        rv = {
            1045: EphGALF,
            1046: EphGALI,
            1020: EphGLO,
            1019: EphGPS,
            1044: EphQZS,
            1042: EphBDS,
            1041: EphNAVIC,
        }
        return rv if bare else rv

    @staticmethod
    def __make_BASE_spec(bare: bool) -> dict:
        """Defines IN/OUT interface of Base Station Data decoder"""

        # Same types are used for bare/scaled data
        rv = {
            1005: BaseRP,
            1006: BaseRPH,
            1007: BaseAD,
            1008: BaseADSN,
            1033: BaseADSNRC,
            1013: BaseSP,
            1029: BaseTS,
            1230: BaseGLBS,
        }

        return rv if bare else rv

    @staticmethod
    def __make_LEGO_spec(
        bare: bool,  # pylint: disable = unused-argument
    ) -> dict:
        """Defines IN/OUT interface of Legacy observables decoder"""
        return {}

    @staticmethod
    def default_decode(buf: bytes):
        """Stub for virtual method decode()"""
        raise NotImplementedError("Virtual method 'decode' not defined")

    _RTCM_MSG_SUBSETS = {
        "LEGO": __make_LEGO_spec,
        "MSM13O": __make_MSM13O_spec,
        "MSM47O": __make_MSM47O_spec,
        "EPH": __make_EPH_spec,
        "BASE": __make_BASE_spec,
    }

    def __init__(self, subset: str, bare: bool = False):

        spec_generator = self._RTCM_MSG_SUBSETS.get(subset)
        assert spec_generator is not None, f"Sub-decoder {subset} not found."

        self.decode = self.default_decode
        self.io_spec = spec_generator(bare)
        self.subset = subset
        self.actual_messages: set[int] = set()


# ----------------------------------------------------------------------------------------------


class ExceptionDecoderDecode(Exception):
    """Exception called during/after method ".decode()" executed"""


def catch_decoder_exceptions(func):
    """Decorator. Implements processing of decoder-related exceptions"""

    def catch_exception_wrapper(*args, **kwargs) -> object | None:
        rv = None
        try:
            rv = func(*args, **kwargs)
        except ExceptionDecoderDecode as de:
            logger.warning(de.args[0])
        except Exception as ex:  # pylint: disable = broad-exception-caught
            logger.error(f"{type(ex)}: {ex}")

        return rv

    return catch_exception_wrapper


class DecoderTop:
    """Combines decoders for RTCM message subsets and implements outer interface"""

    def __init__(self) -> None:
        self.decoders: dict[str, SubDecoderInterface] = dict()
        self._tail = b""
        self._skipped_some_bytes: bool = False
        self._synchronized: bool = False
        self.__pars_err_cnt: int = 0
        self.__dec_attempts: int = 0
        self.__dec_succeeded: int = 0
        if TEST_DATA_GRABBER is not None:
            # used for grabbing and saving rtcm3 samples
            self._TDG = TDG()

    # --- RTCM decoding frame -----------------------------------------------------------

    def register_decoder(self, io: SubDecoderInterface) -> bool:
        """Register new subset of decoded messages"""

        rv = False

        # Validate interface attributes
        if not isinstance(io, SubDecoderInterface):
            logger.error(f"Incorrect 'io' type in {type(io)}")
        elif io.decode == SubDecoderInterface.default_decode:
            logger.error(f"Virtual method 'decode' not defined in {type(io)}")
        elif len(io.actual_messages) == 0:
            logger.error(
                f"Empty message list. Update or delete subdecoder {type(io)}"
            )
        else:
            self.decoders.update({io.subset: io})
            rv = True

        return rv

    @catch_decoder_exceptions
    def decode(self, msg: bytes) -> object | None:
        """Find sub-decoder and decode message"""

        # Find decoder
        num = self.mnum(msg)
        dec = None
        rv = None

        if TEST_DATA_GRABBER is not None:
            self._TDG.save(num, msg, TEST_DATA_GRABBER)

        for dec in self.decoders.values():
            if (num in dec.io_spec.keys()) and (num in dec.actual_messages):
                # Decode
                self.__dec_attempts += 1
                rv = dec.decode(msg)
                if not isinstance(rv, dec.io_spec[num]):
                    raise ExceptionDecoderDecode(
                        f"Decoder {dec.subset} returned unexpected result for msg {num}"
                    )
                self.__dec_succeeded += 1
                break
        else:
            logger.info(f"Decoder not found, message {num}")

        return rv

    # --- RTCM parsing frame -----------------------------------------------------------

    def catch_message(self, chunk: bytes):
        "Accept sequential bytes flow. Find and return RTCM messages"

        ret_list = []
        self._tail = b"".join([self._tail, chunk])
        search_finished = self._tail == b""

        while not search_finished:

            tail_0 = len(self._tail)
            # Check/move synchro byte to [0] position
            tail_length = self.__rebase_to_D3()

            # Check, whether any bytes were skipped after synch had already happened
            if (
                (not self._skipped_some_bytes)
                and (tail_length < tail_0)
                and (self._synchronized)
            ):
                self._skipped_some_bytes = True
                self._synchronized = False  # re-synched and CRC not checked

            # Check, whether full message available
            if tail_length < 6:  # not enough data to decode
                search_finished = True
                msg_length = 0
            else:
                msg_length = self.mlen(self._tail)
                search_finished = msg_length > tail_length

            # Check CRC
            if not search_finished:
                if self.mcrc(self._tail):
                    # Extract message
                    ret_list.append(self._tail[0:msg_length])
                    self._tail = self._tail[msg_length:]
                    # Check, if there were any errors before this message
                    # Anomalies between messages with successive CRC encountered
                    # Anomalies before the first and after the last successive CRC are skipped
                    if self._skipped_some_bytes:
                        self.__pars_err_cnt += 1
                        self._skipped_some_bytes = False
                    # Set synchro mark
                    self._synchronized = True
                else:
                    # Shift out 'D3' and go to the next iteration.
                    # Error will be encountered during the next iteration
                    self._tail = self._tail[1:]

        return ret_list

    # ................................................................................

    def __rebase_to_D3(self):
        """Finds first RTCM synchro byte.

        If exists, all data before first synchro byte would be deleted,
        returns length of the new chunk.
        Else, deletes all data, returns 0.
        """
        if self._tail == b"":
            return 0

        tail_len = len(self._tail)
        synch_ok = self._tail[0] == 0xD3

        # Trivial case.
        if tail_len == 1:
            return 1 if synch_ok else 0

        # Have some more data. Check additional 6 bits
        if synch_ok and (self._tail[1] & 0xFC) != 0:
            synch_ok = False

        if synch_ok:
            return tail_len

        # Acquire 'D3' byte. Main search loop
        ptr = 1
        while not synch_ok:
            ofs = self._tail.find(bytes.fromhex("D3"), ptr)
            if ofs == -1:
                self._tail = b""
                break
            elif ofs == tail_len - 1:
                self._tail = self._tail[ofs : ofs + 1]
                synch_ok = True
            else:
                if (self._tail[ofs + 1] & 0xFC) == 0:
                    # rebase left border to 'D3'
                    self._tail = self._tail[ofs:]
                    synch_ok = True
                else:  # skip this "0xD3", find next one
                    ptr = ofs + 1
        else:
            pass

        return len(self._tail)

    @property
    def parse_errors(self):
        """Returns number of errors on message extraction stage"""
        return self.__pars_err_cnt

    @property
    def dec_errors(self):
        """Returns number of errors on message decoding stage"""
        return self.__dec_attempts - self.__dec_succeeded

    @property
    def dec_attempts(self):
        """Returns total number of decoding attempt"""
        return self.__dec_attempts

    # ----------------------------------------------------------------------------------------------

    @staticmethod
    @catch_bits_exceptions
    def mnum(buf: bytes) -> int:
        """Ëxtract message number"""
        return Bits.getbitu(buf, 24, 12)

    @staticmethod
    @catch_bits_exceptions
    def mlen(buf: bytes) -> int:
        """Returns full length of RTCM message"""
        return Bits.getbitu(buf, 14, 10) + 6

    @staticmethod
    @catch_bits_exceptions
    def mcrc(buf: bytes) -> bool:
        """Check, whether buf contains full and valid RTCM message."""
        data_len = Bits.getbitu(buf, 14, 10) + 3
        crc_calc = CRC24Q.calc(buf[0:data_len])
        crc_get = Bits.getbitu(buf, data_len * 8, 24)
        return crc_calc == crc_get
