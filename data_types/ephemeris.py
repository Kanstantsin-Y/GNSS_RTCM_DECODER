"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    This file implements DTO classes for ephemerida data.
"""

from dataclasses import dataclass
from dataclasses import is_dataclass


__all__ = ['isValidEphBlock', 'GpsLNAV', 'GloL1L2', 'GalFNAV', 'GalINAV', 'BdsD1', 'QzssL1', 'NavicL5']


def isValidEphBlock(ephBlock:object)->bool:
    """Validate minimal requirements to ephemeris data block"""
    valid = True
    if not type(ephBlock) in (GalFNAV, GalINAV, QzssL1, BdsD1, GpsLNAV, NavicL5, GloL1L2):
        valid = False
    if not is_dataclass(ephBlock):
        valid = False
    if not "msgNum" in ephBlock.__dict__.keys():
        valid = False
    if not "satNum" in ephBlock.__dict__.keys():
        valid = False

    return valid 



@dataclass
class EphHdr:
    """ephemeris ID"""
    #3 elements:
    msgNum: int = 0
    satNum: int = 0
    weekNum: int = 0

@dataclass
class ClockBias:
    """Clock correction parameters"""
    #4 elements:
    tc: int = 0
    af0: int|float = 0
    af1: int|float = 0
    af2: int|float = 0

@dataclass
class Keplerians:
    """SV's orbital motion parameters"""
    # 16 elements:
    te:         int = 0
    delta_n:    int|float = 0
    m0:         int|float = 0
    e:          int|float = 0
    sqrt_a:     int|float = 0
    w:          int|float = 0
    i0:         int|float = 0
    i_dot:      int|float = 0
    omega0:     int|float = 0
    omega_dot:  int|float = 0
    crs:        int|float = 0
    crc:        int|float = 0
    cuc:        int|float = 0
    cus:        int|float = 0
    cic:        int|float = 0
    cis:        int|float = 0
    

@dataclass
class GalFNAV(Keplerians, ClockBias, EphHdr):
    """ Galileo FNAV ephemeris, MSG 1045"""
    # 23 + 5 = 28 elements
    IODnav: int = 0
    SISA: int|float = 0
    E5a_BGD: int|float = 0
    E5a_SHS: int = 0
    E5a_DVS: int = 0


@dataclass
class GalINAV(Keplerians, ClockBias, EphHdr):
    """ Galileo INAV ephemeris, MSG 1046"""

    #23 + 8 = 31 elements
    IODnav: int = 0
    SISA: int|float = 0
    E5a_BGD: int|float = 0
    E5b_BGD: int|float = 0
    E1_SHS: int = 0
    E1_DVS: int = 0
    E5b_SHS: int = 0
    E5b_DVS: int = 0

      
@dataclass
class QzssL1(Keplerians, ClockBias, EphHdr):
    """ QZSS L1 ephemeris, MSG 1044"""

    #23 + 7 = 30 elements
    IODE: int = 0
    IODC: int = 0
    Fit: int = 0
    L2_Codes: int = 0
    SVH: int = 0
    URA: int|float = 0
    TGD: int|float = 0


@dataclass
class BdsD1(Keplerians, ClockBias, EphHdr):
    """ BeiDou D1 ephemeris, MSG 1042"""

    #23 + 6 = 29 elements
    AODE: int = 0
    AODC: int = 0
    SVH: int = 0
    URAI: int|float = 0
    TGD1: int|float = 0
    TGD2: int|float = 0


@dataclass
class GpsLNAV(Keplerians, ClockBias, EphHdr):
    """ GPS LNAV/CNAV ephemeris, MSG 1019"""

    #23 + 8 = 31 elements
    IODE: int = 0
    IODC: int = 0
    Fit: int|str = 0
    L2_Codes: int|str = 0
    L2P_Data: int|str = 0
    SVH: int|str = 0
    URA: int|float = 0
    TGD: int|float = 0

@dataclass
class NavicL5(Keplerians, ClockBias, EphHdr):
    """ Navic L5/S ephemeris, MSG 1041"""

    #23 + 5 = 28 elements
    URA: int|float = 0
    TGD: int|float = 0
    IODEC: int = 0
    L5_Flag = 0
    S_Flag = 0
    


@dataclass
class GloL1L2:
    """Glonass L1/L2 ephemeris, MSG 1020"""

    #36 items
    msgNum:         int = 0
    satNum:         int = 0
    frqSloNum:      int = 0         # [-7..6]
    tk:             int = 0         # [sec]
    tb:             int = 0         # [sec]
    xn:             int|float = 0   # [km/s]
    dotXn:          int|float = 0   # [km/s^2]
    dotDotXn:       int|float = 0   # [km/s^3]
    yn:             int|float = 0   # [km/s]
    dotYn:          int|float = 0   # [km/s^2]
    dotDotYn:       int|float = 0   # [km/s^3]
    zn:             int|float = 0   # [km/s]
    dotZn:          int|float = 0   # [km/s^2]
    dotDotZn:       int|float = 0   # [km/s^3]
    gamma_n:        int|float = 0   # []
    Cn:             int = 0
    BnMSB:          int = 0
    AlmHAI:         int = 0
    P:              int = 0
    P1:             int = 0         # [sec]
    P2:             int = 0
    P3:             int = 0
    P4:             int = 0
    ln3:            int = 0
    tauN:           int|float = 0   # [m]
    delta_tauN:     int|float = 0   # [m]
    En:             int = 0
    Ft:             int = 0         # [m]
    Nt:             int = 0
    M:              int = 0
    auxDataOK:      int = 0
    Na:             int = 0
    tauC:           int|float = 0   # [s]
    N4:             int = 0
    tauGPS:         int|float = 0   # [s]
    ln5:            int = 0
    