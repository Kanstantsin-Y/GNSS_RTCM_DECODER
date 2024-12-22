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

# pylint: disable = invalid-name, consider-iterating-dictionary, fixme

# --- Dependencies ---------------------------------------------------------------------------

from gnss_types import *  # pylint: disable = unused-wildcard-import,wildcard-import
from logger import LOGGER_CF as logger

# --- Specification of input data types for different printers -------------------------------

_MARGO_SPECS = {
    "LEGO": set(),
    "MSM13O": {
        ObservablesMSM,
    },
    "MSM47O": {
        ObservablesMSM,
    },
    "EPH": set(),
    "BASE": set(),
}

_JSON_SPECS = {
    "LEGO": set(),  # to be fulfilled with valid data types when developed
    "MSM13O": {BareObservablesMSM123, ObservablesMSM},
    "MSM47O": {BareObservablesMSM4567, ObservablesMSM},
    "EPH": {EphGPS, EphGLO, EphBDS, EphGALF, EphGALI, EphNAVIC, EphQZS},
    "BASE": {
        BaseRP,
        BaseRPH,
        BaseAD,
        BaseADSN,
        BaseADSNRC,
        BaseSP,
        BaseTS,
        BaseGLBS,
    },
}

_JARGO_SPECS = {
    "LEGO": set(),
    "MSM13O": {},
    "MSM47O": {},
    "EPH": {EphGPS, EphGLO, EphBDS, EphGALF, EphGALI, EphNAVIC, EphQZS},
    "BASE": {
        BaseRP,
        BaseRPH,
        BaseAD,
        BaseADSN,
        BaseADSNRC,
        BaseSP,
        BaseTS,
        BaseGLBS,
    },
}


_SPECS_LIST = {
    "MARGO": _MARGO_SPECS,
    "JSON": _JSON_SPECS,
    "JARGO": _JARGO_SPECS,
}


class SubPrinterInterface:
    """Implements common interface for different components of printer.

    Each instance of sub-printer must implement an instance of
    'SubPrinterInterface' named 'io'.
    'io' defines:
        1. Required range of data classes to be processed (printed) - 'data_spec'.
        3. Set of data classes being actually implemented 'actual_spec'.
        3. Virtual method 'print' which must be redefined in sub-printer implementation.
        4. Virtual method 'close' which must be redefined in sub-printer implementation.
           'close' used to finalize sub-printer work properly.
    """

    def __init__(self) -> None:

        self.format = "UNDEF"
        self.print = self.stub_print
        self.close = self.stub_close
        self.data_spec = set()
        self.actual_spec = set()

    @staticmethod
    def make_specs(oformat) -> set[type,]:
        """Return set of required data types to be supported"""

        rv = set()
        specs = _SPECS_LIST.get(oformat)
        if specs is not None:
            type_iterator = (
                dtype for dtypes in specs.values() for dtype in dtypes
            )
            rv = set(type_iterator)
        else:
            assert False, "Undefined printing format."

        return rv

    @staticmethod
    def stub_print(iblock: object) -> None:
        """Stub for virtual method .print(x)."""
        raise NotImplementedError("Virtual method .print() not defined")

    @staticmethod
    def stub_close() -> None:
        """Stub for virtual method .close()."""
        raise NotImplementedError("Virtual method .close() not defined")


def catch_printer_asserts(func):
    """Decorator. Implements processing of asserts raised in MARGO printer"""

    def catch_assert_wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except AssertionError as ae:
            logger.error(f"{ae.args[0]}")

    return catch_assert_wrapper


class PrinterTop:
    """Combines printers for RTCM message subsets and implements outer interface"""

    def __init__(self, in_format: str = "UNDEF") -> None:

        self._format = in_format
        self.printers: set[SubPrinterInterface] = set()
        self.__attempts_cnt = 0
        self.__succeeded_cnt = 0

    @property
    def format(self):
        """Get printer's output format"""
        return self._format

    @format.setter
    def format(self, in_format: str):
        """Set printer's output format"""

        if not in_format in _SPECS_LIST.keys():
            logger.error(f"Format '{in_format}' not supported.")
            self._format = ""
        else:
            self._format = in_format

    @property
    def exist(self):
        """Check, whether the printer has been initialized."""
        return (self.format != "") and (self.format != "UNDEF")

    @property
    def ready(self):
        """Check, whether the printer has been initialized."""
        return self.exist and len(self.printers) != 0

    @property
    def attempts(self):
        """Get the number of print attempts."""
        return self.__attempts_cnt

    @property
    def succeeded(self):
        """Get the number of successful print attempts."""
        return self.__succeeded_cnt

    @property
    def errors(self):
        """Get the number of print failures."""
        return self.__attempts_cnt - self.__succeeded_cnt

    def add_subprinter(self, io: SubPrinterInterface) -> bool:
        """
        Register new subset of data types for printing.
        Return True if registered successfully else False
        """
        rv = False
        if not self.exist:
            logger.error("Top Printer doesn't exist. Impossible to register")
            return rv

        if not isinstance(io, SubPrinterInterface):
            logger.error(
                f"Registered object is not 'SubPrinterInterface': {type(io)}"
            )
            return rv

        # if io.format != self.format:
        #     logger.error(f"Alien sub-printer {io.format}")
        #     return rv

        if io.print == SubPrinterInterface.stub_print:
            logger.error(f"Virtual method 'print' not defined in {type(io)}")
            return rv

        if io.close == SubPrinterInterface.stub_close:
            logger.error(f"Virtual method 'close' not defined in {type(io)}")
            return rv

        if 0 == len(io.actual_spec):
            logger.error(
                f"Empty d-blocks list. Update or delete subprinter {type(io)}"
            )
            return rv

        self.printers.add(io)
        return True

    @catch_printer_asserts
    def print(self, dblock: object):
        """Print input data block"""
        tp = type(dblock)
        # Find printer
        for printer in self.printers:
            if (tp in printer.data_spec) and (tp in printer.actual_spec):
                self.__attempts_cnt += 1
                printer.print(dblock)
                self.__succeeded_cnt += 1
                break
        else:
            logger.warning(f"Printer not found, d-block {tp}")

    def close(self):
        """Finalize subprinters"""

        for p in self.printers:
            p.close()
