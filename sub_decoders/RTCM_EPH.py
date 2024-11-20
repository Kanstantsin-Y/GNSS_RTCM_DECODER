"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements subdecoder which transforms RTCM3 MSM message into a DTO
    object with ephemerids. Two types of DTOs can be returned optinally:
    1. Bare integer data (as it is in the message);
    2. Scaled and ready for futher computations parameters. 
"""
import data_types.ephemerids as mEph

from decoder_top import SubDecoderInterface
from typing import Any
from utilities.bits import Bits
from utilities.bits import ExceptionBitsError
from utilities.bits import catch_bits_exceptions
from logger import LOGGER_CF as logger



#--- Exceptions ----------------------------------------------------------------------------------

# class ExceptionBareEphStructure(Exception):
#     '''Hook error in BareEpemerisDecoder methods'''

#------------------------------------------------------------------------------------------------
    
class EphemerisDecoder(Bits):
    '''Methods to extract bare data from ephemeris message'''

    def __init__(self) -> None:
        super().__init__()
        self.msgList = (1019,1020,1041,1042,1044,1045,1046)
        
    #@catch_bits_exceptions
    def get_msg_num(self, buf: bytes) -> int:
        return self.getbitu(buf, 24, 12)
        
    def __decode1019(self, buf:bytes) -> mEph.GpsLNAV|None:
        """Decode message 1019"""

        eph = mEph.GpsLNAV()
        offset = 24
        eph.msgNum, offset      = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset      = self.getbitu(buf, offset, 6), offset+6         #DF009
        eph.weekNum, offset     = self.getbitu(buf, offset, 10), offset+10       #DF076
        eph.URA, offset         = self.getbitu(buf, offset, 4), offset+4         #DF077
        eph.L2_Codes, offset    = self.getbitu(buf, offset, 2), offset+2         #DF078
        eph.i_dot, offset       = self.getbits(buf, offset, 14), offset+14       #DF079
        eph.IODE, offset        = self.getbitu(buf, offset, 8), offset+8         #DF071
        eph.tc, offset          = self.getbitu(buf, offset, 16), offset+16       #DF081
        eph.af2, offset         = self.getbits(buf, offset, 8), offset+8         #DF082
        eph.af1, offset         = self.getbits(buf, offset, 16), offset+16       #DF083
        eph.af0, offset         = self.getbits(buf, offset, 22), offset+22       #DF084
        eph.IODC, offset        = self.getbitu(buf, offset, 10), offset+10       #DF085
        eph.crs, offset         = self.getbits(buf, offset, 16), offset+16       #DF086
        eph.delta_n, offset     = self.getbits(buf, offset, 16), offset+16       #DF087
        eph.m0, offset          = self.getbits(buf, offset, 32), offset+32       #DF088
        eph.cuc, offset         = self.getbits(buf, offset, 16), offset+16       #DF089
        eph.e, offset           = self.getbitu(buf, offset, 32), offset+32       #DF090
        eph.cus, offset         = self.getbits(buf, offset, 16), offset+16       #DF091
        eph.sqrt_a, offset      = self.getbitu(buf, offset, 32), offset+32       #DF092
        eph.te, offset          = self.getbitu(buf, offset, 16), offset+16       #DF093
        eph.cic, offset         = self.getbits(buf, offset, 16), offset+16       #DF094
        eph.omega0, offset      = self.getbits(buf, offset, 32), offset+32       #DF095
        eph.cis, offset         = self.getbits(buf, offset, 16), offset+16       #DF096
        eph.i0, offset          = self.getbits(buf, offset, 32), offset+32       #DF097
        eph.crc, offset         = self.getbits(buf, offset, 16), offset+16       #DF098
        eph.w, offset           = self.getbits(buf, offset, 32), offset+32       #DF099
        eph.omega_dot, offset   = self.getbits(buf, offset, 24), offset+24       #DF100
        eph.TGD, offset         = self.getbits(buf, offset, 8), offset+8         #DF101
        eph.SVH, offset         = self.getbitu(buf, offset, 6), offset+6         #DF102
        eph.L2PD_Flag, offset   = self.getbitu(buf, offset, 1), offset+1         #DF103
        eph.Fit, offset         = self.getbitu(buf, offset, 1), offset+1         #DF137

        return eph if offset == 488+24 else None
    
    def __scale1019(self, ie: mEph.GpsLNAV) -> mEph.GpsLNAV:
        """Scale and beautify MSG 1019 data"""
        _L2_Codes = {0:'RS', 1:'P', 2:'CA', 3:'L2C'}

        def ura(iURA:int) -> float:
            """Convert URA index to value"""
            if iURA <= 6:
                return 2**(1+iURA*0.5)
            elif iURA < 15:
                return 2**(iURA-2.0)
            else:
                return 6144.0 

        eph = mEph.GpsLNAV()
        eph.msgNum = ie.msgNum
        eph.satNum  = ie.satNum                     #DF009
        eph.weekNum = ie.weekNum                    #DF076
        eph.URA     = ura(ie.URA)                   #DF077
        eph.L2_Codes= _L2_Codes[ie.L2_Codes]        #DF078
        eph.i_dot   = ie.i_dot*(2**-43)             #DF079
        eph.IODE    = ie.IODE                       #DF071
        eph.tc      = ie.tc*16                      #DF081
        eph.af2     = ie.af2*(2**-55)               #DF082
        eph.af1     = ie.af1*(2**-43)               #DF083
        eph.af0     = ie.af0*(2**-31)               #DF084
        eph.IODC    = ie.IODC                       #DF085
        eph.crs     = ie.crs*(2**-5)                #DF086
        eph.delta_n = ie.delta_n*(2**-43)           #DF087
        eph.m0      = ie.m0*(2**-31)                #DF088
        eph.cuc     = ie.cuc*(2**-29)               #DF089
        eph.e       = ie.e*(2**-33)                 #DF090
        eph.cus     = ie.cus*(2**-29)               #DF091
        eph.sqrt_a  = ie.sqrt_a*(2**-19)            #DF092
        eph.te      = ie.te*16                      #DF093
        eph.cic     = ie.cic*(2**-29)               #DF094
        eph.omega0  = ie.omega0*(2**-31)            #DF095
        eph.cis     = ie.cis*(2**-29)               #DF096
        eph.i0      = ie.i0*(2**-31)                #DF097
        eph.crc     = ie.crc*(2**-5)                #DF098
        eph.w       = ie.w*(2**-31)                 #DF099
        eph.omega_dot = ie.omega_dot*(2**-43)       #DF100
        eph.TGD     = ie.TGD*(2**-31)                               #DF101
        eph.SVH         = 'OK' if ie.SVH == 0 else ie.SVH           #DF102
        eph.L2P_Data    = 'ON' if ie.L2PD_Flag == 0 else 'OFF'      #DF103
        eph.Fit         = '=4h' if ie.Fit == 0 else '>4h'           #DF137

        return eph
    
    
    def __decode1020(self, buf:bytes) -> mEph.GloL1L2|None:
        """Decode message 1020"""
        eph = mEph.GloL1L2()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6
        return eph
    
    def __scale1020(self, iEph: mEph.GloL1L2) -> mEph.GloL1L2:
        """Scale and beautify MSG 1020 data"""

        return iEph
    
    
    def __decode1041(self, buf:bytes) -> mEph.NavicL5|None:
        """Decode message 1041"""
        eph = mEph.NavicL5()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6
        return eph
    
    def __scale1041(self, iEph: mEph.NavicL5) -> mEph.NavicL5:
        """Scale and beautify MSG 1041 data"""

        return iEph
    

    def __decode1042(self, buf:bytes) -> mEph.BdsD1|None:
        """Decode message 1042"""
        eph = mEph.BdsD1()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6
        return eph
    
    def __scale1042(self, iEph: mEph.BdsD1) -> mEph.BdsD1:
        """Scale and beautify MSG 1042 data"""

        return iEph
    

    def __decode1044(self, buf:bytes) -> mEph.QzssL1|None:
        """Decode message 1044"""
        eph = mEph.QzssL1()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 4), offset+4
        return eph
    
    def __scale1044(self, iEph: mEph.QzssL1) -> mEph.QzssL1:
        """Scale and beautify MSG 1044 data"""

        return iEph
    

    def __decode1045(self, buf:bytes) -> mEph.GalFNAV|None:
        """Decode message 1045"""
        eph = mEph.GalFNAV()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6
        return eph
    
    def __scale1045(self, iEph: mEph.GalFNAV) -> mEph.GalFNAV:
        """Scale and beautify MSG 1045 data"""

        return iEph
    
    def __decode1046(self, buf:bytes) -> mEph.GalINAV|None:
        """Decode message 1046"""
        eph = mEph.GalINAV()
        offset = 24
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6
        return eph

    def __scale1046(self, iEph: mEph.GalINAV) -> mEph.GalINAV:
        """Scale and beautify MSG 1046 data"""

        return iEph
    
    
    def decode(self, buf:bytes, is_bare_output:bool = False) -> Any|None:
        """Process ephemeris message"""
        
        try:

            msgNum = self.get_msg_num(buf)

            if msgNum == 1019:
                ephBlock = self.__decode1019(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1019(ephBlock)
            elif msgNum == 1020:
                ephBlock = self.__decode1020(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1020(ephBlock)
            elif msgNum == 1041:
                ephBlock = self.__decode1041(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1041(ephBlock)
            elif msgNum == 1042:
                ephBlock = self.__decode1042(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1042(ephBlock)
            elif msgNum == 1044:
                ephBlock = self.__decode1044(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1044(ephBlock)
            elif msgNum == 1045:
                ephBlock = self.__decode1045(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1045(ephBlock)
            elif msgNum == 1046:
                ephBlock = self.__decode1046(buf)
                if ephBlock and is_bare_output == False:
                    ephBlock = self.__scale1046(ephBlock)
            else:
                ephBlock = None
                logger.warning(f'Msg {msgNum}. Selected decoder doesn\'t support this message.')
        
        except ExceptionBitsError as ex:
            logger.error(f"Msg {msgNum}. Decoding failed. " + ex.args[0])
        except IndexError as ie:
            logger.error(f"Msg {msgNum}. Decoding failed. Indexing error: {type(ie)}: {ie}")
        except ArithmeticError as ae:
            logger.error(f"Msg {msgNum}. Decoding failed. Arithm error: {type(ae)}: {ae}")
        except Exception as ex:
            logger.error(f"Msg {msgNum}. Decoding failed. Unexpected error:" + f"{type(ex)}: {ex}")
        else:
            pass

        if ephBlock:
            logger.info(f'Msg {msgNum}. Decoding succeeded. SV = {ephBlock.satNum}.')

        return ephBlock




class SubdecoderEph():
    '''Implements decoding of RTCM ephemeris messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__bare_data = bare_data
        self.decoder = EphemerisDecoder()
        self.io = SubDecoderInterface('EPH', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = self.decoder.msgList
        

    def decode(self, buf:bytes) -> Any | None:
        return self.decoder.decode(buf, self.__bare_data)



