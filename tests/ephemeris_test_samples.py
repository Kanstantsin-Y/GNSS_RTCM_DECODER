"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Functions/classes required for validation of decoding of ephemeris messages.
"""

# pylint: disable = invalid-name, consider-iterating-dictionary, broad-exception-caught

import os
import json
from typing import Any

import gnss_types as gt

from run_conversion import main as convert
from sub_decoders import EphemerisDecoder as ED
from printers import PrintJSON as PJ


__all__ = ["test_eph_message"]


def eph_test_scenario(msg: int) -> tuple[str, list[Any]]:
    """Provides attributes for epemeris test."""
    match msg:
        case 1019:
            return r"RTCM3_TEST_DATA/EPH/msg1019.rtcm3", _G
        case 1020:
            return r"RTCM3_TEST_DATA/EPH/msg1020.rtcm3", _R
        case 1045:
            return r"RTCM3_TEST_DATA/EPH/msg1045.rtcm3", _EF
        case 1046:
            return r"RTCM3_TEST_DATA/EPH/msg1046.rtcm3", _EI
        case 1042:
            return r"RTCM3_TEST_DATA/EPH/msg1042.rtcm3", _B
        case 1041:
            return r"RTCM3_TEST_DATA/EPH/msg1041.rtcm3", _I
        case _:
            assert False, f"no test data for MSG{msg}"


def _determin_type(tname: str) -> type:
    """Returns data class by the textual name of data class."""
    assert (
        tname in gt.__dict__.keys()
    ), 'Product type is absent in the module "gnss_types"'
    return gt.__dict__.get(tname)  # type: ignore


def _test_eph(msgNum: int, mode: str) -> bool:
    """Convert test data and compare with the reference"""

    ts = eph_test_scenario(msgNum)
    tpath, refs = ts
    cargs = "-o " + mode + " " + tpath
    # cargs = "-o " + mode + ' -i addons.ini' + ' ' + tpath
    convert(cargs)

    ofile, *_ = PJ.make_opath(tpath, msgNum, mode)
    assert os.path.isfile(ofile), "Output file not found"

    with open(ofile, "r", encoding="utf-8") as file:
        ephs = json.load(file)

    tp = ephs.pop(0)
    tp = _determin_type(tp["source_type"])

    assert len(ephs) == len(
        refs
    ), f"Unexpected number of output products: {len(ephs)}."

    for i, _ in enumerate(ephs):
        ref = refs[i]
        eph = tp(**ephs[i])
        if mode == "JSON-B":
            eph = ED.scale(eph)
        if isinstance(eph, gt.DataClassMethods):
            assert eph.compare(
                ref, 1e-15
            ), f"Product {i} is not equal to reference."

    return True


def test_eph_message(msgNum: int, mode: str) -> bool:
    """Test single epemeris message."""

    print("-" * 80)
    print(f"TESTER: start conversion MSG{msgNum} to {mode}.")

    ret = False

    if not mode in ("JSON", "JSON-B"):
        print(f"TESTER: format {mode} is not supported in this test")
        return ret

    try:
        ret = _test_eph(msgNum, mode)
        print("TESTER: status SUCCEED.")
    except AssertionError as asrt:
        print(f"TESTER: status FAILED. {asrt.args[0]}")
    except Exception:
        print("TESTER: status FAILED. Unexpected error")

    return ret


# according to file RTCM3_TEST_DATA/EPH/msg1019.rtcm3
_G = [
    gt.EphGPS(
        msgNum=1019,
        satNum=32,
        weekNum=197,
        URA=0,
        L2_Codes=1,
        i_dot=2.10434336622711271047592163086e-10,
        IODE=68,
        tc=403200,
        af2=0.000000000000000000000000000000000e00,
        af1=-1.22781784739345312118530273438e-11,
        af0=-3.6916276440024375915527344e-04,
        IODC=68,
        crs=-8.18750e00,
        delta_n=1.50805590237723663449287414551e-09,
        m0=-2.3986937897279858589172363e-01,
        cuc=-3.036111593246459960937500e-07,
        e=6.48663751780986785888671875e-03,
        cus=9.274110198020935058593750e-06,
        sqrt_a=5.1536912937164306641e03,
        te=403200,
        cic=1.490116119384765625000000e-08,
        omega0=1.3762591034173965454101563e-01,
        cis=1.713633537292480468750000e-07,
        i0=3.0539020989090204238891602e-01,
        crc=2.005625e02,
        w=-7.2424596967175602912902832e-01,
        omega_dot=-2.52248355536721646785736083984e-09,
        TGD=4.6566128730773925781250000e-10,
        SVH=0,
        L2P_Data=0,
        Fit=0,
    ),
    gt.EphGPS(
        msgNum=1019,
        satNum=31,
        weekNum=197,
        URA=0,
        L2_Codes=1,
        i_dot=-1.33354660647455602884292602539e-10,
        IODE=72,
        tc=403200,
        af2=0.000000000000000000000000000000000e00,
        af1=-1.13686837721616029739379882813e-12,
        af0=-2.0678620785474777221679688e-04,
        IODC=72,
        crs=-1.56250e-01,
        delta_n=1.65141500474419444799423217773e-09,
        m0=4.4719802075996994972229004e-01,
        cuc=2.384185791015625000000000e-07,
        e=1.07931792736053466796875000e-02,
        cus=6.247311830520629882812500e-06,
        sqrt_a=5.1536309185028076172e03,
        te=403200,
        cic=-6.519258022308349609375000e-08,
        omega0=4.8095264006406068801879883e-01,
        cis=1.639127731323242187500000e-07,
        i0=3.0369521630927920341491699e-01,
        crc=2.58750e02,
        w=1.5755066927522420883178711e-01,
        omega_dot=-2.61093191511463373899459838867e-09,
        TGD=-1.3504177331924438476562500e-08,
        SVH=0,
        L2P_Data=0,
        Fit=0,
    ),
    gt.EphGPS(
        msgNum=1019,
        satNum=29,
        weekNum=197,
        URA=0,
        L2_Codes=1,
        i_dot=6.60520527162589132785797119141e-11,
        IODE=13,
        tc=403200,
        af2=0.000000000000000000000000000000000e00,
        af1=-2.27373675443232059478759765625e-12,
        af0=-5.8132782578468322753906250e-04,
        IODC=13,
        crs=1.35250e02,
        delta_n=1.29296040540793910622596740723e-09,
        m0=-4.6658467827364802360534668e-01,
        cuc=6.992369890213012695312500e-06,
        e=2.12917546741664409637451172e-03,
        cus=3.868713974952697753906250e-06,
        sqrt_a=5.1535955448150634766e03,
        te=403200,
        cic=1.303851604461669921875000e-08,
        omega0=-8.3556133788079023361206055e-01,
        cis=5.215406417846679687500000e-08,
        i0=3.1143780332058668136596680e-01,
        crc=3.155625e02,
        w=7.6983935059979557991027832e-01,
        omega_dot=-2.54181031777989119291305541992e-09,
        TGD=-1.0244548320770263671875000e-08,
        SVH=0,
        L2P_Data=0,
        Fit=0,
    ),
]

# according to file RTCM3_TEST_DATA/EPH/msg1020.rtcm3
_R = [
    gt.EphGLO(
        msgNum=1020,
        satNum=12,
        frqSloNum=6 - 7,
        tk=17 * 3600 + 56 * 60 + 1 * 30,
        tb=71 * 15 * 60,
        xn=6604.60595703125,
        dotXn=6.81732177734375000000e-01,
        dotDotXn=0.0000000000000000000000000e00,
        yn=-1.34200781250e04,
        dotYn=2.74372291564941406250e00,
        dotDotYn=9.3132257461547851562500000e-10,
        zn=20674.7099609375,
        dotZn=1.56645488739013671875e00,
        dotDotZn=-3.7252902984619140625000000e-09,
        gamma_n=0.0000000000000000000000000000e00,
        Cn=0,
        BnMSB=0,
        AlmHAI=0,
        P=3,
        P1=0,
        P2=1,
        P3=1,
        P4=1,
        ln3=0,
        tauN=-2.4424865841865539550781250e-05,
        delta_tauN=6.5192580223083496093750000e-09,
        En=0,
        Ft=1,
        Nt=1115,
        M=1,
        auxDataOK=1,
        Na=1114,
        tauC=-5.5879354476928710937500000e-09,
        N4=7,
        tauGPS=5.0291419029235839843750000e-08,
        ln5=0,
    ),
    gt.EphGLO(
        msgNum=1020,
        satNum=22,
        frqSloNum=4 - 7,
        tk=17 * 3600 + 56 * 60 + 1 * 30,
        tb=71 * 15 * 60,
        xn=24452.01123046875,
        dotXn=6.07126235961914062500e-01,
        dotDotXn=-1.8626451492309570312500000e-09,
        yn=5855.29736328125,
        dotYn=1.63993835449218750000e-02,
        dotDotYn=-1.8626451492309570312500000e-09,
        zn=-4218.7783203125,
        dotZn=3.51753902435302734375e00,
        dotDotZn=0.0000000000000000000000000e00,
        gamma_n=1.8189894035458564758300781250e-12,
        Cn=0,
        BnMSB=0,
        AlmHAI=0,
        P=3,
        P1=0,
        P2=1,
        P3=1,
        P4=0,
        ln3=0,
        tauN=-6.7307613790035247802734375e-05,
        delta_tauN=3.7252902984619140625000000e-09,
        En=0,
        Ft=2,
        Nt=1115,
        M=1,
        auxDataOK=1,
        Na=1114,
        tauC=-5.5879354476928710937500000e-09,
        N4=7,
        tauGPS=5.0291419029235839843750000e-08,
        ln5=0,
    ),
    gt.EphGLO(
        msgNum=1020,
        satNum=2,
        frqSloNum=3 - 7,
        tk=17 * 3600 + 56 * 60 + 1 * 30,
        tb=71 * 15 * 60,
        xn=8104.78271484375,
        dotXn=1.44910812377929687500e00,
        dotDotXn=0.0000000000000000000000000e00,
        yn=-18315.4677734375,
        dotYn=-1.60379791259765625000e00,
        dotDotYn=0.0000000000000000000000000e00,
        zn=15795.70947265625,
        dotZn=-2.61653804779052734375e00,
        dotDotZn=-3.7252902984619140625000000e-09,
        gamma_n=0.0000000000000000000000000000e00,
        Cn=0,
        BnMSB=0,
        AlmHAI=0,
        P=3,
        P1=0,
        P2=1,
        P3=1,
        P4=0,
        ln3=0,
        tauN=2.3311004042625427246093750e-05,
        delta_tauN=5.5879354476928710937500000e-09,
        En=0,
        Ft=2,
        Nt=1115,
        M=1,
        auxDataOK=1,
        Na=1115,
        tauC=-5.1222741603851318359375000e-09,
        N4=7,
        tauGPS=4.9360096454620361328125000e-08,
        ln5=0,
    ),
]

# according to file RTCM3_TEST_DATA/EPH/msg1046.rtcm3
_EI = [
    gt.EphGALI(
        msgNum=1046,
        satNum=31,
        weekNum=1221,
        tc=398400,
        af0=-5.13730919919908046722412109e-04,
        af1=-1.008970684779342263936996459961e-12,
        af2=0.000000000000000000000000000000000e00,
        te=398400,
        delta_n=8.66862137627322226762771606445e-10,
        m0=7.0258465083315968513488770e-01,
        e=2.45926552452147006988525391e-04,
        sqrt_a=5.4406237583160400391e03,
        w=-9.5354759600013494491577148e-02,
        i0=3.0893438030034303665161133e-01,
        i_dot=-2.19415596802718937397003173828e-10,
        omega0=7.8707502502948045730590820e-01,
        omega_dot=-1.63583990797633305191993713379e-09,
        crs=7.80000e01,
        crc=9.90000e01,
        cuc=3.604218363761901855468750e-06,
        cus=1.148879528045654296875000e-05,
        cic=3.352761268615722656250000e-08,
        cis=1.117587089538574218750000e-08,
        IODnav=24,
        SISA=107,
        E5a_BGD=6.28642737865447998046875000e-09,
        E5b_BGD=6.75208866596221923828125000e-09,
        E1_SHS=0,
        E1_DVS=0,
        E5b_SHS=0,
        E5b_DVS=0,
    ),
    gt.EphGALI(
        msgNum=1046,
        satNum=26,
        weekNum=1221,
        tc=398400,
        af0=-1.84679211815819144248962402e-03,
        af1=1.121236437029438093304634094238e-11,
        af2=0.000000000000000000000000000000000e00,
        te=398400,
        delta_n=9.12223185878247022628784179688e-10,
        m0=9.3852098612114787101745605e-01,
        e=2.84455833025276660919189453e-04,
        sqrt_a=5.4406046161651611328e03,
        w=-4.9730537133291363716125488e-01,
        i0=3.1576013471931219100952148e-01,
        i_dot=-8.86757334228605031967163085938e-12,
        omega0=-5.4805575637146830558776855e-01,
        omega_dot=-1.87571913556894287467002868652e-09,
        crs=-41.84375,
        crc=432.03125,
        cuc=-1.972541213035583496093750e-06,
        cus=-3.525987267494201660156250e-06,
        cic=3.725290298461914062500000e-08,
        cis=-4.842877388000488281250000e-08,
        IODnav=24,
        SISA=107,
        E5a_BGD=-3.95812094211578369140625000e-09,
        E5b_BGD=-4.42378222942352294921875000e-09,
        E1_SHS=0,
        E1_DVS=0,
        E5b_SHS=0,
        E5b_DVS=0,
    ),
    gt.EphGALI(
        msgNum=1046,
        satNum=24,
        weekNum=1221,
        tc=398400,
        af0=-1.06669130036607384681701660e-03,
        af1=-2.106048668792936950922012329102e-11,
        af2=0.000000000000000000000000000000000e00,
        te=398400,
        delta_n=9.16884346224833279848098754883e-10,
        m0=1.4834178797900676727294922e-01,
        e=7.57179339416325092315673828e-04,
        sqrt_a=5.4406266918182373047e03,
        w=2.2021013172343373298645020e-01,
        i0=3.0826849490404129028320313e-01,
        i_dot=-2.21234586206264793872833251953e-10,
        omega0=7.8831104189157485961914063e-01,
        omega_dot=-1.64982338901609182357788085938e-09,
        crs=95.96875,
        crc=106.5625,
        cuc=4.541128873825073242187500e-06,
        cus=1.108273863792419433593750e-05,
        cic=5.215406417846679687500000e-08,
        cis=5.587935447692871093750000e-09,
        IODnav=24,
        SISA=107,
        E5a_BGD=-3.49245965480804443359375000e-09,
        E5b_BGD=-4.19095158576965332031250000e-09,
        E1_SHS=0,
        E1_DVS=0,
        E5b_SHS=0,
        E5b_DVS=0,
    ),
]

_EF = [
    gt.EphGALF(
        msgNum=1045,
        satNum=13,
        weekNum=1119,
        tc=489600,
        af0=-3.85084131266921758651733398e-04,
        af1=-4.234834705130197107791900634766e-12,
        af2=0.0,
        te=489600,
        delta_n=1.20462573249824345111846923828e-09,
        m0=-4.1043115779757499694824219e-02,
        e=3.01621854305267333984375000e-04,
        sqrt_a=4.0959999980926513672e03,
        w=2.6684320438653230667114258e-01,
        i0=3.0373554164543747901916504e-01,
        i_dot=-1.79625203600153326988220214844e-11,
        omega0=2.9648526851087808609008789e-01,
        omega_dot=-1.85616499948082491755485534668e-09,
        crs=-2.73750e01,
        crc=2.1028125e02,
        cuc=-1.426786184310913085937500e-06,
        cus=5.986541509628295898437500e-06,
        cic=2.980232238769531250000000e-08,
        cis=1.862645149230957031250000e-08,
        IODnav=48,
        SISA=107,
        E5a_BGD=2.79396772384643554687500000e-09,
        E5a_SHS=0,
        E5a_DVS=0,
    ),
    gt.EphGALF(
        msgNum=1045,
        satNum=14,
        weekNum=1119,
        tc=485400,
        af0=-7.03603844158351421356201172e-04,
        af1=-7.815970093361102044582366943359e-12,
        af2=0.0,
        te=485400,
        delta_n=1.16415321826934814453125000000e-09,
        m0=-9.3016382772475481033325195e-01,
        e=4.59732254967093467712402344e-05,
        sqrt_a=4.0959999980926513672e03,
        w=-7.8876551426947116851806641e-01,
        i0=3.0394269200041890144348145e-01,
        i_dot=2.44426701101474463939666748047e-11,
        omega0=1.3891745265573263168334961e-01,
        omega_dot=-1.82819803740130737423896789551e-09,
        crs=-2.55625e01,
        crc=1.8734375e02,
        cuc=-1.391395926475524902343750e-06,
        cus=7.012858986854553222656250e-06,
        cic=2.980232238769531250000000e-08,
        cis=9.313225746154785156250000e-09,
        IODnav=41,
        SISA=107,
        E5a_BGD=-3.02679836750030517578125000e-09,
        E5a_SHS=3,
        E5a_DVS=1,
    ),
    gt.EphGALF(
        msgNum=1045,
        satNum=15,
        weekNum=1119,
        tc=489600,
        af0=-3.14562232233583927154541016e-04,
        af1=3.097966327914036810398101806641e-12,
        af2=0.0,
        te=489600,
        delta_n=1.19689502753317356109619140625e-09,
        m0=-2.9462144244462251663208008e-02,
        e=1.42013770528137683868408203e-04,
        sqrt_a=4.0959999980926513672e03,
        w=5.0688092550262808799743652e-01,
        i0=3.0373969580978155136108398e-01,
        i_dot=-1.62572177941910922527313232422e-11,
        omega0=2.9648230876773595809936523e-01,
        omega_dot=-1.85491444426588714122772216797e-09,
        crs=-2.88750e01,
        crc=2.078125e02,
        cuc=-1.367181539535522460937500e-06,
        cus=5.939975380897521972656250e-06,
        cic=1.862645149230957031250000e-09,
        cis=6.705522537231445312500000e-08,
        IODnav=48,
        SISA=107,
        E5a_BGD=3.25962901115417480468750000e-09,
        E5a_SHS=0,
        E5a_DVS=0,
    ),
]


# according to file RTCM3_TEST_DATA/EPH/msg1042.rtcm3
_B = [
    gt.EphBDS(
        msgNum=1042,
        satNum=11,
        weekNum=889,
        tc=396000,
        af0=-1.69055419974029064178466797e-04,
        af1=2.0458301719372684601694345474243e-11,
        af2=0.0,
        te=396000,
        delta_n=1.07183950603939592838287353516e-09,
        m0=7.5426618661731481552124023e-01,
        e=2.20211397390812635421752930e-03,
        sqrt_a=5.2826134490966796875e03,
        w=-5.5255910055711865425109863e-01,
        i0=3.1453688256442546844482422e-01,
        i_dot=6.60520527162589132785797119141e-11,
        omega0=-7.0987578993663191795349121e-01,
        omega_dot=-2.19336016016313806176185607910e-09,
        crs=86.859375,
        crc=385.296875,
        cuc=4.3073669075965881347656250e-06,
        cus=-5.2992254495620727539062500e-07,
        cic=4.7031790018081665039062500e-08,
        cis=6.9849193096160888671875000e-09,
        AODE=20,
        AODC=0,
        SVH=1,
        URAI=0,
        TGD1=4.3000000000e-09,
        TGD2=1.7000000000e-09,
    ),
    gt.EphBDS(
        msgNum=1042,
        satNum=12,
        weekNum=889,
        tc=396000,
        af0=4.05856408178806304931640625e-04,
        af1=1.9801937867214292054995894432068e-11,
        af2=0e00,
        te=396000,
        delta_n=1.06251718534622341394424438477e-09,
        m0=9.6775119937956333160400391e-01,
        e=1.29693408962339162826538086e-03,
        sqrt_a=5.2826118469238281250e03,
        w=-5.2105836756527423858642578e-01,
        i0=3.1406169291585683822631836e-01,
        i_dot=7.02584657119587063789367675781e-11,
        omega0=-7.1371181588619947433471680e-01,
        omega_dot=-2.20188667299225926399230957031e-09,
        crs=98.140625,
        crc=369.859375,
        cuc=4.9462541937828063964843750e-06,
        cus=2.3189932107925415039062500e-07,
        cic=2.1886080503463745117187500e-08,
        cis=2.3283064365386962890625000e-08,
        AODE=1,
        AODC=0,
        SVH=0,
        URAI=0,
        TGD1=3.3000000000e-09,
        TGD2=0.0000000000e00,
    ),
    gt.EphBDS(
        msgNum=1042,
        satNum=8,
        weekNum=889,
        tc=396000,
        af0=5.27856522239744663238525391e-04,
        af1=1.8207657603852567262947559356689e-13,
        af2=0e00,
        te=396000,
        delta_n=1.29261934489477425813674926758e-10,
        m0=-9.0804585628211498260498047e-01,
        e=2.52199952956289052963256836e-03,
        sqrt_a=6.4929606914520263672e03,
        w=-9.7549673402681946754455566e-01,
        i0=3.3661110280081629753112793e-01,
        i_dot=-1.30853550217580050230026245117e-10,
        omega0=-3.4455005777999758720397949e-01,
        omega_dot=-6.67796484776772558689117431641e-10,
        crs=-765.40625,
        crc=270.171875,
        cuc=-2.5115441530942916870117188e-05,
        cus=1.1408701539039611816406250e-07,
        cic=-1.6950070858001708984375000e-07,
        cis=-2.7474015951156616210937500e-08,
        AODE=0,
        AODC=0,
        SVH=0,
        URAI=0,
        TGD1=1.1600000000e-08,
        TGD2=-8.0000000000e-10,
    ),
]

# according to file RTCM3_TEST_DATA/EPH/msg1041.rtcm3
_I = [
    gt.EphNAVIC(
        msgNum=1041,
        satNum=6,
        weekNum=197,
        tc=399024,
        af0=4.7382619231939315795898438e-04,
        af1=7.37827576813288033008575439453e-11,
        af2=0.000000000000000000000000000000000e00,
        te=399024,
        delta_n=6.6729626269079744815826416016e-09,
        m0=2.8355306154116988182067871e-01,
        e=2.32746696565300226211547852e-03,
        sqrt_a=6.4935362281799316406e03,
        w=-9.9264327669516205787658691e-01,
        i0=1.3885335996747016906738281e-02,
        i_dot=2.00316208065487444400787353516e-10,
        omega0=1.5178411826491355895996094e-01,
        omega_dot=-6.2764229369349777698516845703e-09,
        crs=6.6350e02,
        crc=4.8625e01,
        cuc=2.201274037361145019531250e-05,
        cus=-1.687556505203247070312500e-06,
        cic=-1.117587089538574218750000e-08,
        cis=1.639127731323242187500000e-07,
        URA=0,
        TGD=-1.8626451492309570312500000e-09,
        IODEC=220,
    ),
    gt.EphNAVIC(
        msgNum=1041,
        satNum=3,
        weekNum=197,
        tc=396000,
        af0=-5.0594331696629524230957031e-04,
        af1=-2.93312041321769356727600097656e-11,
        af2=0.000000000000000000000000000000000e00,
        te=396000,
        delta_n=4.0495251596439629793167114258e-09,
        m0=-4.2506487946957349777221680e-01,
        e=1.69275084044784307479858398e-03,
        sqrt_a=6.4934780826568603516e03,
        w=4.6045118011534214019775391e-02,
        i0=1.9125337712466716766357422e-02,
        i_dot=2.55795384873636066913604736328e-10,
        omega0=3.1842715106904506683349609e-02,
        omega_dot=-3.6920937418472021818161010742e-09,
        crs=493.3125,
        crc=-485.9375,
        cuc=1.611188054084777832031250e-05,
        cus=1.614913344383239746093750e-05,
        cic=2.086162567138671875000000e-07,
        cis=1.005828380584716796875000e-07,
        URA=0,
        TGD=-1.3969838619232177734375000e-09,
        IODEC=7,
    ),
    gt.EphNAVIC(
        msgNum=1041,
        satNum=2,
        weekNum=197,
        tc=399024,
        af0=2.2758590057492256164550781e-04,
        af1=-2.78532752417959272861480712891e-11,
        af2=0.000000000000000000000000000000000e00,
        te=399024,
        delta_n=9.0949470177292823791503906250e-10,
        m0=-2.4595478642731904983520508e-01,
        e=1.86042161658406257629394531e-03,
        sqrt_a=6.4934688835144042969e03,
        w=9.9464357830584049224853516e-01,
        i0=1.6193800885230302810668945e-01,
        i_dot=-3.53793438989669084548950195313e-10,
        omega0=8.1917671207338571548461914e-01,
        omega_dot=-7.5260686571709811687469482422e-10,
        crs=97.375,
        crc=-595.3125,
        cuc=2.812594175338745117187500e-06,
        cus=2.261251211166381835937500e-05,
        cic=2.123415470123291015625000e-07,
        cis=3.725290298461914062500000e-09,
        URA=0,
        TGD=-1.8626451492309570312500000e-09,
        IODEC=220,
    ),
]
