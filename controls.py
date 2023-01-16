

from configparser import ConfigParser
from margo_printer import MargoControls




class BoxWithDecoderControls():
    """Container for summary of decoder controls"""
    __slots__ = ['MARGO']
    
    def __init__(self) -> None:
        self.MARGO : MargoControls
        # Extend with other controls here:
        # ...


class DecoderControls():

    
    def __init__(self) -> None:
        self.__MARGO = MargoControls()
        self.__ini = ConfigParser()
        self.__ini_ok = False
        self.__MARGO_ok = False
    
    def _read_ini(self, ini_file:str)->bool:
        """Read *ini file. Return true if there is something in it."""
        self.__ini.read(ini_file)
        rv = len(self.__ini.sections()) != 0
        if not rv:
            print(f"INI file {ini_file} is corrupted or empty.")
        
        return rv

    def _make_MARGO(self)->bool:
        """Compose controls for MARGO printer"""
        if not self.__ini_ok:
            return False

        if 'LITERALS' not in self.__ini.sections():
            return False

        if 'TIME' not in self.__ini.sections():
            return False

        if 'MARGO' not in self.__ini.sections():
            return False

        lt = {}
        mask:int = 0

        keys = set(self.__ini['LITERALS'])
        # 'keys' collects garbage from 'DEFAULT'
        if 'DEFAULT' in self.__ini.sections():
            keys = keys - set(self.__ini['DEFAULT'])

        for key in keys:
            sat = int(key.strip('rR'))
            if 0 < sat <= 24:
                mask |= (1<<(sat-1))
                lt.update({sat: self.__ini['LITERALS'].getint(key)})
        
        res = MargoControls()

        if mask == 0xffffff:
            res.glo_lit_tab = lt
        else:
            return False

        res.gps_utc_shift = self.__ini['TIME'].getint('GPS2UTC')
        if res.gps_utc_shift == None:
            return False

        res.half_cycle_enable = self.__ini['MARGO'].getboolean('HCA')
        if res.half_cycle_enable == None:
            return False
        
        res.lock_time_enable = self.__ini['MARGO'].getboolean('LOCK_TIME')
        if res.lock_time_enable == None:
            return False
        
        self.__MARGO = res
        return True

    def init_from_file(self, ini_file:str):
        """Update controls from *.ini file"""
        self.__ini_ok = self._read_ini(ini_file)
        if self.__ini_ok:
            self.__MARGO_ok = self._make_MARGO()
    
    def update_from_file(self, ini_file:str):
        """Update controls from *.ini file"""
        # Update is possible only after initialization
        if not self.__ini_ok:
            return
        
        if not self._read_ini(ini_file):
            return
        
        if self.__MARGO_ok:
            self._make_MARGO()

    @property
    def MARGO(self)->MargoControls:
        return self.__MARGO if self.__MARGO_ok else None

    @property
    def boxed_controls(self):
        rv = BoxWithDecoderControls()
        rv.MARGO = self.MARGO
        return rv
