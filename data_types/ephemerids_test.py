

from data_types.ephemerids import GpsLNAV
from data_types.ephemerids import GloL1L2
#from data_types.ephemerids import GalFNAV
from data_types.ephemerids import GalINAV
from data_types.ephemerids import BdsD1
from data_types.ephemerids import NavicL5
#from data_types.ephemerids import QzssL1





# according to file RTCM3_TEST_DATA\EPH\msg1019.rtcm3
_G = [
    GpsLNAV(
        msgNum  = 1019,
        satNum  = 32,
        weekNum = 197,
        URA     = 0,
        L2_Codes= 1,
        i_dot   = 2.10434336622711271047592163086e-10,
        IODE    = 68,
        tc      = 403200,
        af2     = 0.000000000000000000000000000000000e+00,
        af1     = -1.22781784739345312118530273438e-11,
        af0     = -3.6916276440024375915527344e-04,
        IODC    = 68,
        crs     = -8.18750e+00,
        delta_n = 1.50805590237723663449287414551e-09,
        m0      = -2.3986937897279858589172363e-01,
        cuc     = -3.036111593246459960937500e-07,
        e       = 6.48663751780986785888671875e-03,
        cus     = 9.274110198020935058593750e-06,
        sqrt_a  = 5.1536912937164306641e+03,
        te      = 403200,
        cic     = 1.490116119384765625000000e-08,
        omega0  = 1.3762591034173965454101563e-01,
        cis     = 1.713633537292480468750000e-07,
        i0      = 3.0539020989090204238891602e-01,
        crc     = 2.005625e+02,
        w       = -7.2424596967175602912902832e-01,
        omega_dot = -2.52248355536721646785736083984e-09,
        TGD      = 4.6566128730773925781250000e-10,
        SVH      = 0,
        L2P_Data = 0,
        Fit      = 0
    ),
    GpsLNAV(
        msgNum  = 1019,
        satNum  = 31,
        weekNum = 197,
        URA     = 0,
        L2_Codes= 1,
        i_dot   = -1.33354660647455602884292602539e-10,
        IODE    = 72,
        tc      = 403200,
        af2     = 0.000000000000000000000000000000000e+00,
        af1     = -1.13686837721616029739379882813e-12,
        af0     = -2.0678620785474777221679688e-04,
        IODC    = 72,
        crs     = -1.56250e-01,
        delta_n = 1.65141500474419444799423217773e-09,
        m0      = 4.4719802075996994972229004e-01,
        cuc     = 2.384185791015625000000000e-07,
        e       = 1.07931792736053466796875000e-02,
        cus     = 6.247311830520629882812500e-06,
        sqrt_a  = 5.1536309185028076172e+03,
        te      = 403200,
        cic     = -6.519258022308349609375000e-08,
        omega0  = 4.8095264006406068801879883e-01,
        cis     = 1.639127731323242187500000e-07,
        i0      = 3.0369521630927920341491699e-01,
        crc     = 2.58750e+02,
        w       = 1.5755066927522420883178711e-01,
        omega_dot = -2.61093191511463373899459838867e-09,
        TGD      = -1.3504177331924438476562500e-08,
        SVH      = 0,
        L2P_Data = 0,
        Fit      = 0
    ),
    GpsLNAV(
        msgNum  = 1019,
        satNum  = 29,
        weekNum = 197,
        URA     = 0,
        L2_Codes= 1,
        i_dot   = 6.60520527162589132785797119141e-11,
        IODE    = 13,
        tc      = 403200,
        af2     = 0.000000000000000000000000000000000e+00,
        af1     = -2.27373675443232059478759765625e-12,
        af0     = -5.8132782578468322753906250e-04,
        IODC    = 13,
        crs     = 1.35250e+02,
        delta_n = 1.29296040540793910622596740723e-09,
        m0      = -4.6658467827364802360534668e-01,
        cuc     = 6.992369890213012695312500e-06,
        e       = 2.12917546741664409637451172e-03,
        cus     = 3.868713974952697753906250e-06,
        sqrt_a  = 5.1535955448150634766e+03,
        te      = 403200,
        cic     = 1.303851604461669921875000e-08,
        omega0  = -8.3556133788079023361206055e-01,
        cis     = 5.215406417846679687500000e-08,
        i0      = 3.1143780332058668136596680e-01,
        crc     = 3.155625e+02,
        w       = 7.6983935059979557991027832e-01,
        omega_dot = -2.54181031777989119291305541992e-09,
        TGD      = -1.0244548320770263671875000e-08,
        SVH      = 0,
        L2P_Data = 0,
        Fit      = 0
    )
]

