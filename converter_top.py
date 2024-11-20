"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com
"""

"""
This module implements upper level of RTCM converter hierarchy.
Use factory class ConverterFactory() to create a new item of converter.
Use abstract class ConverterInterface() to access converter methods.
Use class BoxWithDecoderControls() to provide control parameters to converter.

Converter is a combination of two items: RTCM decoder (class DecoderTop()) and
printer (class PrinterTop()).

Decoder is responsible for:
- Extraction of RTCM messages from bytes flow.
- Parsing of RTCM messages, extraction of primary data fields.
- Conversion of primary data fields into DTO classes with predefined structure -
intermediate data types.
An instance of DecoderTop() defines decoder interface and aggregates several sub-decoder
instances. Sub-decoders are responsible for processing of different subsets of RTCM messages.

Printer is responsible for:
- Processing of intermediate data types (formatting and saving to file, etc.)
- Control over system resources being used for 'printing'.
An instance of PrinterTop() defines printer interface and aggregates several subprinters.
Sub-printers are responsible for processing of different subsets of intermediate data types
and generation of different output formats.

A combination of sub-printers and sub-decoders defines properties of definite converter instance.
At the moment there are following converter types:
- 'MARGO'[^1] - converts data from MSM messages into textual CSV files.
- 'JSON'  - converts data from MSM messages into textual JSON files.
- 'JSON-B' - extracts bare (integer, not scaled) data from MSM messages and saves in JSON format.

How to extend converter functionality.
- Develope new intermediate data class if required. See data_types\observables.py to check existing
data types. Example, ephemerids.py may be created and populated with intermediate data classes for
ephemeris data.
- Develope new sub-decoder to:
-- support new subsets of RTCM messages.
-- provide new intermediate data classes instead of previously developed.
- Develope new sub-printer to:
-- print new intermediate data types as one of existing output formats;
-- print existing intermediate data types in new format.   
- Develope new strategy_xxx() function (see below). Strategy function instantiates new converter
as a set of sub-printers and sub-decoders.
- Register new strategy_xxx() function in ConverterFactory(). 

1. MARGO is a simple, textual, CSV-like format for GNSS observables representation. Developed by NTLab
company. See DOCs\PrintersAndDecoders.md for details.

"""

from dataclasses import dataclass
from abc import ABC, abstractmethod

from decoder_top import DecoderTop
from sub_decoders import SubdecoderMSM4567, SubdecoderMSM123, SubdecoderEph

from printer_top import PrinterTop
from printers import MSMtoMARGO as MargoPrinter
from printers import MSMtoJSON as JsonPrinter

from controls import BoxWithConverterControls

from logger import LOGGER_CF as logger



@dataclass
class ConverterStatistics:
    decoding_attempts: int = 0
    parsing_errors: int = 0
    decoding_errors: int = 0


class ConverterInterface(ABC):
    """Defines protocol for RTCM decoder instance."""

    @abstractmethod
    def parse_bytes(self, buf: bytes) -> list[bytes]:
        """Extract RTCM messages from input bytes"""
    
    @abstractmethod
    def decode(self, message: bytes) -> object:
        """Process RTCM message in accordance with instance rules."""
    
    @abstractmethod
    def print(self, rtcm_data: object) -> None:
        """Save 'rtcm_data' content in accordance with instance rules."""
    
    @abstractmethod
    def release(self) -> None:
        """Release converter resources if any."""
    
    @abstractmethod
    def get_statistics(self) -> ConverterStatistics:
        """Return structure with auxiliary information about conversion results."""


class Converter(ConverterInterface):

    def __init__(self) -> None:
        self.decoder = DecoderTop()
        self.printer = PrinterTop()
        
    def parse_bytes(self, buf:bytes) -> list[bytes]:
        return self.decoder.catch_message(buf)            

    def decode(self, message:bytes) -> object:
        return self.decoder.decode(message)

    def print(self, rtcm_data) -> None:
        self.printer.print(rtcm_data)

    def release(self) -> None:
        self.printer.close()       

    def get_statistics(self) -> ConverterStatistics:
        rv = ConverterStatistics()
        rv.decoding_attempts = self.decoder.dec_attempts
        rv.decoding_errors = self.decoder.dec_errors
        rv.parsing_errors = self.decoder.parse_errors
        return rv


def strategy_MSM17toMARGO(wfld: str, controls: BoxWithConverterControls) -> ConverterInterface|None:
    conv = Converter()
    # Implement and register decoders
    msm123 = SubdecoderMSM123(bare_data=False)
    msm4567 = SubdecoderMSM4567(bare_data=False)
    if not conv.decoder.register_decoder(msm4567.io): 
        return None
    if not conv.decoder.register_decoder(msm123.io):
        return None
    
    # Implement and register printers
    conv.printer.format = 'MARGO'
    msm_to_margo = MargoPrinter(wfld, controls.MARGO)
    if not conv.printer.add_subprinter(msm_to_margo.io):
        return None
    
    return conv

def strategy_MSM17_EPH_to_JSON(wfld: str, controls: BoxWithConverterControls) -> ConverterInterface|None:
    conv = Converter()
    # Implement and register decoders
    msm123 = SubdecoderMSM123(bare_data=False)
    msm4567 = SubdecoderMSM4567(bare_data=False)
    eph = SubdecoderEph(bare_data=False)
    if not conv.decoder.register_decoder(msm4567.io): 
        return None
    if not conv.decoder.register_decoder(msm123.io):
        return None
    if not conv.decoder.register_decoder(eph.io):
        return None
        
    # Implement and register printers
    conv.printer.format = 'JSON'
    msm_to_json = JsonPrinter(wfld,controls.JSON)
    if not conv.printer.add_subprinter(msm_to_json.io):
        return None
    
    return conv

def strategy_MSM17_EPH_to_JSON_BareData(wfld: str, controls: BoxWithConverterControls) -> ConverterInterface|None:
    conv = Converter()
    # Implement and register decoders
    msm123 = SubdecoderMSM123(bare_data=True)
    msm4567 = SubdecoderMSM4567(bare_data=True)
    eph = SubdecoderEph(bare_data=True)
    if not conv.decoder.register_decoder(msm4567.io): 
        return None
    if not conv.decoder.register_decoder(msm123.io):
        return None
    if not conv.decoder.register_decoder(eph.io):
        return None
    

    # Implement and register printers
    conv.printer.format = 'JSON'
    msm_to_json = JsonPrinter(wfld, controls.JSON)
    if not conv.printer.add_subprinter(msm_to_json.io):
        return None
    
    return conv    


class ConverterFactory():

    __FACTORY = {
        'MARGO': strategy_MSM17toMARGO,
        'JSON': strategy_MSM17_EPH_to_JSON,
        'JSON-B': strategy_MSM17_EPH_to_JSON_BareData
    }

    def __init__(self, format: str = 'MARGO') -> None:
        """Factory creating RTCM converter.
        Choose one of available formats: 'MARGO', 'JSON', 'JSON-B'.
        """
        self.__f = self.__FACTORY.get(format)
        if not self.__f:
            print(f"Unknown format {format}.")

    def __call__(self, wfld: str, controls: BoxWithConverterControls) -> ConverterInterface|None:
        
        return self.__f(wfld, controls) if self.__f else None

