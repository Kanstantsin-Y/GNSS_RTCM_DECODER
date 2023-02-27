"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    There are 3 classes here:
    1. MSMtoJSON() - top level. Receives DTO object with observables at the input and
    saves it's content into JSON files. Implements sub-decoder interface.
    2. JSONCore() - utility methods.
    3. JSONControls() - DTO for control parameters.
"""


import  io, os

from printer_top import SubPrinterInterface
from data_types.observables import ObservablesMSM, BareObservablesMSM4567, BareObservablesMSM123
from utilities.RTCM_utilities import MSMT

from logger import LOGGER_CF as logger
from json import dumps as jdumps



class JSONControls:

    __slots__ = ('enable_hdr_data', 'enable_aux_data', 'enable_pretty_view')

    def __init__(self) -> None:
        self.enable_hdr_data: bool = False
        self.enable_aux_data: bool = False
        self.enable_pretty_view: bool = False


class JSONCore:
    """Core utilities for JSON serialization"""
    
    # Defines supported GNSS systems and appropriate output folders
    __GNSS_DIRS = {
            'G':'GPS',
            'R':'GLN',
            'E':'GAL',
            'S':'SBS',
            'Q':'QZS',
            'B':'BDS',
            'I':'NAVIC'
        }

    @classmethod
    def DIRNAME(cls, gnss):
        rv = cls.__GNSS_DIRS.get(gnss)
        assert rv != None, f"GNSS {gnss} not supported by FILENAME()."
        return rv
    
    def __init__(self, controls:JSONControls|None = None) -> None:
        if controls:
            self.ctrls = controls
        else:
            self.ctrls = JSONControls()
        
    def ObservablesMSMtoPrintBuffer(self, pdata:ObservablesMSM) -> str:
        """ Return a JSON string encoding 'ObservablesMSM' data."""
        
        # Repack ObservablesMSM into a dictionary

        time = pdata.hdr.time + pdata.hdr.day*86400000
        try:
            obs = {s:pdata.obs.__getattribute__(s) for s in pdata.obs.__slots__}
            hdr = {s:pdata.hdr.__getattribute__(s) for s in pdata.hdr.__slots__}
            aux = {s:pdata.aux.__getattribute__(s) for s in pdata.aux.__slots__}
        except AttributeError as ke:
            logger.error(f"'ObservablesMSM' wasn't converted to dict")
            logger.error(f"{type(ke)}: {ke}")
            return ""
        else:
            summary = dict()
            if self.ctrls.enable_hdr_data:
                summary.update({'hdr':hdr})
            if self.ctrls.enable_aux_data:
                summary.update({'aux':aux})
            summary.update({'obs':obs})
            
        try:
            indent = 2 if self.ctrls.enable_pretty_view else None
            rv = jdumps({time:summary}, indent=indent, allow_nan=True, ensure_ascii=False)
        except TypeError:
            logger.error(f"JSON: can't serialize 'ObservablesMSM'")
            return ""
        else:
            return rv

    def BareObservablesMSMtoPrintBuffer(self, pdata:BareObservablesMSM4567|BareObservablesMSM123) -> str:
        """ Return a JSON string encoding 'BareObservables' data."""
        
        # Repack 'BareObservablesMSM' into a dictionary

        time = pdata.time
        try:
            sat = {s:pdata.sat.__getattribute__(s) for s in pdata.sat.__slots__}
            sgn = {s:pdata.sgn.__getattribute__(s) for s in pdata.sgn.__slots__}
            hdr = {s:pdata.hdr.__getattribute__(s) for s in pdata.hdr.__slots__}
            atr = {s:pdata.atr.__getattribute__(s) for s in pdata.atr.__slots__}
        except AttributeError as ke:
            logger.error(f"'BareObservablesMSM' wasn't converted to dict")
            logger.error(f"{type(ke)}: {ke}")
            return ""
        else:
            summary = dict()
            if self.ctrls.enable_hdr_data:
                summary.update({'hdr':hdr})
            if self.ctrls.enable_aux_data:
                summary.update({'aux':atr})
            summary.update({'sat':sat})
            summary.update({'sgn':sgn})
            
        try:
            indent = 2 if self.ctrls.enable_pretty_view else None
            rv = jdumps({time:summary}, indent=indent, allow_nan=True, ensure_ascii=False)
        except TypeError:
            logger.error(f"JSON: can't serialize 'BareObservablesMSM'")
            return ""
        else:
            return rv


class MSMtoJSON():
    
    def __init__(self, work_dir: str, controls: JSONControls|None = None):
        
        assert (os.path.isdir(work_dir)), f"Output directory {work_dir} not found"
        
        self.core = JSONCore(controls)

        self._map_printers = {
            ObservablesMSM : self.__print_ObservablesMSM,
            BareObservablesMSM4567 : self.__print_BareObservablesMSM17,
            BareObservablesMSM123 : self.__print_BareObservablesMSM17,
        }
        
        self.__wd = work_dir
        self.__src_obj_type = None
        # Create an empty dictionary of opened files
        # Members should have 'file_name':file_descriptor form
        self.__ofiles: dict[str, io.TextIOWrapper] = {}
        
        self.io = SubPrinterInterface()
        self.io.data_spec = SubPrinterInterface.make_specs('JSON')
        self.io.actual_spec = set()
        self.io.actual_spec.update(self._map_printers.keys())
        self.io.print = self.__print
        self.io.close = self.__close
        self.io.format = 'JSON'
        
        return
    
    def __close(self):
        '''Close all opened files'''
        if len(self.__ofiles):
            for itm in self.__ofiles.values():
                if isinstance(itm, io.TextIOWrapper):
                    itm.write('\r]')
                    itm.close()
        self.__ofiles = {}

    def __create_ofile(self, msg_num:int)->bool:
        '''Create new MARGO file and fill header'''

        gnss, subset = MSMT.msm_subset(msg_num)

        if not len(gnss):
            return False

        path = os.path.join(self.__wd, self.core.DIRNAME(gnss)) 
        fname = f"{subset}.json"
        try:
            if not os.path.isdir(path):
                os.makedirs(path)
            path = os.path.join(path, fname)
            self.__ofiles[msg_num] = open(path,'w')
            return True
        except OSError as oe:
            logger.error(f"Failed to create target file '{path}'.")
            logger.error(f"{type(oe)}: {oe}")
            return False
        
    def __append(self, msg_num:int, line:str)->bool:
        '''Append a new row of observables to the file.
        If file doesn't exist, create new file, then append'''
        
        if msg_num not in self.__ofiles.keys():
            if not self.__create_ofile(msg_num):
                return False
            else:
                self.__ofiles[msg_num].write(f"[source_type : {self.__src_obj_type.__name__}")  

        self.__ofiles[msg_num].write(line)
        return True

    def __print_ObservablesMSM(self, obs:ObservablesMSM):
        '''Print data from ObservablesMSM data block'''
        
        data_string = self.core.ObservablesMSMtoPrintBuffer(obs)
        if len(data_string):
            data_string = ',\r' + data_string
            self.__append(obs.atr.msg_number, data_string)

    def __print_BareObservablesMSM17(self, obs:BareObservablesMSM4567|BareObservablesMSM123):
        '''Print data from BareObservablesMSM17 data block'''
        
        data_string = self.core.BareObservablesMSMtoPrintBuffer(obs)
        if len(data_string):
            data_string = ',\r' + data_string
            self.__append(obs.atr.msg_number, data_string)


    #@catch_printer_asserts
    def __print(self, iblock:object):
        '''Margo printer'''

        self.__src_obj_type = type(iblock)
        print_func = self._map_printers.get(self.__src_obj_type)
        if print_func:
            print_func(iblock)
        else:
            #Paranoid check. Issue should be caught at PrinterTop level.
            assert print_func, f"Printer does not support {self.__src_obj_type}"
