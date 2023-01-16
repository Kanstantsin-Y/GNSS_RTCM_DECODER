
#--- Dependencies ---------------------------------------------------------------------------

from data_types.observables import ObservablesMSM
from data_types.observables import BareObservablesMSM4567

from utilities.bits import Bits  
from utilities.bits import catch_bits_exceptions
from utilities.CRC24Q import CRC24Q

from cons_file_logger import LOGGER_CF as logger

#--- Exceptions for upper level of RTCM decoder ---------------------------------------------

class ExceptionDecoderInit(Exception):
    '''Exception called during decoder initialization'''

class ExceptionDecoderDecode(Exception):
    '''Exception called during/after method ".decode()" executed '''

def catch_decoder_exceptions(func):
    """Decorator. Implements processing of decoder-related exceptions"""
    def catch_exception_wrapper(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        except ExceptionDecoderInit as di:
            logger.error(di.args[0])
        except ExceptionDecoderDecode as de:
            logger.warning(de.args[0])
        except Exception as ex:
             logger.error(f"{type(ex)}: {ex}")
        else:
            return rv

    return catch_exception_wrapper

#----------------------------------------------------------------------------------------------




#----------------------------------------------------------------------------------------------

_RTCM_MSG_SUBSETS : tuple[str,...] = ('UNDEF', 'LEGO', 'LEGE', 'MSM13O', 'MSM47O', 'MSME')

class DecoderTop():
    '''Combines decoders for RTCM message subsets and implements outer interface'''

    # bits = Bits()

    def __init__(self) -> None:
        self.decoders : dict[str, SubDecoderInterface] = dict()
        self._tail = b''
        self._skipped_some_bytes: bool = False
        self._synchronized: bool = False
        self.__pars_err_cnt: int = 0
        self.__dec_attempts: int = 0
        self.__dec_succeeded: int = 0

#--- RTCM decoding frame -----------------------------------------------------------------------------

    @catch_decoder_exceptions
    def register_decoder(self, new_decoder: object):
        '''Register new subset of decoded messages'''
        
        # Validate interface attributes
        if not 'io' in new_decoder.__dict__:
            raise ExceptionDecoderInit(f"No 'io' instance in sub-decoder {type(new_decoder)}")
        
        if not isinstance(new_decoder.io, SubDecoderInterface):
            raise ExceptionDecoderInit(f"Incorrect 'io' type in {type(new_decoder)}")

        if new_decoder.io.subset == 'UNDEF':
            raise ExceptionDecoderInit(f'Interface not defined in {type(new_decoder)}')

        if new_decoder.io.decode == SubDecoderInterface.default_decode:
            raise ExceptionDecoderInit(f"Virtual method 'decode' not defined in {type(new_decoder)}")

        if len(new_decoder.io.actual_messages) == 0:
            raise ExceptionDecoderInit(f"Empty message list. Update or delete subdecoder {type(new_decoder)}")

        self.decoders.update({new_decoder.io.subset:new_decoder.io})

        return

    @catch_decoder_exceptions
    def decode(self, msg: bytes):
        
        self.__dec_attempts += 1

        #Find decoder
        num = self.mnum(msg)
        dec = None
        for d in self.decoders.values():
            if num in d.io_spec.keys():
                dec = d
                break
        else:
            raise ExceptionDecoderDecode(f"Decoder not found, message {num}")

        if not num in dec.actual_messages:
            raise ExceptionDecoderDecode(f"Decoder {dec.subset} does not support message {num}")

        # Decode
        rv = dec.decode(msg)

        if rv != None:
            # Check result type 
            if not isinstance(rv, dec.io_spec[num]):
                raise ExceptionDecoderDecode(f"Decoder {dec.subset} returned unexpected result for msg {num}")
            
            self.__dec_succeeded += 1
        
        return rv

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

    


#----------------------------------------------------------------------------------------------

class SubDecoderInterface():
    ''' Sub decoder interface.
    
        Each instance of sub-decoder must implement an instance of
        'DecoderInterface' named 'io'.
        'io' defines:
            1. Required subset of RTCM messages to be supported in the sub-decoder -'io_spec.keys()'.
            2. Appropriate data types returned as a result of decoding - 'io_spec.values()'.
            3. Set of actually implemented messages - 'actual_messages'.
            3. Virtual method 'decode' which must be redefined in
            sub-decoder implementation.
    '''

    def __init__(self, subset:str = 'UNDEF', bare:bool = False) -> None:
                                
        match subset:
            case 'MSM47O':
                self.io_spec = self.__make_MSM47O_spec(bare)
            case 'MSM13O':
                self.io_spec = self.__make_MSM13O_spec(bare)
            case 'MSME':
                self.io_spec = self.__make_MSM13E_spec(bare)
            case 'LEGO':
                self.io_spec = self.__make_LEGO_spec(bare)
            case 'LEGE':
                self.io_spec = self.__make_LEGE_spec(bare)
            case _:
                self.io_spec = {}

        self.subset = subset if len(self.io_spec) else 'UNDEF'
        self.decode = self.default_decode
        self.actual_messages : set[int] = set()
    
    @staticmethod
    def default_decode(buf:bytes):
        '''Stub for virtual method decode()'''
        raise NotImplementedError(f"Virtual method 'decode' not defined")

    @staticmethod
    def __make_MSM47O_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of sub-decoder'''

        messages = (1074, 1075, 1076, 1077)
        messages = [m+i*10 for i in range (7) for m in messages]
        output_format = BareObservablesMSM4567 if bare else ObservablesMSM
        rv = dict().fromkeys(messages,output_format)
        return rv

    @staticmethod
    def __make_MSM13O_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of sub-decoder'''

        messages = (1071, 1072, 1073)
        messages = [m+i*10 for i in range (7) for m in messages]
        output_format = BareObservablesMSM4567 if bare else ObservablesMSM
        rv = dict().fromkeys(messages,output_format)
        return rv

    @staticmethod
    def __make_MSM13E_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of MSM ephemeris decoder'''
        return {}

    @staticmethod
    def __make_LEGO_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of Legacy observables decoder'''
        return {}
    
    @staticmethod
    def __make_LEGE_spec(bare:bool) -> dict:
        '''Defines IN/OUT interface of Legacy ephemeris decoder'''
        return {}



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