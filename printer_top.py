
"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements classes:
    1. PrinterTop(). Aggregates sub-printers, finds and calls appropriate printing method
        for input DTO object.
    2. SubPrinterInterface(). 
        2.1 Specifies available sub-printers.
        2.2 Specifies list of DTO classes to be supported by each sub-printer.
        2.3 Defines virtual methods and attributes which should be implemented in sub-printer.
"""

#--- Dependencies ---------------------------------------------------------------------------

import data_types.ephemerids as mEph

from typing import Any
from data_types.observables import ObservablesMSM, BareObservablesMSM4567, BareObservablesMSM123
from logger import LOGGER_CF as logger

#--- Specification of input data types for different printers -------------------------------

_MARGO_SPECS = {
    'LEGO'  : set(),    # to be fulfilled with valid data types when developed
    'MSM13O': {ObservablesMSM,},
    'MSM47O': {ObservablesMSM,},
    'EPH'   : {mEph.GpsLNAV, mEph.GloL1L2, mEph.BdsD1, mEph.GalFNAV, mEph.GalINAV, mEph.NavicL5, mEph.QzssL1}
    }

_JSON_SPECS = {
    'LEGO'  : set(),    # to be fulfilled with valid data types when developed
    'MSM13O': {BareObservablesMSM123, ObservablesMSM},
    'MSM47O': {BareObservablesMSM4567, ObservablesMSM},
    'EPH'   : {mEph.GpsLNAV, mEph.GloL1L2, mEph.BdsD1, mEph.GalFNAV, mEph.GalINAV, mEph.NavicL5, mEph.QzssL1}
    }

_SPECS_LIST = {
    'MARGO': _MARGO_SPECS,
    'JSON' : _JSON_SPECS
}


class SubPrinterInterface():
    ''' Implements common interface for different components of printer.
    
        Each instance of sub-printer must implement an instance of
        'SubPrinterInterface' named 'io'.
        'io' defines:
            1. Required range of data classes to be processed (printed) - 'data_spec'.
            3. Set of data classes being actually implemented 'actual_spec'.
            3. Virtual method 'print' which must be redefined in sub-printer implementation.
            4. Virtual method 'close' which must be redefined in sub-printer implementation.
               'close' used to finalize sub-printer work properly. 
    '''

    def __init__(self) -> None:

        self.format = 'UNDEF'
        self.print = self.stub
        self.close = self.stub
        self.data_spec = set()
        self.actual_spec = set()
    
    @staticmethod
    def make_specs(format) -> set:
        '''Return set of required data types to be supported'''
        assert format in _SPECS_LIST.keys(), f"Undefined printing format."
        specs = _SPECS_LIST.get(format)
        rv = (dtype for dtypes in specs.values() for dtype in dtypes)
        rv = set(rv)
        return rv

    @staticmethod
    def stub():
        '''Stub for virtual methods'''
        raise NotImplementedError(f"Virtual method not defined")


def catch_printer_asserts(func):
    """Decorator. Implements processing of asserts sourced from MARGO printer"""
    def catch_assert_wrapper(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        except AssertionError as ae:
            logger.error(f"MARGOPRNT. {ae.args[0]}")
            return None
        else:
            return rv
            
    return catch_assert_wrapper


class PrinterTop():
    '''Combines decoders for RTCM message subsets and implements outer interface'''

    def __init__(self, in_format:str='UNDEF') -> None:

        # if len(format) and (not (format in _SPECS_LIST.keys())):
        #     logger.error(f"Format '{format}' not supported.")
        #     self._format = ''
        #     return

        self._format = in_format
        self.printers : set[SubPrinterInterface] = set()
        self.__attempts_cnt = 0
        self.__succeeded_cnt = 0

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, in_format:str):
        if not (in_format in _SPECS_LIST.keys()):
            logger.error(f"Format '{in_format}' not supported.")
            self._format = ''
        else:
            self._format = in_format

    @property
    def exist(self):
        return (self.format != '') and (self.format != 'UNDEF')

    @property
    def ready(self):
        return self.exist and len(self.printers) != 0

    @property
    def attempts(self):
        return self.__attempts_cnt

    @property
    def succeeded(self):
        return self.__succeeded_cnt

    def add_subprinter(self, io: SubPrinterInterface)->bool:
        '''
        Register new subset of data types for printing.
        Return True if registered successfully else False
        '''
        rv = False
        if not self.exist:
            logger.error(f"Top Printer doesn't exist. Impossible to register")
            return rv

        # Validate interface attributes
        # if not ('io' in new_printer.__dict__):
        #     logger.error(f"No 'io' instance in sub-decoder {type(new_printer)}")
        #     return rv

        if not isinstance(io, SubPrinterInterface): 
            logger.error(f"Registered object is not 'SubPrinterInterface': {type(io)}")
            return rv

        if (io.format != self.format):  
            logger.error(f'Alien sub-printer {io.format}')
            return rv

        if (io.print == SubPrinterInterface.stub):  
            logger.error(f"Virtual method 'print' not defined in {type(io)}")
            return rv
        
        if (io.close == SubPrinterInterface.stub):  
            logger.error(f"Virtual method 'close' not defined in {type(io)}")
            return rv

        if not len(io.actual_spec): 
            logger.error(f"Empty d-blocks list. Update or delete subprinter {type(io)}")
            return rv

        self.printers.add(io)
        return True


    @catch_printer_asserts
    def print(self, dblock: object):
        '''Print input data block'''
        tp = type(dblock)
        #Find printer
        for printer in self.printers:
            if (tp in printer.data_spec) and (tp in printer.actual_spec):
                self.__attempts_cnt += 1
                printer.print(dblock)
                self.__succeeded_cnt +=1
                break
        else:
            logger.warning(f"Printer not found, d-block {tp}")
        

    def close(self):
        '''Finalize subprinters'''

        for p in self.printers:
            p.close()


