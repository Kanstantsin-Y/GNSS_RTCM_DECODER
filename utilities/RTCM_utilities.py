"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Functions/classes required for RTCM3 processing.
"""

# pylint: disable = invalid-name

__all__ = ["getSubset", "MSMT", "LEGT", "EPHT"]


def getSubset(num: int) -> tuple[str, str]:
    "Identify message subset and GNSS. Returns tuple: (<GNSS letter>, <Subset>)"

    if num in (1001, 1002, 1003, 1004, 1009, 1010, 1011, 1012):
        gnss, subset = LEGT.legacy_subset(num)
    elif num in (1019, 1020):
        gnss, subset = EPHT.eph_subset(num)
    elif 1041 <= num <= 1046:
        gnss, subset = EPHT.eph_subset(num)
    elif 1071 <= num <= 1137:
        gnss, subset = MSMT.msm_subset(num)
    else:
        gnss, subset = "", ""

    return gnss, subset


# ------------------------------------------------------------------------------------------------
class LEGT:
    """Classificator of Legacy Oservables messages."""

    CRNG_1MS: float = 299792.458  # [m]

    LEG1_MSG_LIST = {1001: "G", 1009: "R"}
    LEG2_MSG_LIST = {1002: "G", 1010: "R"}
    LEG3_MSG_LIST = {1003: "G", 1011: "R"}
    LEG4_MSG_LIST = {1004: "G", 1012: "R"}

    @classmethod
    def legacy_subset(cls, num: int) -> tuple[str, str]:
        """Classify legacy observables. Returns tuple: (<GNSS letter>, <LEG type>)."""
        if (num < 1001) or (num > 1012):
            return "", ""

        gnss = cls.LEG1_MSG_LIST.get(num)
        if gnss:
            return gnss, "LEG1"

        gnss = cls.LEG2_MSG_LIST.get(num)
        if gnss:
            return gnss, "LEG2"

        gnss = cls.LEG3_MSG_LIST.get(num)
        if gnss:
            return gnss, "LEG3"

        gnss = cls.LEG4_MSG_LIST.get(num)
        if gnss:
            return gnss, "LEG4"

        return "", ""


# ------------------------------------------------------------------------------------------------


class EPHT:
    """Classificator of ephemeris messages."""

    EPH_MSG_LIST = {
        1019: "G",
        1020: "R",
        1045: "E",
        1046: "E",
        1044: "Q",
        1042: "B",
        1041: "I",
    }

    @classmethod
    def eph_subset(cls, num: int) -> tuple[str, str]:
        """Classify EPH-message number. Returns tuple: (<GNSS letter>, "EPH")."""

        gnss = cls.EPH_MSG_LIST.get(num)

        if gnss:
            return gnss, "EPH"
        else:
            return "", ""


# ------------------------------------------------------------------------------------------------
class MSMT:
    """Classificator of MSM messages."""

    CRNG_1MS: float = 299792.458  # [m]

    MSM7_MSG_LIST = {
        1077: "G",
        1087: "R",
        1097: "E",
        1107: "S",
        1117: "Q",
        1127: "B",
        1137: "I",
    }
    MSM6_MSG_LIST = {
        1076: "G",
        1086: "R",
        1096: "E",
        1106: "S",
        1116: "Q",
        1126: "B",
        1136: "I",
    }
    MSM5_MSG_LIST = {
        1075: "G",
        1085: "R",
        1095: "E",
        1105: "S",
        1115: "Q",
        1125: "B",
        1135: "I",
    }
    MSM4_MSG_LIST = {
        1074: "G",
        1084: "R",
        1094: "E",
        1104: "S",
        1114: "Q",
        1124: "B",
        1134: "I",
    }
    MSM3_MSG_LIST = {
        1073: "G",
        1083: "R",
        1093: "E",
        1103: "S",
        1113: "Q",
        1123: "B",
        1133: "I",
    }
    MSM2_MSG_LIST = {
        1072: "G",
        1082: "R",
        1092: "E",
        1102: "S",
        1112: "Q",
        1122: "B",
        1132: "I",
    }
    MSM1_MSG_LIST = {
        1071: "G",
        1081: "R",
        1091: "E",
        1101: "S",
        1111: "Q",
        1121: "B",
        1131: "I",
    }

    # Signals. MSM-number-to-RNEX-ID conversion table
    __NAVIC_LIT = {8: "9A", 22: "5A"}

    __BDS_LIT = {
        2: "2I",
        3: "2Q",
        4: "2X",
        8: "6I",
        9: "6Q",
        10: "6X",
        14: "7I",
        15: "7Q",
        16: "7X",
    }

    __QZSS_LIT = {
        2: "1C",
        30: "1S",
        31: "1L",
        32: "1X",
        9: "6S",
        10: "6L",
        11: "6X",
        15: "2S",
        16: "2L",
        17: "2X",
        22: "5I",
        23: "5Q",
        24: "5X",
    }

    __SBAS_LIT = {2: "1C", 22: "5I", 23: "5Q", 24: "5X"}

    __GAL_LIT = {
        2: "1C",
        3: "1A",
        4: "1B",
        5: "1X",
        6: "1Z",
        8: "6C",
        9: "6A",
        10: "6B",
        11: "6X",
        12: "6Z",
        14: "7I",
        15: "7Q",
        16: "7X",
        18: "8I",
        19: "8Q",
        20: "8X",
        22: "5I",
        23: "5Q",
        24: "5X",
    }

    __GPS_LIT = {
        2: "1C",
        3: "1P",
        4: "1W",
        30: "1S",
        31: "1L",
        32: "1X",
        8: "2C",
        9: "2P",
        10: "2W",
        15: "2S",
        16: "2L",
        17: "2X",
        22: "5I",
        23: "5Q",
        24: "5X",
    }

    __GLN_LIT = {2: "1C", 3: "1P", 8: "2C", 9: "2P"}

    __MSM2RINEX_TAB = {
        "G": __GPS_LIT,
        "R": __GLN_LIT,
        "E": __GAL_LIT,
        "S": __SBAS_LIT,
        "Q": __QZSS_LIT,
        "B": __BDS_LIT,
        "I": __NAVIC_LIT,
    }

    # Signals. RNEX-slot-to-central-frequency conversion table.
    __NAVIC_CF = {
        "5A": 1176.45,
        "5B": 1176.45,
        "5C": 1176.45,
        "5X": 1176.45,
        "9A": 2492.028,
        "9B": 2492.028,
        "9C": 2492.028,
        "9X": 2492.028,
    }

    __BDS_CF = {
        "2I": 1561.098,
        "2Q": 1561.098,
        "2X": 1561.098,
        "1D": 1575.42,
        "1P": 1575.42,
        "1X": 1575.42,
        "1A": 1575.42,
        "1N": 1575.42,
        "5D": 1176.45,
        "5P": 1176.45,
        "5X": 1176.45,
        "7I": 1207.140,
        "7Q": 1207.140,
        "7X": 1207.140,
        "7D": 1207.140,
        "7P": 1207.140,
        "7Z": 1207.140,
        "8D": 1191.795,
        "8P": 1191.795,
        "8X": 1191.795,
        "6I": 1268.52,
        "6Q": 1268.52,
        "6X": 1268.52,
    }

    __QZSS_CF = {
        "1C": 1575.42,
        "1S": 1575.42,
        "1L": 1575.42,
        "1X": 1575.42,
        "1Z": 1575.42,
        "2S": 1227.60,
        "2L": 1227.60,
        "2X": 1227.60,
        "5I": 1176.45,
        "5Q": 1176.45,
        "5X": 1176.45,
        "5D": 1176.45,
        "5P": 1176.45,
        "5Z": 1176.45,
        "6S": 1278.75,
        "6L": 1278.75,
        "6X": 1278.75,
        "6E": 1278.75,
        "6Z": 1278.75,
    }

    __SBAS_CF = {"1C": 1575.42, "5I": 1176.45, "5Q": 1176.45, "5X": 1176.45}

    __GAL_CF = {
        "1A": 1575.42,
        "1B": 1575.42,
        "1C": 1575.42,
        "1Z": 1575.42,
        "1X": 1575.42,
        "5I": 1176.45,
        "5Q": 1176.45,
        "5X": 1176.45,
        "7I": 1207.140,
        "7Q": 1207.140,
        "7X": 1207.140,
        "8I": 1191.795,
        "8Q": 1191.795,
        "8X": 1191.795,
        "6A": 1278.75,
        "6B": 1278.75,
        "6C": 1278.75,
        "6X": 1278.75,
        "6Z": 1278.75,
    }

    __GPS_CF = {
        "1C": 1575.42,
        "1S": 1575.42,
        "1L": 1575.42,
        "1X": 1575.42,
        "1P": 1575.42,
        "1W": 1575.42,
        "1Y": 1575.42,
        "1M": 1575.42,
        "1N": 1575.42,
        "2C": 1227.60,
        "2D": 1227.60,
        "2S": 1227.60,
        "2L": 1227.60,
        "2X": 1227.60,
        "2P": 1227.60,
        "2W": 1227.60,
        "2Y": 1227.60,
        "2M": 1227.60,
        "2N": 1227.60,
        "5I": 1176.45,
        "5Q": 1176.45,
        "5X": 1176.45,
    }

    __GLN_CF = {
        "1C": 1602.0,
        "1P": 1602.0,
        "4A": 1600.995,
        "4B": 1600.995,
        "4X": 1600.995,
        "2C": 1246.0,
        "2P": 1246.0,
        "6A": 1248.06,
        "6B": 1248.06,
        "6X": 1248.06,
        "25": 1202.0,
        "3I": 1202.0,
        "3Q": 1202.0,
        "3X": 1202.0,
    }

    _RINEX_CF_TAB = {
        "G": __GPS_CF,
        "R": __GLN_CF,
        "E": __GAL_CF,
        "S": __SBAS_CF,
        "Q": __QZSS_CF,
        "B": __BDS_CF,
        "I": __NAVIC_CF,
    }

    @classmethod
    def rnx_lit(cls, gnss: str, msm_code: int) -> str | None:
        """Convert MSM signal code to RINEX signal ID.

        'gnss' - gnss letter (RINEX style),
        'msm_code' - 1..32 signal number
        'return' - RINEX signal ID"""

        tab = cls.__MSM2RINEX_TAB.get(gnss)
        return tab.get(msm_code) if tab else None

    @classmethod
    def crr_frq(cls, gnss: str, sgn: str):
        """Returns carrier frequency value for 'sgn' signal
        of 'gnss' navigation system in kHz. 'gnss' and 'sgn'
        are in rinex notation."""

        return cls._RINEX_CF_TAB[gnss][sgn]

    @classmethod
    def msm_subset(cls, num: int) -> tuple[str, str]:
        """Classify MSM number. Returns tuple: (<GNSS letter>, <MSM type>)."""
        if (num < 1071) or (num > 1137):
            return "", ""

        gnss = cls.MSM7_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM7"

        gnss = cls.MSM6_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM6"

        gnss = cls.MSM5_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM5"

        gnss = cls.MSM4_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM4"

        gnss = cls.MSM3_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM3"

        gnss = cls.MSM2_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM2"

        gnss = cls.MSM1_MSG_LIST.get(num)
        if gnss:
            return gnss, "MSM1"

        return "", ""

    @staticmethod
    def unpack_clk_steer(code: int) -> str:
        """Convert DF411 field into verbose form"""
        if code == 0:
            return "OFF"  # 1 ms range
        elif code == 1:
            return "ON"  # 1 mks range
        else:
            return "UNDEF"

    @staticmethod
    def unpack_clk_ext(code: int) -> str:
        """Convert DF412 field into verbose form"""
        if code == 0:
            return "INTERNAL"
        elif code == 1:
            return "EXT-LOCK"
        elif code == 2:
            return "EXT-UNLOCK"
        else:
            return "UNDEF"

    @staticmethod
    def unpack_smth_indc(code: int) -> str:
        """Convert DF417 field into verbose form"""
        return "DVRG-FREE" if code == 1 else "UNDEF"

    @staticmethod
    def unpack_smth_intr(code: int) -> str:
        """Convert DF418 field into verbose form"""
        if code == 0:
            return "NOSMTH"
        elif code == 1:
            return "00-30"
        elif code == 2:
            return "30-60"
        elif code == 3:
            return "60-120"
        elif code == 4:
            return "120-240"
        elif code == 5:
            return "240-480"
        elif code == 6:
            return "480+"
        else:
            return "UNLIM"

    @staticmethod
    def unpack_tlock10(t: int) -> int:
        """Converts DF407 index into time, [ms]"""

        if t < 64:
            rv = t
        elif t < 704:
            k = (t >> 5) - 1
            rv = (1 << k) * (t - 32 * k)
        elif t == 704:
            rv = 67108864
        else:
            rv = 0

        return rv

    @staticmethod
    def unpack_tlock4(t: int) -> int:
        """Converts DF402 index into time, [ms]"""
        return 0 if t == 0 else (1 << (4 + t))

    @staticmethod
    def isDF405_OK(x: int) -> bool:
        """Check for DF405 error indicator."""
        return (x & 0xFFFFF) != 0x80000

    @staticmethod
    def isDF406_OK(x: int) -> bool:
        """Check for DF406 error indicator."""
        return (x & 0xFFFFFF) != 0x800000

    @staticmethod
    def isDF400_OK(x: int) -> bool:
        """Check for DF400 error indicator."""
        return (x & 0x7FFF) != 0x4000

    @staticmethod
    def isDF401_OK(x: int) -> bool:
        """Check for DF401 error indicator."""
        return (x & 0x3FFFFF) != 0x200000

    @staticmethod
    def isDF404_OK(x: int) -> bool:
        """Check for DF404 error indicator."""
        return (x & 0x7FFF) != 0x4000
