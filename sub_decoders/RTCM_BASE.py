"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements subdecoder for the messages describing base station. Provides one DTO
    object per each message. Two types of DTOs can be returned optionally:
    1. Bare integer data (as it is in the message);
    2. Scaled and ready for futher computations parameters. Fields like:
       - binary flags
       - status codes
       - indexes for tabled values
       are not scaled and shall be interpreted on the user side.
"""
import math

from gnss_types import *

from decoder_top import SubDecoderInterface
from typing import Any
from utilities import Bits
from utilities import ExceptionBitsError
from logger import LOGGER_CF as logger


#--- Exceptions ----------------------------------------------------------------------------------

class ExceptionBaseStationDataDecoder(Exception):
    '''Hook error in BaseStationDataDecoder methods'''

#------------------------------------------------------------------------------------------------
    
class BaseStationDataDecoder(Bits):
    '''Methods to extract bare data from ephemeris message'''

    def __init__(self) -> None:
        super().__init__()
        self.msgList = (1005,1006,1007,1008,1033,1013,1029,1230)
        
    def get_msg_num(self, buf: bytes) -> int:
        return self.getbitu(buf, 24, 12)
    
    @staticmethod
    def __length_check(Nexp:int, Ndec:int, bufLen:int):
        """Validate message length"""

        if Ndec != Nexp:
            raise ExceptionBaseStationDataDecoder(f'data field length error: {Ndec} vs {Nexp}')
       
        Ndec = 6 + ((Ndec+7)>>3)
        if Ndec != bufLen:
            raise ExceptionBaseStationDataDecoder(f'message length error: {bufLen} vs {Ndec}')


    def __decode10056(self, buf:bytes) -> BaseRP|BaseRPH:
        """Decode messages 1005/1006"""

        offset = 24
        msgNum, offset              = self.getbitu(buf, offset, 12), offset+12      #DF002
        bs = BaseRP() if (msgNum == 1005) else BaseRPH()

        bs.msgNum = msgNum
        bs.bsID, offset             = self.getbitu(buf, offset, 12), offset+12  #DF003
        bs.ITRF_RY, offset          = self.getbitu(buf,offset,6), offset+6      #DF021
        bs.GPS_OK, offset           = self.getbitu(buf,offset,1), offset+1      #DF022
        bs.GLO_OK, offset           = self.getbitu(buf,offset,1), offset+1      #DF023
        bs.GAL_OK, offset           = self.getbitu(buf,offset,1), offset+1      #DF024
        bs.isVirtual, offset        = self.getbitu(buf,offset,1), offset+1      #DF141
        bs.refPoint_X, offset       = self.getbits(buf,offset,38),offset+38     #DF025
        bs.singleOsc, offset        = self.getbitu(buf,offset,1), offset+1+1    #DF142
        bs.refPoint_Y, offset       = self.getbits(buf,offset,38),offset+38     #DF026
        bs.QC_bias, offset          = self.getbitu(buf,offset,2), offset+2      #DF364
        bs.refPoint_Z, offset       = self.getbits(buf,offset,38),offset+38     #DF027

        if msgNum == 1006:
            bs.height, offset       = self.getbitu(buf, offset, 16), offset+16  #DF028
            self.__length_check(168,offset-24,len(buf))
        else:
            self.__length_check(152,offset-24,len(buf))

        return bs
    
    @classmethod
    def __scale10056(cls, ibs: BaseRP|BaseRPH) -> BaseRP|BaseRPH:
        """Scale MSG 10056 data"""
        __QC_VALUES = ['UNDEF', 'CORRECTED', 'NOT CORRECTED', 'RESERVED']
        
        bs = ibs.copy()           
        bs.GPS_OK = (bs.GPS_OK == 1)            #DF022
        bs.GLO_OK = (bs.GLO_OK == 1)            #DF023
        bs.GAL_OK = (bs.GAL_OK == 1)            #DF024
        bs.isVirtual = (bs.isVirtual == 1)      #DF141
        bs.refPoint_X = bs.refPoint_X * 1e-4    #DF025
        bs.singleOsc = (bs.singleOsc == 1)      #DF142
        bs.refPoint_Y = bs.refPoint_Y * 1e-4    #DF026
        bs.QC_bias = __QC_VALUES[bs.QC_bias]    #DF364
        bs.refPoint_Z = bs.refPoint_Z * 1e-4    #DF027

        if isinstance(bs, BaseRPH):
            bs.height = bs.height * 1e-4
        
        return bs
    
    
    def __decode10078_1033(self, buf:bytes) -> BaseAD|BaseADSN|BaseADSNRC:
        """Decode messages 1007/1008/1033"""

        offset = 24
        msgNum, offset = self.getbitu(buf, offset, 12), offset+12               #DF002
                
        if msgNum == 1007:
            bs = BaseAD()
        elif msgNum == 1008:
            bs = BaseADSN()
        else:
            bs = BaseADSNRC()

        bs.msgNum = msgNum
        bs.bsID, offset = self.getbitu(buf, offset, 12), offset + 12                #DF003
        
        bs.descrLength, offset = self.getbitu(buf, offset, 8), offset + 8           #DF029
        symb = list()
        for _ in range(bs.descrLength):
            symb.append( self.getbitu(buf, offset, 8) )                             #DF030
            offset += 8                                                   
        bs.descr = bytes(symb).decode()                                             #DF030
        bs.setupID, offset = self.getbitu(buf, offset, 8), offset + 8               #DF031
        
        if msgNum == 1007:
            self.__length_check(40+8*bs.descrLength, offset-24, len(buf))
            return bs

        bs.serialNumberLength, offset = self.getbitu(buf, offset, 8), offset+8      #DF032
        symb = list()
        for _ in range(bs.serialNumberLength):
            symb.append( self.getbitu(buf, offset, 8) )
            offset += 8                                                             #DF033
        bs.serialNumber = bytes(symb).decode()                                      #DF033
        
        if msgNum == 1008:
            self.__length_check(48+8*(bs.descrLength + bs.serialNumberLength), offset-24, len(buf))
            return bs

        bs.rcvDescriptorLength, offset = self.getbitu(buf, offset, 8), offset+8     #DF227
        symb = list()
        for _ in range(bs.rcvDescriptorLength):
            symb.append( self.getbitu(buf, offset, 8) )
            offset += 8                                                             #DF228
        bs.rcvDescriptor = bytes(symb).decode()                                     #DF228

        bs.rcvFWVersionLength, offset = self.getbitu(buf, offset, 8), offset+8      #DF229
        symb = list()
        for _ in range(bs.rcvFWVersionLength):
            symb.append( self.getbitu(buf, offset, 8) )
            offset += 8                                                             #DF230
        bs.rcvFWVersion = bytes(symb).decode()                                      #DF230

        bs.rcvSerNumLength, offset = self.getbitu(buf, offset, 8), offset+8         #DF231
        symb = list()
        for _ in range(bs.rcvSerNumLength):
            symb.append( self.getbitu(buf, offset, 8) )
            offset += 8                                                             #DF232
        bs.rcvSerNum = bytes(symb).decode()                                         #DF232

        strLen = bs.descrLength + bs.serialNumberLength + bs.rcvDescriptorLength
        strLen += bs.rcvFWVersionLength + bs.rcvSerNumLength
        self.__length_check(72+8*strLen, offset-24, len(buf))
        return bs


    @classmethod
    def __scale10078_1033(cls, ibs: BaseAD|BaseADSN|BaseADSNRC) -> BaseAD|BaseADSN|BaseADSNRC:
        """Scale MSG 1007/1008/1033 data"""
        
        return ibs

            
    def __decode1013(self, buf:bytes) -> BaseSP:
        """Decode message 1013, System Parameters"""

        bs = BaseSP()
        offset = 24
        bs.msgNum, offset       = self.getbitu(buf, offset, 12), offset+12      #DF002
        bs.bsID, offset         = self.getbitu(buf, offset, 12), offset+12      #DF003
        bs.modifiedJulianDay, offset = self.getbitu(buf, offset, 16), offset+16 #DF051
        bs.daySec, offset       = self.getbitu(buf, offset, 17), offset+17      #DF052
        bs.Nm, offset           = self.getbitu(buf, offset, 5), offset+5        #DF053
        bs.leapSec, offset      = self.getbitu(buf, offset, 8), offset+8        #DF054
        
        if bs.Nm != 0:
            Nm = bs.Nm
        else:
            Nm = math.floor((8*len(buf)-70)/29)

        for _ in range(Nm):
            ID, offset          = self.getbitu(buf, offset, 12), offset+12      #DF055
            isPeriodic, offset  = self.getbitu(buf, offset, 1), offset+1        #DF056
            period, offset      = self.getbitu(buf, offset, 16), offset+16      #DF057
            bs.shedule.update( {ID : (isPeriodic, period)} )
        
        self.__length_check(70 + 29*Nm, offset-24, len(buf))
        return bs
    
    @classmethod
    def __scale1013(cls, ibs: BaseSP) -> BaseSP:
        """Scale MSG 1013 data"""
        
        bs = ibs.deepcopy()
        for k in bs.shedule.keys():
            bs.shedule[k][0] = (1 == bs.shedule[k][0])
            bs.shedule[k][1] = bs.shedule[k][1]*0.1

        return bs

    
    def __decode1029(self, buf:bytes) -> BaseTS:
        """Decode message 1029, Unicode Textual String"""

        bs = BaseTS()
        offset = 24
        bs.msgNum, offset               = self.getbitu(buf, offset, 12), offset+12      #DF002
        bs.bsID, offset                 = self.getbitu(buf, offset, 12), offset+12      #DF003
        bs.modifiedJulianDay, offset    = self.getbitu(buf, offset, 16), offset+16      #DF051
        bs.daySec, offset               = self.getbitu(buf, offset, 17), offset+17      #DF052
        bs.charNum, offset              = self.getbitu(buf, offset, 7),  offset+7       #DF138
        bs.unitsNum, offset             = self.getbitu(buf, offset, 8),  offset+8       #DF139

        msg = []
        for _ in range(bs.unitsNum):
            msg.append( self.getbitu(buf, offset, 8) )
            offset += 8

        bs.message = bytes(msg).decode(encoding='utf-8')
        
        self.__length_check(72 + 8*bs.unitsNum, offset-24, len(buf))
        return bs
    

    @classmethod
    def __scale1029(cls, ibs: BaseTS) -> BaseTS:
        """Scale MSG 1029 data"""
        return ibs

    
    def __decode1230(self, buf:bytes) -> BaseGLBS:
        """Decode message 1230, Glonass code-phase bias"""

        bs = BaseGLBS()
        offset = 24
        bs.msgNum, offset   = self.getbitu(buf, offset, 12), offset+12      #DF002
        bs.bsID, offset     = self.getbitu(buf, offset, 12), offset+12      #DF003
        bs.isCorrected, offset  = self.getbitu(buf, offset, 1), offset+1+3  #DF421
        validity, offset    = self.getbitu(buf, offset, 4), offset+4        #DF422
        
        N = 0
        if validity & 0x08:
            bs.correction['1C'], offset = self.getbits(buf, offset, 16), offset+16  #DF423
            if bs.correction['1C'] == -32768:
                logger.warning(f"Msg {bs.msgNum}. Field L1CA marked as undefined (0x8000)")
            bs.validity['1C'] = 1
            N += 1
        if validity & 0x04:
            bs.correction['1P'], offset  = self.getbits(buf, offset, 16), offset+16  #DF424
            if bs.correction['1P'] == -32768:
                logger.warning(f"Msg {bs.msgNum}. Field L1P marked as undefined (0x8000)")
            bs.validity['1P'] = 1
            N += 1
        if validity & 0x02:
            bs.correction['2C'], offset = self.getbits(buf, offset, 16), offset+16  #DF425
            if bs.correction['2C'] == -32768:
                logger.warning(f"Msg {bs.msgNum}. Field L2CA marked as undefined (0x8000)")
            bs.validity['2C'] = 1
            N += 1
        if validity & 0x01:
            bs.correction['2P'], offset  = self.getbits(buf, offset, 16), offset+16  #DF426
            if bs.correction['2P'] == -32768:
                logger.warning(f"Msg {bs.msgNum}. Field L2P marked as undefined (0x8000)")
            bs.validity['2P'] = 1
            N += 1
        
        self.__length_check(32 + 16*N, offset-24, len(buf))
        return bs

    @classmethod
    def __scale1230(cls, ibs: BaseGLBS) -> BaseGLBS:
        """Scale MSG 1230 data"""
        
        bs = ibs.deepcopy()
        bs.isCorrected = (bs.isCorrected == 1)
        bs.validity['1C']  = (bs.validity['1C'] == 1)           #DF422
        bs.validity['1P']  = (bs.validity['1P'] == 1)           #DF422
        bs.validity['2C']  = (bs.validity['2C'] == 1)           #DF422
        bs.validity['2P']  = (bs.validity['2P'] == 1)           #DF422
        bs.correction['1C'] *= 0.2                              #DF423 [m]
        bs.correction['1P'] *= 0.2                              #DF424 [m]
        bs.correction['2C'] *= 0.2                              #DF425 [m]
        bs.correction['2P'] *= 0.2                              #DF426 [m]
        
        return bs
    
    
    def __decode(self, buf:bytes) -> object:
        """Decode Base Data message"""
        
        msgNum = self.get_msg_num(buf)
        
        match msgNum:
            case 1005:
                return self.__decode10056(buf)
            case 1006:
                return self.__decode10056(buf)
            case 1007:
                return self.__decode10078_1033(buf)
            case 1008:
                return self.__decode10078_1033(buf)
            case 1033:
                return self.__decode10078_1033(buf)
            case 1013:
                return self.__decode1013(buf)
            case 1029:
                return self.__decode1029(buf)
            case 1230:
                return self.__decode1230(buf)
            case _:
                raise ExceptionBaseStationDataDecoder(f'message {msgNum} is not allowed.')
            

    @classmethod
    def scale(cls, bs:object)->object:
        """Apply scaling coefficients to a bare Base Station Data"""

        if isinstance(bs, (BaseRP,BaseRPH)):
            return cls.__scale10056(bs)
        elif isinstance(bs, (BaseAD,BaseADSN,BaseADSNRC)):
            return cls.__scale10078_1033(bs)
        elif isinstance(bs, BaseSP):
            return cls.__scale1013(bs)
        elif isinstance(bs, BaseTS):
            return cls.__scale1029(bs)
        elif isinstance(bs, BaseGLBS):
            return cls.__scale1230(bs)
        else:
            raise ExceptionBaseStationDataDecoder(f'scaler doesn\'t support type {type(bs)}')
    

    def decode(self, buf:bytes, is_bare_output:bool = False) -> object:
        """Process Base Data message"""
        
        baseData = self.__decode(buf)
            
        if is_bare_output == False:
            baseData = self.scale(baseData)

        return baseData



class SubdecoderBaseStationData():
    '''Implements decoding of Base Station Data messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__is_bare_data = bare_data
        self.decoder = BaseStationDataDecoder()
        self.io = SubDecoderInterface('BASE', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = self.decoder.msgList
        

    def decode(self, buf:bytes) -> Any | None:

        bsMsg = None
            
        try:
            msgNum = self.decoder.get_msg_num(buf)
            bsMsg = self.decoder.decode(buf, self.__is_bare_data)
            logger.info(f'Msg {msgNum}. Decoding succeeded. SV = {bsMsg.bsID}.')

        except ExceptionBaseStationDataDecoder as ex:
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
        
        return bsMsg
    
    