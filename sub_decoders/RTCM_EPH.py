"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements subdecoder for ephemeris messages. Provides one DTO
    object per each message. Two types of DTOs can be returned optionally:
    1. Bare integer data (as it is in the message);
    2. Scaled and ready for futher computations parameters. Fields like:
       - binary flags
       - status codes
       - indexes (URA (GPS), Ft (GLONASS)) for tabled values
       are not scaled and shall be interpreted on the user side.
"""
import data_types.ephemerids as mEph

from data_types.ephemerids_test import getReferenceEphData

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
    
    def __scale1019(self, ie: mEph.GpsLNAV, decorate:bool = False) -> mEph.GpsLNAV:
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
        eph.TGD     = ie.TGD*(2**-31)               #DF101
        
        if decorate:
            eph.L2_Codes    = _L2_Codes[ie.L2_Codes]                    #DF078
            eph.URA         = ura(ie.URA)                               #DF077
            eph.SVH         = 'OK' if ie.SVH == 0 else ie.SVH           #DF102
            eph.L2P_Data    = 'ON' if ie.L2P_Data == 0 else 'OFF'      #DF103
            eph.Fit         = '=4h' if ie.Fit == 0 else '>4h'           #DF137
        else:
            eph.L2_Codes    = ie.L2_Codes
            eph.URA         = ie.URA
            eph.SVH         = ie.SVH
            eph.L2P_Data    = ie.L2P_Data
            eph.Fit         = ie.Fit
        
        return eph
    
    def getbitS(self, buf:bytes, offcet:int, length:int)->int:
        """Extract data from [s,m] field"""
        sgnMask = 1<<(length-1)
        magnMask = sgnMask-1
        d = self.getbitu(buf, offcet, length)
        magn = d & magnMask
        return magn if (d & sgnMask) == 0 else -magn
        
    def __decode1020(self, buf:bytes) -> mEph.GloL1L2|None:
        """Decode message 1020"""
          
        eph = mEph.GloL1L2()
        offset = 24
        eph.msgNum, offset      = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset      = self.getbitu(buf, offset, 6), offset+6    #DF038
        eph.frqSloNum, offset   = self.getbitu(buf, offset, 5), offset+5    #DF040
        eph.Cn, offset          = self.getbitu(buf, offset, 1), offset+1    #DF104
        eph.AlmHAI, offset      = self.getbitu(buf, offset, 1), offset+1    #DF105
        eph.P1, offset          = self.getbitu(buf, offset, 2), offset+2    #DF106
        eph.tk, offset          = self.getbitu(buf, offset, 12), offset+12  #DF107
        eph.BnMSB, offset       = self.getbitu(buf, offset, 1), offset+1    #DF108
        eph.P2, offset          = self.getbitu(buf, offset, 1), offset+1    #DF109
        eph.tb, offset          = self.getbitu(buf, offset, 7), offset+7    #DF110
        eph.dotXn, offset       = self.getbitS(buf, offset, 24), offset+24  #DF111
        eph.xn, offset          = self.getbitS(buf, offset, 27), offset+27  #DF112
        eph.dotDotXn, offset    = self.getbitS(buf, offset, 5), offset+5    #DF113
        eph.dotYn, offset       = self.getbitS(buf, offset, 24), offset+24  #DF114
        eph.yn, offset          = self.getbitS(buf, offset, 27), offset+27  #DF115
        eph.dotDotYn, offset    = self.getbitS(buf, offset, 5), offset+5    #DF116
        eph.dotZn, offset       = self.getbitS(buf, offset, 24), offset+24  #DF117
        eph.zn, offset          = self.getbitS(buf, offset, 27), offset+27  #DF118
        eph.dotDotZn, offset    = self.getbitS(buf, offset, 5), offset+5    #DF119
        eph.P3, offset          = self.getbitu(buf, offset, 1), offset+1    #DF120
        eph.gamma_n, offset     = self.getbitS(buf, offset, 11), offset+11  #DF121
        eph.P, offset           = self.getbitu(buf, offset, 2), offset+2    #DF122
        eph.ln3, offset         = self.getbitu(buf, offset, 1), offset+1    #DF123
        eph.tauN, offset        = self.getbitS(buf, offset, 22), offset+22  #DF124
        eph.delta_tauN, offset  = self.getbitS(buf, offset, 5), offset+5    #DF125
        eph.En, offset          = self.getbitu(buf, offset, 5), offset+5    #DF126
        eph.P4, offset          = self.getbitu(buf, offset, 1), offset+1    #DF127
        eph.Ft, offset          = self.getbitu(buf, offset, 4), offset+4    #DF128
        eph.Nt, offset          = self.getbitu(buf, offset, 11), offset+11  #DF129
        eph.M, offset           = self.getbitu(buf, offset, 2), offset+2    #DF130
        eph.auxDataOK, offset   = self.getbitu(buf, offset, 1), offset+1    #DF131
        eph.Na, offset          = self.getbitu(buf, offset, 11), offset+11  #DF132
        eph.tauC, offset        = self.getbitS(buf, offset, 32), offset+32  #DF133
        eph.N4, offset          = self.getbitu(buf, offset, 5), offset+5    #DF134
        eph.tauGPS, offset      = self.getbitS(buf, offset, 22), offset+22  #DF135
        eph.ln5, offset         = self.getbitu(buf, offset, 1), offset+1+7  #DF136

        # expected offset value is 360+24=384
        return eph
    
    def __scale1020(self, ie: mEph.GloL1L2) -> mEph.GloL1L2:
        """Scale MSG 1020 data"""

        #__FT = [1.0, 2.0, 2.5, 4.0, 5.0, 7.0, 10.0, 12.0, 14.0, 16.0, 32.0, 64.0, 128.0, 256.0, 512.0]
        #__P1 = [0, 30, 45, 60]

        eph = mEph.GloL1L2()
        eph.msgNum = ie.msgNum    
        eph.satNum = ie.satNum                      #DF038
        eph.frqSloNum = ie.frqSloNum - 7            #DF040  [-7..13]
        
        tk_h = 3600*((ie.tk>>7) & 0x1f)             #DF107
        tk_m = 60*((ie.tk>>1) & 0x3f)               #DF107
        tk_s = 30*(ie.tk & 0x01)                    #DF107
        eph.tk = tk_h + tk_m + tk_s                 # [s]

        eph.Cn = ie.Cn                              #DF104  [0-unhealthy, 1-healthy]
        eph.AlmHAI = ie.AlmHAI                      #DF105  [0/1, 1 - Cn is available] 
        eph.P1 = ie.P1                              #DF106  [s]
        eph.BnMSB = ie.BnMSB                        #DF108
        eph.P2 = ie.P2                              #DF109

        eph.tb = ie.tb*15*60                        #DF110 [s]

        eph.dotXn       = ie.dotXn*(2**-20)         #DF111  [km/s2]
        eph.xn          = ie.xn*(2**-11)            #DF112  [km/s]
        eph.dotDotXn    = ie.dotDotXn*(2**-30)      #DF113  [km/s3]

        eph.dotYn       = ie.dotYn*(2**-20)         #DF114  [km/s2]
        eph.yn          = ie.yn*(2**-11)            #DF115  [km/s]
        eph.dotDotYn    = ie.dotDotYn*(2**-30)      #DF116  [km/s3]

        eph.dotZn       = ie.dotZn*(2**-20)         #DF117  [km/s2]
        eph.zn          = ie.zn*(2**-11)            #DF118  [km/s]
        eph.dotDotZn    = ie.dotDotZn*(2**-30)      #DF119  [km/s3]

        eph.P3 = ie.P3                              #DF120 [0/1]
        eph.gamma_n = ie.gamma_n*(2**-40)           #DF121 [unitless]
        eph.P = ie.P                                #DF122 [0,1,2,3] [tauC,tauGPS] acquisition mode
        eph.ln3 = ie.ln3                            #DF123 [0/1, 0-healthy, 1-mulfunction]
        eph.tauN = ie.tauN*(2**-30)                 #DF124 [s]
        eph.delta_tauN = ie.delta_tauN*(2**-30)     #DF125 [s]
        eph.En = ie.En                              #DF126 [day]
        eph.P4 = ie.P4                              #DF127 [0/1] flag
        eph.Ft = ie.Ft                              #DF128 [m]
        eph.Nt = ie.Nt                              #DF129 [day]
        eph.M =  ie.M                               #DF130 [1-M, 2-K]
        eph.auxDataOK = ie.auxDataOK                #DF131 [0/1]
        eph.Na = ie.Na                              #DF132 [day]
        eph.tauC = ie.tauC*(2**-31)                 #DF133 [s]
        eph.N4 = ie.N4                              #DF134 [1..31] - 4-year interval
        eph.tauGPS = ie.tauGPS*(2**-30)             #DF135 [s]
        eph.ln5 = ie.ln5                            #DF136 [0/1]
        
        #return getReferenceEphData(ie.msgNum, ie.satNum)
        return eph
    
    
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



