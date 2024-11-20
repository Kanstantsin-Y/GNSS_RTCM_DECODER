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
from dataclasses import dataclass

from typing import Any
#from utilities.RTCM_utilities import MSMT
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
        eph.msgNum, offset = self.getbitu(buf, offset, 12), offset+12
        eph.satNum, offset = self.getbitu(buf, offset, 6), offset+6

        return eph
    
    def __scale1019(self, iEph: mEph.GpsLNAV) -> mEph.GpsLNAV:
        """Scale and beautify MSG 1019 data"""

        return iEph
    
    
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


# def decode_ephemerids(is_bare_output: bool, buf:bytes) -> mEph.GpsLNAV|None:
#     """Process ephemeris message"""
    
#     dec = EphemerisDecoder()
#     mnum = dec.get_msg_num(buf)

#     try:
#         ephBlock = dec.decode(buf, is_bare_output)
#     except ExceptionBitsError as ex:
#         logger.error(f"Msg {mnum}. Decoding failed. " + ex.args[0])
#     except IndexError as ie:
#         logger.error(f"Msg {mnum}. Decoding failed. Indexing error: {type(ie)}: {ie}")
#     except ArithmeticError as ae:
#         logger.error(f"Msg {mnum}. Decoding failed. Arithm error: {type(ae)}: {ae}")
#     except Exception as ex:
#         logger.error(f"Msg {mnum}. Decoding failed. Unexpected error:" + f"{type(ex)}: {ex}")
#     else:
#         pass

#     if not ephBlock:
#         return None

#     logger.info(f'Msg {mnum}. Decoding succeeded. SV = {ephBlock.satNum}.')
#     return ephBlock
    

    # if is_bare_output:
    #     logger.info(f'Msg {mnum}. Decoding succeeded. SV = {ephBlock.satNum}.')
    #     return ephBlock
    
    # scaler = Bare2Scaled()

    # try:
    #     rv = scaler.convert(msm.bare_data)
    # except IndexError as ie:
    #     logger.error(f"Indexing error in get_scaled_obs() {type(ie)}: {ie}")
    # except ArithmeticError as ae:
    #     logger.error(f"Arithmetic error in get_scaled_obs() {type(ae)}: {ae}")
    # except Exception as ex:
    #     logger.error(f"Undefined error in get_scaled_obs() {type(ex)}: {ex}")
    # else:
    #     logger.info(f'Msg {mnum}. Decoding succeeded. t = {rv.hdr.time}, sats = {len(rv.hdr.sats)}.')

    # return rv





class SubdecoderEph():
    '''Implements decoding of RTCM ephemeris messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__bare_data = bare_data
        self.decoder = EphemerisDecoder()
        self.io = SubDecoderInterface('EPH', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = self.decoder.msgList #set(self.io.io_spec.keys())
        

    def decode(self, buf:bytes) -> Any | None:
        return self.decoder.decode(buf, self.__bare_data)



