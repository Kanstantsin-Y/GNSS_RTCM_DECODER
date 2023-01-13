

__all__=['Bits','ExceptionBitsError','ExceptionBitsWrn','catch_bits_exceptions']

#--- Exceptions -----------------------------------------------------------------------------------

from cons_file_logger import LOGGER_CF as logger

class ExceptionBitsError(Exception):
    '''Hook error in Bits methods'''
    def process(self):
        logger.error(self.args[0])


def catch_bits_exceptions(func):
    """Decorator. Implements processing of exeptions in Bits methods"""
    def catch_exception_wrapper(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        except ExceptionBitsError as be:
            be.process()
        except Exception as ex:
             logger.error(f"{type(ex)}: {ex}")
        else:
            return rv
    return catch_exception_wrapper


#------------------------------------------------------------------------------------------------
        
class Bits(): 

    MAX_BIT_WIDTH = 128
    
    @classmethod
    def getbitu(cls, buf: bytes, start_pos: int, length: int)->int:
        '''Extracts unsigned data field from 'bytes' varable '''
        
        if (length < 1) or (length > cls.MAX_BIT_WIDTH) or (start_pos < 0):
            raise ExceptionBitsError(f'getbitu length:{length=},{start_pos=}')
            
        finish_pos = start_pos + length         # bits
        finish_byte = (finish_pos+7)>>3         # bytes
        start_byte = start_pos>>3               # bytes
        
        if finish_byte > len(buf):
            raise ExceptionBitsError(f'getbitu overshoot:{finish_byte=},len={len(buf)}')
        
        acc = int(0)
        for i in range(start_byte, finish_byte):
            acc = acc*256 + buf[i]
        # Clean extra bits
        acc = acc >> (finish_byte*8-finish_pos)
        mask = (int(1)<<length) - 1
        return acc & mask

    @classmethod
    def getbits(cls, buf: bytes, start_pos: int, length: int)->int:
        '''Extracts signed data field from 'bytes' varable'''
        
        acc = cls.getbitu(buf, start_pos, length)
        # Extend sign
        mask = int(1)<<(length - 1) # Selects sign
        acc = (acc^mask) - mask
        return acc

    @classmethod
    def revbitu(cls, a:int, length:int, ofs:int=0)->int:
        ''' Reverse bit order.
        Returns 'len' bits of 'a' starting from bit number 'ofs' in bit-reversed order'''
        
        if length + ofs > cls.MAX_BIT_WIDTH:
            raise ExceptionBitsError(f'revbitu index:len={length+ofs}')
            
        src = (a >> ofs)
        rv = 0
        for i in range(0,length):
            rv = (rv << 1) | (src & 1)
            src = src >> 1

        return rv

    @classmethod
    def revbits(cls, a:int, length:int, ofs:int=0)->int:
        ''' Reverse bit order and expand MSB bit as sign bit.
        Returns 'len' bits of 'a' starting from bit number 'ofs' in bit-reversed order'''

        rv = cls.revbitu(a, length, ofs)
        mask = 1<<(length-1)
        return (rv^mask) - mask

#------------------------------------------------------------------------------------------------


