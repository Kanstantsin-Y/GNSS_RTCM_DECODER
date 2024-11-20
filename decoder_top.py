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
        2.3 Defines virtual methods and attributes which should be implemented in sub-decoder.
"""




#--- Dependencies ---------------------------------------------------------------------------

import data_types.ephemerids as mEph

from data_types.observables import ObservablesMSM
from data_types.observables import BareObservablesMSM4567, BareObservablesMSM123

from utilities.bits import Bits  
from utilities.bits import catch_bits_exceptions
from utilities.CRC24Q import CRC24Q

from logger import LOGGER_CF as logger
from typing import Any

#----------------------------------------------------------------------------------------------

class SubDecoderInterface():
    ''' Sub decoder interface.
    
        Each instance of sub-decoder must implement an instance of
        'DecoderInterface' named for example 'io'. 'io' defines:
            1. Required subset of RTCM messages to be supported in the sub-decoder -'io_spec.keys()'.
            2. Appropriate data types returned as a result of decoding - 'io_spec.values()'.
            3. Set of actually implemented messages - 'actual_messages'.
            3. Virtual method 'decode' which must be redefined in
            sub-decoder implementation.
    '''

    @staticmethod
    def __make_MSM47O_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of sub-decoder'''

        messages: Any = (1074, 1075, 1076, 1077)
        messages = [m+i*10 for i in range (7) for m in messages]
        output_format = BareObservablesMSM4567 if bare else ObservablesMSM
        rv = dict().fromkeys(messages,output_format)
        return rv

    @staticmethod
    def __make_MSM13O_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of sub-decoder'''

        messages : Any = (1071, 1072, 1073)
        messages = [m+i*10 for i in range (7) for m in messages]
        output_format = BareObservablesMSM123 if bare else ObservablesMSM
        rv = dict().fromkeys(messages,output_format)
        return rv

    @staticmethod
    def __make_EPH_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of ephemeris decoder'''

        # Same types are used for bare/scaled data
        rv = {  1045: mEph.GalFNAV,
                1046: mEph.GalINAV,
                1020: mEph.GloL1L2,
                1019: mEph.GpsLNAV,
                1044: mEph.QzssL1,
                1042: mEph.BdsD1,
                1041: mEph.NavicL5 }
        return rv


    @staticmethod
    def __make_LEGO_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of Legacy observables decoder'''
        return {}

    @staticmethod
    def default_decode(buf:bytes):
        '''Stub for virtual method decode()'''
        raise NotImplementedError(f"Virtual method 'decode' not defined")

    _RTCM_MSG_SUBSETS = {
        'LEGO' : __make_LEGO_spec,
        'MSM13O' : __make_MSM13O_spec,
        'MSM47O' : __make_MSM47O_spec,
        'EPH' : __make_EPH_spec
    }

    def __init__(self, subset:str , bare:bool = False) -> None:
        
        spec_generator = self._RTCM_MSG_SUBSETS.get(subset)
        assert spec_generator != None, f"Sub-decoder {subset} not found."
        
        self.decode = self.default_decode
        self.io_spec = spec_generator(bare)
        self.subset = subset
        self.actual_messages : set[int] = set()
        return
    
    
#--- Exceptions for upper level of RTCM decoder ---------------------------------------------

# class ExceptionDecoderInit(Exception):
#     '''Exception called during decoder initialization'''

class ExceptionDecoderDecode(Exception):
    '''Exception called during/after method ".decode()" executed '''

def catch_decoder_exceptions(func):
    """Decorator. Implements processing of decoder-related exceptions"""
    def catch_exception_wrapper(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        # except ExceptionDecoderInit as di:
        #     logger.error(di.args[0])
        except ExceptionDecoderDecode as de:
            logger.warning(de.args[0])
        except Exception as ex:
             logger.error(f"{type(ex)}: {ex}")
        else:
            return rv

    return catch_exception_wrapper

#----------------------------------------------------------------------------------------------

class DecoderTop():
    '''Combines decoders for RTCM message subsets and implements outer interface'''

    def __init__(self) -> None:
        self.decoders : dict[str, SubDecoderInterface] = dict()
        self._tail = b''
        self._skipped_some_bytes: bool = False
        self._synchronized: bool = False
        self.__pars_err_cnt: int = 0
        self.__dec_attempts: int = 0
        self.__dec_succeeded: int = 0
        #self.TG = TestDataGrabber() - used for saving rtcm3 samples
        return

#--- RTCM decoding frame -----------------------------------------------------------------------------

    def register_decoder(self, io: SubDecoderInterface) -> bool:
        '''Register new subset of decoded messages'''
        
        rv = False

        # Validate interface attributes
        if not isinstance(io, SubDecoderInterface):
            logger.error(f"Incorrect 'io' type in {type(io)}")
        elif io.decode == SubDecoderInterface.default_decode:
            logger.error(f"Virtual method 'decode' not defined in {type(io)}")
        elif len(io.actual_messages) == 0:
            logger.error(f"Empty message list. Update or delete subdecoder {type(io)}")
        else:
            self.decoders.update({io.subset:io})
            rv = True

        return rv    

    @catch_decoder_exceptions
    def decode(self, msg: bytes):
        
        # Find decoder
        num = self.mnum(msg)
        dec = None

        #self.TG.save_eph(num,msg)

        for dec in self.decoders.values():
            if (num in dec.io_spec.keys()) and (num in dec.actual_messages):
                # Decode
                self.__dec_attempts += 1
                rv = dec.decode(msg)
                if isinstance(rv, dec.io_spec[num]):
                    self.__dec_succeeded += 1
                    return rv
                else:
                    raise ExceptionDecoderDecode(f"Decoder {dec.subset} returned unexpected result for msg {num}")
        else:
            logger.info(f"Decoder not found, message {num}")


#--- RTCM parsing frame -----------------------------------------------------------------------------

    def catch_message(self, chunk: bytes):
        'Accept sequential bytes flow. Find and return RTCM messages'
        
        ret_list = []
        self._tail = b''.join([self._tail, chunk])
        search_finished = (self._tail == b'')
        
        while not search_finished:

            tail_0 = len(self._tail)
            # Check/move synchro byte to [0] position
            tail_length = self.__rebase_to_D3()

            # Check, whether any bytes were skipped after synch had already happened
            if (not self._skipped_some_bytes) and (tail_length < tail_0) and (self._synchronized):
                self._skipped_some_bytes = True
                self._synchronized = False # re-synched and CRC not checked

            # Check, whether full message available 
            if tail_length < 6: # not enough data to decode
                search_finished = True
            else:
                msg_length = self.mlen(self._tail)
                search_finished = (msg_length > tail_length)
            
            # Check CRC
            if not search_finished:
                if self.mcrc(self._tail):
                    # Extract message
                    ret_list.append(self._tail[0:msg_length])
                    self._tail = self._tail[msg_length:]
                    # Check, if there were any errors before this message
                    # Anomalies between messages with successive CRC encountered
                    # Anomalies before the first and after the last successive CRC are skipped 
                    if (self._skipped_some_bytes):
                        self.__pars_err_cnt += 1
                        self._skipped_some_bytes = False
                    # Set synchro mark
                    self._synchronized = True
                else:
                    # Shift out 'D3' and go to the next iteration.
                    # Error will be encountered during the next iteration
                    self._tail = self._tail[1:]
        else:
            pass

        return ret_list

#................................................................................

    def __rebase_to_D3(self):
        '''Finds first RTCM synchro byte.

        If exists, all data before first synchro byte would be deleted,
        returns length of the new chunk.
        Else, deletes all data, returns 0.
        '''
        if self._tail == b'':
            return 0

        tail_len = len(self._tail)
        synch_ok = (self._tail[0] == 0xd3)

        # Trivial case.
        if (tail_len == 1):
            return 1 if synch_ok else 0
        
        # Have some more data. Check additional 6 bits
        if synch_ok and (self._tail[1] & 0xfc) != 0:
            synch_ok = False
                   
        if synch_ok:
            return tail_len
        
        # Acquire 'D3' byte. Main search loop
        ptr = 1
        while not synch_ok:
            ofs = self._tail.find(bytes.fromhex('D3'), ptr)
            if ofs == -1:
                self._tail = b''
                break
            elif ofs == tail_len-1:
                self._tail = self._tail[ofs:ofs+1] # !!! use 'byte' notation
                synch_ok = True
            else:                
                if (self._tail[ofs+1] & 0xfc) == 0:
                    self._tail = self._tail[ofs:] # <-- rebase left border to 'D3' 
                    synch_ok = True
                else:   # skip this "0xD3", find next one
                    ptr = ofs + 1
        else:
            pass

        return len(self._tail)

    @property
    def parse_errors(self):
        '''Returns number of errors on message extraction stage'''
        return self.__pars_err_cnt
    
    @property
    def dec_errors(self):
        '''Returns number of errors on message decoding stage'''
        return self.__dec_attempts - self.__dec_succeeded
    
    @property
    def dec_attempts(self):
        '''Returns total number of decoding attempt'''
        return self.__dec_attempts
    
#----------------------------------------------------------------------------------------------

    @staticmethod
    @catch_bits_exceptions
    def mnum(buf:bytes)->int:
        return Bits.getbitu(buf, 24, 12)

    @staticmethod
    @catch_bits_exceptions
    def mlen(buf:bytes)->int:
        '''Returns full length of RTCM message'''
        return Bits.getbitu(buf, 14, 10) + 6

    @staticmethod
    @catch_bits_exceptions
    def mcrc(buf:bytes)->bool:
        '''Check, whether buf contains full and valid RTCM message.'''        
        data_len = Bits.getbitu(buf, 14, 10) +3
        crc_calc = CRC24Q.calc(buf[0:data_len])
        crc_get = Bits.getbitu(buf, data_len*8, 24)
        return crc_calc == crc_get

#----------------------------------------------------------------------------------------------


class TestDataGrabber():

    def __init__(self):
        self.scenario = {
            1019: {'fname':'msg1019.rtcm3', 'cnt':3, 'fp':None},
            1020: {'fname':'msg1020.rtcm3', 'cnt':3, 'fp':None},
            1041: {'fname':'msg1041.rtcm3', 'cnt':3, 'fp':None},
            1042: {'fname':'msg1042.rtcm3', 'cnt':3, 'fp':None},
            1044: {'fname':'msg1044.rtcm3', 'cnt':3, 'fp':None},
            1045: {'fname':'msg1045.rtcm3', 'cnt':3, 'fp':None},
            1046: {'fname':'msg1046.rtcm3', 'cnt':3, 'fp':None}
        }

    def save_eph(self, mNum:int, msg:bytes):
        """Save a messages from the input flow to file."""

        s = self.scenario.get(mNum)
        if not s:
            return
        
        if s['cnt'] == 0:
            return
        
        if s['fp'] == None:
            s['fp'] = open(s['fname'],'wb')

        s['fp'].write(msg)
        s['fp'].flush()
        s['cnt'] -= 1
        
        if s['cnt'] == 0:
            s['fp'].close()

        


# def _save_some_test_data(msg_list):
#     '''Utility function. Accepts a bunch or RTCM messages.
#         Makes some test files.'''

#     f = open('reference-3msg.rtcm3','wb')
#     f.write(b''.join([msg_list[0], msg_list[1], msg_list[2]]))
#     f.close()

#     f = open('reference-3msg-interleaved.rtcm3','wb')
#     f.write(b'-'.join([msg_list[0], msg_list[1], msg_list[2]]))
#     f.close()

#     f = open('reference-3msg-noiseBefore.rtcm3','wb')
#     f.write(b''.join([b'abra-cadabra', msg_list[0], msg_list[1], msg_list[2]]))
#     f.close()

#     f = open('reference-3msg-noiseAfter.rtcm3','wb')
#     f.write(b''.join([msg_list[0], msg_list[1], msg_list[2], b'abra-cadabra']))
#     f.close()
    
#     f = open('reference-3msg-1brokenCRC.rtcm3','wb')
#     a = bytearray(msg_list[0])
#     a[-1:] = b'0'
#     a[-2:-1] = b'0'
#     f.write(b''.join([a,msg_list[1],msg_list[2]]))
#     f.close()
    
#     f = open('reference-3msg-2brokenCRC.rtcm3','wb')
#     a = bytearray(msg_list[0])
#     a[-1:] = b'0'
#     a[-2:-1] = b'0'
#     b = bytearray(msg_list[1])
#     b[-5:-4] = b'0'
#     b[-6:-5] = b'0'
#     f.write(b''.join([a,b,msg_list[2]]))
#     f.close()