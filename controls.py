"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements functionality for reading control parameters from *.ini files.
"""

# pylint: disable = invalid-name

from configparser import ConfigParser
from printers import MargoControls
from printers import JSONControls


class BoxWithConverterControls:
    """Container for summary of converter controls"""

    def __init__(self, inMARGO: MargoControls, inJSON: JSONControls) -> None:
        self.__MARGO = inMARGO
        self.__JSON = inJSON

    @property
    def MARGO(self) -> MargoControls:
        """Get MARGO properties."""
        return self.__MARGO

    @property
    def JSON(self) -> JSONControls:
        """Get JSON properties."""
        return self.__JSON


class ConverterControls:
    """Controls manager."""

    def __init__(self) -> None:
        self.__MARGO = MargoControls()
        self.__JSON = JSONControls()
        self.__ini = ConfigParser()
        self.__ini_ok = False
        self.__MARGO_ok = False
        self.__JSON_ok = False

    def _read_ini(self, ini_file: str) -> bool:
        """Read *ini file. Return true if there is something in it."""
        self.__ini.read(ini_file)
        rv = len(self.__ini.sections()) != 0
        if not rv:
            print(f"INI file {ini_file} is corrupted or empty.")

        return rv

    def _make_MARGO(self) -> bool:
        """Compose controls for MARGO printer"""
        if not self.__ini_ok:
            return False

        if "LITERALS" not in self.__ini.sections():
            return False

        if "TIME" not in self.__ini.sections():
            return False

        if "MARGO" not in self.__ini.sections():
            return False

        lt = {}
        mask: int = 0

        keys = set(self.__ini["LITERALS"])
        # 'keys' collects garbage from 'DEFAULT'
        if "DEFAULT" in self.__ini.sections():
            keys = keys - set(self.__ini["DEFAULT"])

        for key in keys:
            sat = int(key.strip("rR"))
            if 0 < sat <= 24:
                mask |= 1 << (sat - 1)
                lt.update({sat: self.__ini["LITERALS"].getint(key)})

        res = MargoControls()

        if mask == 0xFFFFFF:
            res.glo_lit_tab = lt
        else:
            return False

        res.gps_utc_shift = self.__ini["TIME"].getint("GPS2UTC")
        if res.gps_utc_shift is None:
            return False

        res.half_cycle_enable = self.__ini["MARGO"].getboolean("HCA")
        if res.half_cycle_enable is None:
            return False

        res.lock_time_enable = self.__ini["MARGO"].getboolean("LOCK_TIME")
        if res.lock_time_enable is None:
            return False

        self.__MARGO = res
        return True

    def _make_JSON(self) -> bool:
        """Compose controls for JSON printer"""
        if not self.__ini_ok:
            return False

        if "JSON" not in self.__ini.sections():
            return False

        res = JSONControls()

        res.enable_hdr_data = self.__ini["JSON"].getboolean("ENABLE_HDR_DATA")
        if res.enable_hdr_data is None:
            return False

        res.enable_aux_data = self.__ini["JSON"].getboolean("ENABLE_AUX_DATA")
        if res.enable_aux_data is None:
            return False

        res.enable_pretty_view = self.__ini["JSON"].getboolean("ENABLE_PRETTY_VIEW")
        if res.enable_pretty_view is None:
            return False

        self.__JSON = res
        return True

    def init_from_file(self, ini_file: str):
        """Update controls from *.ini file"""
        self.__ini_ok = self._read_ini(ini_file)
        if self.__ini_ok:
            self.__MARGO_ok = self._make_MARGO()
            self.__JSON_ok = self._make_JSON()

    def update_from_file(self, ini_file: str):
        """Update controls from *.ini file"""

        # Update is possible only after initialization
        if not self.__ini_ok:
            return

        if not self._read_ini(ini_file):
            return

        if self.__MARGO_ok:
            self._make_MARGO()

        if self.__JSON_ok:
            self._make_JSON()

    @property
    def MARGO(self) -> MargoControls | None:
        """Get MARGO properties."""
        return self.__MARGO if self.__MARGO_ok else None

    @property
    def JSON(self) -> JSONControls | None:
        """Get JSON properties."""
        return self.__JSON if self.__JSON_ok else None

    @property
    def boxed_controls(self) -> BoxWithConverterControls | None:
        """Get Converter properties."""
        if self.__JSON_ok and self.__MARGO_ok:
            return BoxWithConverterControls(self.__MARGO, self.__JSON)
        else:
            return None