# according to file RTCM3_TEST_DATA\EPH\msg1020.rtcm3
_R = [
    GloL1L2(
        msgNum     = 1020,                 
        satNum     = 12,
        frqSloNum  = 6-7,
        tk         = 17*3600 + 56*60 + 1*30,
        tb         = 71*15*60,
        xn         = 6.60460595703e+03,
        dotXn      = 6.81732177734375000000e-01,
        dotDotXn   = 0.0000000000000000000000000e+00,
        yn         = -1.34200781250e+04,
        dotYn      = 2.74372291564941406250e+00,
        dotDotYn   = 9.3132257461547851562500000e-10,
        zn         = 2.06747099609e+04,
        dotZn      = 1.56645488739013671875e+00,
        dotDotZn   = -3.7252902984619140625000000e-09,
        gamma_n    = 0.0000000000000000000000000000e+00,
        Cn         = 0,
        BnMSB      = 0,
        AlmHAI     = 0,
        P          = 3,
        P1         = 0,
        P2         = 1,
        P3         = 1,
        P4         = 1,
        ln3        = 0,
        tauN       = -2.4424865841865539550781250e-05,
        delta_tauN = 6.5192580223083496093750000e-09,
        En         = 0,
        Ft         = 1,
        Nt         = 1115,
        M          = 1,
        auxDataOK  = 1,
        Na         = 1114,
        tauC       = -5.5879354476928710937500000e-09,
        N4         = 7,
        tauGPS     = 5.0291419029235839843750000e-08,
        ln5        = 0
    ),
    GloL1L2(
        msgNum     = 1020,
        satNum     = 22,
        frqSloNum  = 4-7,
        tk         = 17*3600+56*60+1*30,
        tb         = 71*15*60,
        xn         = 2.44520112305e+04,
        dotXn      = 6.07126235961914062500e-01,
        dotDotXn   = -1.8626451492309570312500000e-09,
        yn         = 5.85529736328e+03,
        dotYn      = 1.63993835449218750000e-02,
        dotDotYn   = -1.8626451492309570312500000e-09,
        zn         = -4.21877832031e+03,
        dotZn      = 3.51753902435302734375e+00,
        dotDotZn   = 0.0000000000000000000000000e+00,
        gamma_n    = 1.8189894035458564758300781250e-12,
        Cn         = 0,
        BnMSB      = 0,
        AlmHAI     = 0,
        P          = 3,
        P1         = 0,
        P2         = 1,
        P3         = 1,
        P4         = 0,
        ln3        = 0,
        tauN       = -6.7307613790035247802734375e-05,
        delta_tauN = 3.7252902984619140625000000e-09,
        En         = 0,
        Ft         = 2,
        Nt         = 1115,
        M          = 1,
        auxDataOK  = 1,
        Na         = 1114,
        tauC       = -5.5879354476928710937500000e-09,
        N4         = 7,
        tauGPS     = 5.0291419029235839843750000e-08,
        ln5        = 0
    ),
    GloL1L2(
        msgNum     = 1020,
        satNum     = 2,
        frqSloNum  = 3-7,
        tk         = 17*3600 + 56*60 + 1*30,
        tb         = 71*15*60,
        xn         = 8.10478271484e+03,
        dotXn      = 1.44910812377929687500e+00,
        dotDotXn   = 0.0000000000000000000000000e+00,
        yn         = -1.83154677734e+04,
        dotYn      = -1.60379791259765625000e+00,
        dotDotYn   = 0.0000000000000000000000000e+00,
        zn         = 1.57957094727e+04,
        dotZn      = -2.61653804779052734375e+00,
        dotDotZn   = -3.7252902984619140625000000e-09,
        gamma_n    = 0.0000000000000000000000000000e+00,
        Cn         = 0,
        BnMSB      = 0,
        AlmHAI     = 0,
        P          = 3,
        P1         = 0,
        P2         = 1,
        P3         = 1,
        P4         = 0,
        ln3        = 0,
        tauN       = 2.3311004042625427246093750e-05,
        delta_tauN = 5.5879354476928710937500000e-09,
        En         = 0,
        Ft         = 2,
        Nt         = 1115,
        M          = 1,
        auxDataOK  = 1,
        Na         = 1115,
        tauC       = -5.1222741603851318359375000e-09,
        N4         = 7,
        tauGPS     = 4.9360096454620361328125000e-08,
        ln5        = 0
    )
]

# according to file RTCM3_TEST_DATA\EPH\msg1046.rtcm3
_EI = [
    GalINAV(),
    GalINAV(),
    GalINAV()
]

# according to file RTCM3_TEST_DATA\EPH\msg1042.rtcm3
_B = [
    BdsD1(),
    BdsD1(),
    BdsD1()
]

# according to file RTCM3_TEST_DATA\EPH\msg1041.rtcm3
_I = [
    NavicL5(),
    NavicL5(),
    NavicL5()
]

EPH_TEST_SCENARIO = {
    1019 : [r'RTCM3_TEST_DATA\EPH\msg1019.rtcm3', _G],
    1020 : [r'RTCM3_TEST_DATA\EPH\msg1020.rtcm3', _R],
    1046 : [r'RTCM3_TEST_DATA\EPH\msg1046.rtcm3', _EI],
    1042 : [r'RTCM3_TEST_DATA\EPH\msg1042.rtcm3', _B],
    1041 : [r'RTCM3_TEST_DATA\EPH\msg1041.rtcm3', _I]
    }

def getReferenceEphData(msgNum:int,satNum:int):
    """Return decoded and scaled ephemeris message"""

    test_sample = EPH_TEST_SCENARIO.get(msgNum)
        
    if not test_sample:
        return None
    
    ephs = test_sample[1]    
    for eph in ephs:
        if eph.satNum == satNum:
            return eph
        
    return None
