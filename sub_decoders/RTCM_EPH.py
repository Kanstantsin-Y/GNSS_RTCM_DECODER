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
import gnss_types as mEph

from decoder_top import SubDecoderInterface
from typing import Any
from utilities import Bits
from utilities import ExceptionBitsError
from logger import LOGGER_CF as logger


#--- Exceptions ----------------------------------------------------------------------------------

class ExceptionEphemerisDecoder(Exception):
    '''Hook error in EphemerisDecoder methods'''

#------------------------------------------------------------------------------------------------
    
class EphemerisDecoder(Bits):
    '''Methods to extract bare data from ephemeris message'''

    def __init__(self) -> None:
        super().__init__()
        self.msgList = (1019,1020,1041,1042,1044,1045,1046)
        
    def get_msg_num(self, buf: bytes) -> int:
        return self.getbitu(buf, 24, 12)
    
    @staticmethod
    def __length_check(Nexp:int, Ndec:int, bufLen:int):
        """Validate message length"""

        if Ndec != Nexp:
            raise ExceptionEphemerisDecoder(f'data field length error: {Ndec} vs {Nexp}')
       
        Ndec = 6 + ((Ndec+7)>>3)
        if Ndec != bufLen:
            raise ExceptionEphemerisDecoder(f'message length error: {bufLen} vs {Ndec}')

        
    def __decode1019(self, buf:bytes) -> mEph.GpsLNAV:
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
        
        #expected offcet value is 488+24 = 512
        self.__length_check(488,offset-24,len(buf))
        
        return eph
    
    @classmethod
    def __scale1019(cls, ie: mEph.GpsLNAV, decorate:bool = False) -> mEph.GpsLNAV:
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
        eph.weekNum = ie.weekNum                    #DF076 [0..1023]
        eph.i_dot   = ie.i_dot*(2**-43)             #DF079 [hc/sec]
        eph.IODE    = ie.IODE                       #DF071 [0..255]
        eph.tc      = ie.tc*16                      #DF081 [sec]
        eph.af2     = ie.af2*(2**-55)               #DF082 [sec/sec/sec]
        eph.af1     = ie.af1*(2**-43)               #DF083 [sec/sec]
        eph.af0     = ie.af0*(2**-31)               #DF084 [sec]
        eph.IODC    = ie.IODC                       #DF085 [0..1023]
        eph.crs     = ie.crs*(2**-5)                #DF086 [m]
        eph.delta_n = ie.delta_n*(2**-43)           #DF087 [hc/sec]
        eph.m0      = ie.m0*(2**-31)                #DF088 [hc]
        eph.cuc     = ie.cuc*(2**-29)               #DF089 [rad]
        eph.e       = ie.e*(2**-33)                 #DF090 []
        eph.cus     = ie.cus*(2**-29)               #DF091 [rad]
        eph.sqrt_a  = ie.sqrt_a*(2**-19)            #DF092 [m^0.5]
        eph.te      = ie.te*16                      #DF093 [sec]
        eph.cic     = ie.cic*(2**-29)               #DF094 [rad]
        eph.omega0  = ie.omega0*(2**-31)            #DF095 [hc]
        eph.cis     = ie.cis*(2**-29)               #DF096 [rad]
        eph.i0      = ie.i0*(2**-31)                #DF097 [hc]
        eph.crc     = ie.crc*(2**-5)                #DF098 [m]
        eph.w       = ie.w*(2**-31)                 #DF099 [hc]
        eph.omega_dot = ie.omega_dot*(2**-43)       #DF100 [hc/sec]
        eph.TGD     = ie.TGD*(2**-31)               #DF101 [m]
        
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
        
    def __decode1020(self, buf:bytes) -> mEph.GloL1L2:
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
        self.__length_check(360,offset-24,len(buf))
        return eph
    
    @classmethod
    def __scale1020(cls, ie: mEph.GloL1L2) -> mEph.GloL1L2:
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
        
        return eph
    
    
    def __decode1041(self, buf:bytes) -> mEph.NavicL5:
        """Decode message 1041"""

        eph = mEph.NavicL5()
        offset = 24
        eph.msgNum, offset  = self.getbitu(buf, offset, 12), offset+12          #DF002
        eph.satNum, offset  = self.getbitu(buf, offset, 6), offset+6            #DF516
        eph.weekNum, offset = self.getbitu(buf, offset, 10), offset+10          #DF517
        
        eph.af0, offset     = self.getbits(buf, offset, 22), offset+22          #DF518      
        eph.af1, offset     = self.getbits(buf, offset, 16), offset+16          #DF519
        eph.af2, offset     = self.getbits(buf, offset, 8), offset+8            #DF520
        
        eph.URA, offset     = self.getbitu(buf, offset, 4), offset+4            #DF521
        eph.tc, offset      = self.getbitu(buf, offset, 16), offset+16          #DF522
        eph.TGD, offset     = self.getbits(buf, offset, 8), offset+8            #DF523
        eph.delta_n, offset = self.getbits(buf, offset, 22), offset+22          #DF524
        eph.IODEC, offset   = self.getbitu(buf, offset, 8), offset+8+10         #DF525 526
        eph.L5_Flag, offset = self.getbitu(buf, offset, 1), offset+1            #DF527
        eph.S_Flag, offset  = self.getbitu(buf, offset, 1), offset+1            #DF528
        
        eph.cuc, offset     = self.getbits(buf, offset, 15), offset+15          #DF529
        eph.cus, offset     = self.getbits(buf, offset, 15), offset+15          #DF530
        eph.cic, offset     = self.getbits(buf, offset, 15), offset+15          #DF531
        eph.cis, offset     = self.getbits(buf, offset, 15), offset+15          #DF532
        eph.crc, offset     = self.getbits(buf, offset, 15), offset+15          #DF533
        eph.crs, offset     = self.getbits(buf, offset, 15), offset+15          #DF534
        
        eph.i_dot, offset   = self.getbits(buf, offset, 14), offset+14          #DF535
        eph.m0, offset      = self.getbits(buf, offset, 32), offset+32          #DF536
        eph.te, offset      = self.getbitu(buf, offset, 16), offset+16          #DF537
        eph.e, offset       = self.getbitu(buf, offset, 32), offset+32          #DF538
        eph.sqrt_a, offset  = self.getbitu(buf, offset, 32), offset+32          #DF539
        eph.omega0, offset  = self.getbits(buf, offset, 32), offset+32          #DF540
        eph.w, offset       = self.getbits(buf, offset, 32), offset+32          #DF541
        eph.omega_dot, offset   = self.getbits(buf, offset, 22), offset+22      #DF542
        eph.i0, offset          = self.getbits(buf, offset, 32), offset+32+2+2  #DF543

        #expected offset value is 482+24 = 506 
        self.__length_check(482,offset-24,len(buf))
        return eph
    
    @classmethod
    def __scale1041(cls, ie: mEph.NavicL5) -> mEph.NavicL5:
        """Scale MSG 1041 data"""

        eph = mEph.NavicL5()
        eph.msgNum      = ie.msgNum             #DF002
        eph.satNum      = ie.satNum             #DF516
        eph.weekNum     = ie.weekNum            #DF517 [0..1023]       
        
        eph.af0         = ie.af0*(2**-31)       #DF518 [sec]     
        eph.af1         = ie.af1*(2**-43)       #DF519 [sec/sec]
        eph.af2         = ie.af2*(2**-55)       #DF520 [sec/sec/sec]       
        
        eph.URA         = ie.URA                #DF521 [index]
        eph.tc          = ie.tc*16              #DF522 [sec]
        eph.TGD         = ie.TGD*(2**-31)       #DF523 [sec]
        eph.delta_n     = ie.delta_n*(2**-41)   #DF524 [hc/sec]
        eph.IODEC       = ie.IODEC              #DF525
        eph.L5_Flag     = ie.L5_Flag            #DF527
        eph.S_Flag      = ie.S_Flag             #DF528        
        eph.cuc         = ie.cuc*(2**-28)       #DF529 [rad]
        eph.cus         = ie.cus*(2**-28)       #DF530 [rad]
        eph.cic         = ie.cic*(2**-28)       #DF531 [rad]
        eph.cis         = ie.cis*(2**-28)       #DF532 [rad]
        eph.crc         = ie.crc*(2**-4)        #DF533 [m]
        eph.crs         = ie.crs*(2**-4)        #DF534 [m]        
        eph.i_dot       = ie.i_dot*(2**-43)     #DF535 [hc/sec]
        eph.m0          = ie.m0*(2**-31)        #DF536 [hc]
        eph.te          = ie.te*16              #DF537 [sec]
        eph.e           = ie.e*(2**-33)         #DF538 []
        eph.sqrt_a      = ie.sqrt_a*(2**-19)    #DF539 [m^0.5]
        eph.omega0      = ie.omega0*(2**-31)    #DF540 [hc]
        eph.w           = ie.w*(2**-31)         #DF541 [hc]
        eph.omega_dot   = ie.omega_dot*(2**-41) #DF542 [hc/sec]
        eph.i0          = ie.i0*(2**-31)        #DF543 [hc]

        return eph
    

    def __decode1042(self, buf:bytes) -> mEph.BdsD1:
        """Decode message 1042"""

        eph = mEph.BdsD1()
        offset = 24
        eph.msgNum, offset  = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset  = self.getbitu(buf, offset, 6), offset+6        #DF488
        eph.weekNum, offset = self.getbitu(buf, offset, 13), offset+13      #DF489
        eph.URAI, offset    = self.getbitu(buf, offset, 4), offset+4        #DF490
        eph.i_dot, offset   = self.getbits(buf, offset, 14), offset+14      #DF491
        eph.AODE, offset    = self.getbitu(buf, offset, 5), offset+5        #DF492
        eph.tc, offset      = self.getbitu(buf, offset, 17), offset+17      #DF493
        
        eph.af2, offset     = self.getbits(buf, offset, 11), offset+11      #DF494
        eph.af1, offset     = self.getbits(buf, offset, 22), offset+22      #DF495
        eph.af0, offset     = self.getbits(buf, offset, 24), offset+24      #DF496
        
        eph.AODC, offset    = self.getbitu(buf, offset, 5), offset+5        #DF497
        eph.crs, offset     = self.getbits(buf, offset, 18), offset+18      #DF498
        eph.delta_n, offset = self.getbits(buf, offset, 16), offset+16      #DF499
        eph.m0, offset      = self.getbits(buf, offset, 32), offset+32      #DF500
        eph.cuc, offset     = self.getbits(buf, offset, 18), offset+18      #DF501
        eph.e, offset       = self.getbitu(buf, offset, 32), offset+32      #DF502
        eph.cus, offset     = self.getbits(buf, offset, 18), offset+18      #DF503
        eph.sqrt_a, offset  = self.getbitu(buf, offset, 32), offset+32      #DF504
        eph.te, offset      = self.getbitu(buf, offset, 17), offset+17      #DF505
        eph.cic, offset     = self.getbits(buf, offset, 18), offset+18      #DF506
        eph.omega0, offset  = self.getbits(buf, offset, 32), offset+32      #DF507
        eph.cis, offset     = self.getbits(buf, offset, 18), offset+18      #DF508
        eph.i0, offset      = self.getbits(buf, offset, 32), offset+32      #DF509
        eph.crc, offset     = self.getbits(buf, offset, 18), offset+18      #DF510
        eph.w, offset       = self.getbits(buf, offset, 32), offset+32      #DF511
        eph.omega_dot, offset = self.getbits(buf, offset, 24), offset+24    #DF512
        eph.TGD1, offset    = self.getbits(buf, offset, 10), offset+10      #DF513
        eph.TGD2, offset    = self.getbits(buf, offset, 10), offset+10      #DF514
        eph.SVH, offset     = self.getbitu(buf, offset, 1), offset+1        #DF515

        #expected offset value is 511+24 = 535
        self.__length_check(511,offset-24,len(buf))
        return eph
    
    @classmethod
    def __scale1042(cls, ie: mEph.BdsD1) -> mEph.BdsD1:
        """Scale MSG 1042 data"""

        eph = mEph.BdsD1()
        eph.msgNum      = ie.msgNum          # hc - half cycle
        eph.satNum      = ie.satNum          #DF488 [1..63]
        eph.weekNum     = ie.weekNum         #DF489 [0..8191]
        eph.URAI        = ie.URAI            #DF490 [0..15] index
        eph.i_dot       = ie.i_dot*(2**-43)  #DF491 [hc/sec]
        eph.AODE        = ie.AODE            #DF492 [0..31]
        eph.tc          = ie.tc*8            #DF493 [sec]
        
        eph.af2         = ie.af2*(2**-66)    #DF494 [sec/sec/sec]
        eph.af1         = ie.af1*(2**-50)    #DF495 [sec/sec]
        eph.af0         = ie.af0*(2**-33)    #DF496 [sec]
        
        eph.AODC        = ie.AODC            #DF497 [0..31]
        eph.crs         = ie.crs*(2**-6)     #DF498 [m]
        eph.delta_n     = ie.delta_n*(2**-43)#DF499 [hc/sec]
        eph.m0          = ie.m0*(2**-31)     #DF500 [hc]
        eph.cuc         = ie.cuc*(2**-31)    #DF501 [rad]
        eph.e           = ie.e*(2**-33)      #DF502
        eph.cus         = ie.cus*(2**-31)    #DF503 [rad]
        eph.sqrt_a      = ie.sqrt_a*(2**-19) #DF504 [m^0.5]
        eph.te          = ie.te*8            #DF505 [sec]
        eph.cic         = ie.cic*(2**-31)    #DF506 [rad]
        eph.omega0      = ie.omega0*(2**-31) #DF507 [hc]
        eph.cis         = ie.cis*(2**-31)    #DF508 [rad]
        eph.i0          = ie.i0*(2**-31)     #DF509 [hc]
        eph.crc         = ie.crc*(2**-6)     #DF510 [m]
        eph.w           = ie.w*(2**-31)      #DF511 [hc]
        eph.omega_dot   = ie.omega_dot*(2**-43) #DF512 [hc/sec]
        eph.TGD1        = ie.TGD1*1e-10      #DF513 [sec]
        eph.TGD2        = ie.TGD2*1e-10      #DF514 [sec]
        eph.SVH         = ie.SVH             #DF515 [0/1]

        return eph
    
    def __decode1046(self, buf:bytes) -> mEph.GalINAV:
        """Decode message 1046"""

        eph = mEph.GalINAV()
        offset = 24
        eph.msgNum, offset      = self.getbitu(buf, offset, 12), offset+12  #DF002
        eph.satNum, offset      = self.getbitu(buf, offset, 6), offset+6    #DF252
        eph.weekNum, offset     = self.getbitu(buf, offset, 12), offset+12  #DF289
        eph.IODnav, offset      = self.getbitu(buf, offset, 10), offset+10  #DF290
        eph.SISA, offset        = self.getbitu(buf, offset, 8), offset+8    #DF286
        eph.i_dot, offset       = self.getbits(buf, offset, 14), offset+14  #DF292
        eph.tc, offset          = self.getbitu(buf, offset, 14), offset+14  #DF293
        eph.af2, offset         = self.getbits(buf, offset, 6), offset+6    #DF294
        eph.af1, offset         = self.getbits(buf, offset, 21), offset+21  #DF295
        eph.af0, offset         = self.getbits(buf, offset, 31), offset+31  #DF296
        eph.crs, offset         = self.getbits(buf, offset, 16), offset+16  #DF297
        eph.delta_n, offset     = self.getbits(buf, offset, 16), offset+16  #DF298
        eph.m0, offset          = self.getbits(buf, offset, 32), offset+32  #DF299
        eph.cuc, offset         = self.getbits(buf, offset, 16), offset+16  #DF300
        eph.e, offset           = self.getbitu(buf, offset, 32), offset+32  #DF301
        eph.cus, offset         = self.getbits(buf, offset, 16), offset+16  #DF302
        eph.sqrt_a, offset      = self.getbitu(buf, offset, 32), offset+32  #DF303
        eph.te, offset          = self.getbitu(buf, offset, 14), offset+14  #DF304
        eph.cic, offset         = self.getbits(buf, offset, 16), offset+16  #DF305
        eph.omega0, offset      = self.getbits(buf, offset, 32), offset+32  #DF306
        eph.cis, offset         = self.getbits(buf, offset, 16), offset+16  #DF307
        eph.i0, offset          = self.getbits(buf, offset, 32), offset+32  #DF308
        eph.crc, offset         = self.getbits(buf, offset, 16), offset+16  #DF309
        eph.w, offset           = self.getbits(buf, offset, 32), offset+32  #DF310
        eph.omega_dot, offset   = self.getbits(buf, offset, 24), offset+24  #DF311
        eph.E5a_BGD, offset     = self.getbits(buf, offset, 10), offset+10  #DF312
        eph.E5b_BGD, offset     = self.getbits(buf, offset, 10), offset+10  #DF313
        eph.E5b_SHS, offset     = self.getbitu(buf, offset, 2), offset+2    #DF316
        eph.E5b_DVS, offset     = self.getbitu(buf, offset, 1), offset+1    #DF317
        eph.E1_SHS, offset      = self.getbitu(buf, offset, 2), offset+2    #DF287
        eph.E1_DVS, offset      = self.getbitu(buf, offset, 1), offset+1+2  #DF288
        
        #expected offset value is 504+24 = 528
        self.__length_check(504,offset-24,len(buf))
        return eph

    @classmethod
    def __scale1046(cls, ie: mEph.GalINAV) -> mEph.GalINAV:
        """Scale MSG 1046 data"""

        eph = mEph.GalINAV()
        eph.msgNum      = ie.msgNum                 #DF002
        eph.satNum      = ie.satNum                 #DF252
        eph.weekNum     = ie.weekNum                #DF289
        eph.IODnav      = ie.IODnav                 #DF290 [0..1023]
        eph.SISA        = ie.SISA                   #DF286 [0..255] index
        eph.i_dot       = ie.i_dot*(2**-43)         #DF292 [hc/sec]
        eph.tc          = ie.tc*60                  #DF293 [sec]
        eph.af2         = ie.af2*(2**-59)           #DF294 [sec/sec/sec]
        eph.af1         = ie.af1*(2**-46)           #DF295 [sec/sec]
        eph.af0         = ie.af0*(2**-34)           #DF296 [sec]
        eph.crs         = ie.crs*(2**-5)            #DF297 [m]
        eph.delta_n     = ie.delta_n*(2**-43)       #DF298 [hc/sec]
        eph.m0          = ie.m0*(2**-31)            #DF299 [hc]
        eph.cuc         = ie.cuc*(2**-29)           #DF300 [rad]
        eph.e           = ie.e*(2**-33)             #DF301 []
        eph.cus         = ie.cus*(2**-29)           #DF302 [rad]
        eph.sqrt_a      = ie.sqrt_a*(2**-19)        #DF303 [m^0.5]
        eph.te          = ie.te*60                  #DF304 [sec]
        eph.cic         = ie.cic*(2**-29)           #DF305 [rad]
        eph.omega0      = ie.omega0*(2**-31)        #DF306 [hc]
        eph.cis         = ie.cis*(2**-29)           #DF307 [rad]
        eph.i0          = ie.i0*(2**-31)            #DF308 [hc]
        eph.crc         = ie.crc*(2**-5)            #DF309 [m]
        eph.w           = ie.w*(2**-31)             #DF310 [hc]
        eph.omega_dot   = ie.omega_dot*(2**-43)     #DF311 [hc/sec]
        eph.E5a_BGD     = ie.E5a_BGD*(2**-32)       #DF312 [sec]
        eph.E5b_BGD     = ie.E5b_BGD*(2**-32)       #DF313 [sec]
        eph.E5b_SHS     = ie.E5b_SHS                #DF316 [0..3], 0 - OK
        eph.E5b_DVS     = ie.E5b_DVS                #DF317 [0/1]
        eph.E1_SHS      = ie.E1_SHS                 #DF287 [0..3], 0 - OK
        eph.E1_DVS      = ie.E1_DVS                 #DF288 [0/1]
        
        return eph

    def __decode1045(self, buf:bytes) -> mEph.GalFNAV:
        """Decode message 1045"""

        eph = mEph.GalFNAV()
        offset = 24
        eph.msgNum, offset      = self.getbitu(buf, offset, 12), offset+12  #DF002
        eph.satNum, offset      = self.getbitu(buf, offset, 6), offset+6    #DF252
        eph.weekNum, offset     = self.getbitu(buf, offset, 12), offset+12  #DF289
        eph.IODnav, offset      = self.getbitu(buf, offset, 10), offset+10  #DF290
        eph.SISA, offset        = self.getbitu(buf, offset, 8), offset+8    #DF291
        eph.i_dot, offset       = self.getbits(buf, offset, 14), offset+14  #DF292
        eph.tc, offset          = self.getbitu(buf, offset, 14), offset+14  #DF293
        eph.af2, offset         = self.getbits(buf, offset, 6), offset+6    #DF294
        eph.af1, offset         = self.getbits(buf, offset, 21), offset+21  #DF295
        eph.af0, offset         = self.getbits(buf, offset, 31), offset+31  #DF296
        eph.crs, offset         = self.getbits(buf, offset, 16), offset+16  #DF297
        eph.delta_n, offset     = self.getbits(buf, offset, 16), offset+16  #DF298
        eph.m0, offset          = self.getbits(buf, offset, 32), offset+32  #DF299
        eph.cuc, offset         = self.getbits(buf, offset, 16), offset+16  #DF300
        eph.e, offset           = self.getbitu(buf, offset, 32), offset+32  #DF301
        eph.cus, offset         = self.getbits(buf, offset, 16), offset+16  #DF302
        eph.sqrt_a, offset      = self.getbitu(buf, offset, 32), offset+32  #DF303
        eph.te, offset          = self.getbitu(buf, offset, 14), offset+14  #DF304
        eph.cic, offset         = self.getbits(buf, offset, 16), offset+16  #DF305
        eph.omega0, offset      = self.getbits(buf, offset, 32), offset+32  #DF306
        eph.cis, offset         = self.getbits(buf, offset, 16), offset+16  #DF307
        eph.i0, offset          = self.getbits(buf, offset, 32), offset+32  #DF308
        eph.crc, offset         = self.getbits(buf, offset, 16), offset+16  #DF309
        eph.w, offset           = self.getbits(buf, offset, 32), offset+32  #DF310
        eph.omega_dot, offset   = self.getbits(buf, offset, 24), offset+24  #DF311
        eph.E5a_BGD, offset     = self.getbits(buf, offset, 10), offset+10  #DF312
        eph.E5a_SHS, offset     = self.getbitu(buf, offset, 2), offset+2    #DF314
        eph.E5a_DVS, offset     = self.getbitu(buf, offset, 1), offset+1+7  #DF315
        
        #expected offset value is 496+24 = 520
        self.__length_check(496,offset-24,len(buf))
        return eph
    
    @classmethod
    def __scale1045(cls, ie: mEph.GalFNAV) -> mEph.GalFNAV:
        """Scale MSG 1045 data"""

        eph = mEph.GalFNAV()
        eph.msgNum      = ie.msgNum                 #DF002
        eph.satNum      = ie.satNum                 #DF252
        eph.weekNum     = ie.weekNum                #DF289
        eph.IODnav      = ie.IODnav                 #DF290 [0..1023]
        eph.SISA        = ie.SISA                   #DF291 [0..255] index
        eph.i_dot       = ie.i_dot*(2**-43)         #DF292 [hc/sec]
        eph.tc          = ie.tc*60                  #DF293 [sec]
        eph.af2         = ie.af2*(2**-59)           #DF294 [sec/sec/sec]
        eph.af1         = ie.af1*(2**-46)           #DF295 [sec/sec]
        eph.af0         = ie.af0*(2**-34)           #DF296 [sec]
        eph.crs         = ie.crs*(2**-5)            #DF297 [m]
        eph.delta_n     = ie.delta_n*(2**-43)       #DF298 [hc/sec]
        eph.m0          = ie.m0*(2**-31)            #DF299 [hc]
        eph.cuc         = ie.cuc*(2**-29)           #DF300 [rad]
        eph.e           = ie.e*(2**-33)             #DF301 []
        eph.cus         = ie.cus*(2**-29)           #DF302 [rad]
        eph.sqrt_a      = ie.sqrt_a*(2**-19)        #DF303 [m^0.5]
        eph.te          = ie.te*60                  #DF304 [sec]
        eph.cic         = ie.cic*(2**-29)           #DF305 [rad]
        eph.omega0      = ie.omega0*(2**-31)        #DF306 [hc]
        eph.cis         = ie.cis*(2**-29)           #DF307 [rad]
        eph.i0          = ie.i0*(2**-31)            #DF308 [hc]
        eph.crc         = ie.crc*(2**-5)            #DF309 [m]
        eph.w           = ie.w*(2**-31)             #DF310 [hc]
        eph.omega_dot   = ie.omega_dot*(2**-43)     #DF311 [hc/sec]
        eph.E5a_BGD     = ie.E5a_BGD*(2**-32)       #DF312 [sec]
        eph.E5a_SHS     = ie.E5a_SHS                #DF314 [0..3], 0 - OK
        eph.E5a_DVS     = ie.E5a_DVS                #DF315 [0/1]
        
        return eph
    
    def __decode1044(self, buf:bytes) -> mEph.QzssL1:
        """Decode message 1044"""
        eph = mEph.QzssL1()
        offset = 24
        
        eph.msgNum, offset      = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset      = self.getbitu(buf, offset, 4), offset+4         #DF429
        eph.tc, offset          = self.getbitu(buf, offset, 16), offset+16       #DF430
        eph.af2, offset         = self.getbits(buf, offset, 8), offset+8         #DF431
        eph.af1, offset         = self.getbits(buf, offset, 16), offset+16       #DF432
        eph.af0, offset         = self.getbits(buf, offset, 22), offset+22       #DF433
        eph.IODE, offset        = self.getbitu(buf, offset, 8), offset+8         #DF434
        eph.crs, offset         = self.getbits(buf, offset, 16), offset+16       #DF435
        eph.delta_n, offset     = self.getbits(buf, offset, 16), offset+16       #DF436
        eph.m0, offset          = self.getbits(buf, offset, 32), offset+32       #DF437
        eph.cuc, offset         = self.getbits(buf, offset, 16), offset+16       #DF438
        eph.e, offset           = self.getbitu(buf, offset, 32), offset+32       #DF439
        eph.cus, offset         = self.getbits(buf, offset, 16), offset+16       #DF440
        eph.sqrt_a, offset      = self.getbitu(buf, offset, 32), offset+32       #DF441
        eph.te, offset          = self.getbitu(buf, offset, 16), offset+16       #DF442
        eph.cic, offset         = self.getbits(buf, offset, 16), offset+16       #DF443
        eph.omega0, offset      = self.getbits(buf, offset, 32), offset+32       #DF444
        eph.cis, offset         = self.getbits(buf, offset, 16), offset+16       #DF445
        eph.i0, offset          = self.getbits(buf, offset, 32), offset+32       #DF446
        eph.crc, offset         = self.getbits(buf, offset, 16), offset+16       #DF447
        eph.w, offset           = self.getbits(buf, offset, 32), offset+32       #DF448
        eph.omega_dot, offset   = self.getbits(buf, offset, 24), offset+24       #DF449
        eph.i_dot, offset       = self.getbits(buf, offset, 14), offset+14       #DF450
        eph.L2_Codes, offset    = self.getbitu(buf, offset, 2), offset+2         #DF451
        eph.weekNum, offset     = self.getbitu(buf, offset, 10), offset+10       #DF452
        eph.URA, offset         = self.getbitu(buf, offset, 4), offset+4         #DF453
        eph.SVH, offset         = self.getbitu(buf, offset, 6), offset+6         #DF454
        eph.TGD, offset         = self.getbits(buf, offset, 8), offset+8         #DF455
        eph.IODC, offset        = self.getbitu(buf, offset, 10), offset+8        #DF456
        eph.Fit, offset         = self.getbitu(buf, offset, 1), offset+1         #DF457

        #expected offcet value is 485+24=509   
        self.__length_check(485,offset-24,len(buf))
        return eph
    
    @classmethod
    def __scale1044(cls, ie: mEph.QzssL1) -> mEph.QzssL1:
        """Scale MSG 1044 data"""

        eph = mEph.QzssL1()
        eph.msgNum = ie.msgNum
        eph.satNum  = ie.satNum                     #DF429 [0..10]
        eph.tc      = ie.tc*16                      #DF430 [sec]
        eph.af2     = ie.af2*(2**-55)               #DF431 [sec/sec/sec]
        eph.af1     = ie.af1*(2**-43)               #DF432 [sec/sec]
        eph.af0     = ie.af0*(2**-31)               #DF433 [sec]
        eph.IODE    = ie.IODE                       #DF434 [0..255]
        eph.crs     = ie.crs*(2**-5)                #DF435 [m]
        eph.delta_n = ie.delta_n*(2**-43)           #DF436 [hc/sec]
        eph.m0      = ie.m0*(2**-31)                #DF437 [hc]
        eph.cuc     = ie.cuc*(2**-29)               #DF438 [rad]
        eph.e       = ie.e*(2**-33)                 #DF439 []
        eph.cus     = ie.cus*(2**-29)               #DF440 [rad]
        eph.sqrt_a  = ie.sqrt_a*(2**-19)            #DF441 [m^0.5]
        eph.te      = ie.te*16                      #DF442 [sec]
        eph.cic     = ie.cic*(2**-29)               #DF443 [rad]
        eph.omega0  = ie.omega0*(2**-31)            #DF444 [hc]
        eph.cis     = ie.cis*(2**-29)               #DF445 [rad]
        eph.i0      = ie.i0*(2**-31)                #DF446 [hc]
        eph.crc     = ie.crc*(2**-5)                #DF447 [m]
        eph.w       = ie.w*(2**-31)                 #DF448 [hc]
        eph.omega_dot = ie.omega_dot*(2**-43)       #DF449 [hc/sec]
        eph.i_dot   = ie.i_dot*(2**-43)             #DF450 [hc/sec]
        eph.L2_Codes= ie.L2_Codes                   #DF451
        eph.weekNum = ie.weekNum                    #DF452 [0..1023]
        eph.URA     = ie.URA                        #DF453
        eph.SVH     = ie.SVH                        #DF454,[6-bit code] 0-OK
        eph.TGD     = ie.TGD*(2**-31)               #DF455 [m]
        eph.IODC    = ie.IODC                       #DF456 [0..1023]
        eph.Fit     = ie.Fit                        #DF457 [0/1] 0: =2h, 1: >2h

        return eph
    
    
    def __decode(self, buf:bytes) -> object:
        """Decode ephemeris message"""
        
        msgNum = self.get_msg_num(buf)
        
        match msgNum:
            case 1019:
                return self.__decode1019(buf)
            case 1020:
                return self.__decode1020(buf)
            case 1041:
                return self.__decode1041(buf)
            case 1042:
                return self.__decode1042(buf)
            case 1044:
                return self.__decode1044(buf)
            case 1045:
                return self.__decode1045(buf)
            case 1046:
                return self.__decode1046(buf)
            case _:
                raise ExceptionEphemerisDecoder(f'message {msgNum} is not allowed.')
            
    @classmethod
    def scale(cls, ie: object)->object:
        """Apply scaling coefficients to a bare ephemeris data"""

        match type(ie):
            case mEph.GpsLNAV:
                return cls.__scale1019(ie)
            case mEph.GloL1L2:
                return cls.__scale1020(ie)
            case mEph.GalFNAV:
                return cls.__scale1045(ie)
            case mEph.GalINAV:
                return cls.__scale1046(ie)
            case mEph.BdsD1:
                return cls.__scale1042(ie)
            case mEph.NavicL5:
                return cls.__scale1041(ie)
            case mEph.QzssL1:
                return cls.__scale1044(ie)
            case _:
                raise ExceptionEphemerisDecoder(f'scaler doesn\'t support type {type(ie)}')
    

    def decode(self, buf:bytes, is_bare_output:bool = False) -> object:
        """Process ephemeris message"""
        
        eph = self.__decode(buf)
            
        if is_bare_output == False:
            eph = self.scale(eph)

        return eph




class SubdecoderEph():
    '''Implements decoding of RTCM ephemeris messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__bare_data = bare_data
        self.decoder = EphemerisDecoder()
        self.io = SubDecoderInterface('EPH', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = self.decoder.msgList
        

    def decode(self, buf:bytes) -> Any | None:

        ephBlock = None
            
        try:
            msgNum = self.decoder.get_msg_num(buf)
            ephBlock = self.decoder.decode(buf, self.__bare_data)
            logger.info(f'Msg {msgNum}. Decoding succeeded. SV = {ephBlock.satNum}.')

        except ExceptionEphemerisDecoder as ex:
            logger.error(f"Msg {msgNum}. Decoding failed: " + ex.args[0])            
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
        
        return ephBlock
    