"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    There are 3 classes here:
    1. PrintJSON() - top level. Receives DTO object with observables at the input and
    saves it's content into JSON files. Implements sub-decoder interface.
    2. JSONCore() - utility methods.
    3. JSONControls() - DTO for control parameters.
"""

# pylint: disable = invalid-name, unused-import, consider-iterating-dictionary

import io
import os
from dataclasses import asdict, is_dataclass
from json import dumps as jdumps
from printer_top import SubPrinterInterface
from gnss_types import *  # pylint: disable = wildcard-import, unused-wildcard-import

__OBS_M123 = {ObservablesMSM, BareObservablesMSM123}
__OBS_M4567 = {ObservablesMSM, BareObservablesMSM4567}


JSON_SPEC = {
    1071: ["GPS", "MSM1", __OBS_M123, "GPS-MSM1-1071.json"],
    1072: ["GPS", "MSM2", __OBS_M123, "GPS-MSM2-1072.json"],
    1073: ["GPS", "MSM3", __OBS_M123, "GPS-MSM3-1073.json"],
    1074: ["GPS", "MSM4", __OBS_M4567, "GPS-MSM4-1074.json"],
    1075: ["GPS", "MSM5", __OBS_M4567, "GPS-MSM5-1075.json"],
    1076: ["GPS", "MSM6", __OBS_M4567, "GPS-MSM6-1076.json"],
    1077: ["GPS", "MSM7", __OBS_M4567, "GPS-MSM7-1077.json"],
    1081: ["GLN", "MSM1", __OBS_M123, "GLN-MSM1-1081.json"],
    1082: ["GLN", "MSM2", __OBS_M123, "GLN-MSM2-1082.json"],
    1083: ["GLN", "MSM3", __OBS_M123, "GLN-MSM3-1083.json"],
    1084: ["GLN", "MSM4", __OBS_M4567, "GLN-MSM4-1084.json"],
    1085: ["GLN", "MSM5", __OBS_M4567, "GLN-MSM5-1085.json"],
    1086: ["GLN", "MSM6", __OBS_M4567, "GLN-MSM6-1086.json"],
    1087: ["GLN", "MSM7", __OBS_M4567, "GLN-MSM7-1087.json"],
    1091: ["GAL", "MSM1", __OBS_M123, "GAL-MSM1-1091.json"],
    1092: ["GAL", "MSM2", __OBS_M123, "GAL-MSM2-1092.json"],
    1093: ["GAL", "MSM3", __OBS_M123, "GAL-MSM3-1093.json"],
    1094: ["GAL", "MSM4", __OBS_M4567, "GAL-MSM4-1094.json"],
    1095: ["GAL", "MSM5", __OBS_M4567, "GAL-MSM5-1095.json"],
    1096: ["GAL", "MSM6", __OBS_M4567, "GAL-MSM6-1096.json"],
    1097: ["GAL", "MSM7", __OBS_M4567, "GAL-MSM7-1097.json"],
    1101: ["SBS", "MSM1", __OBS_M123, "SBS-MSM1-1101.json"],
    1102: ["SBS", "MSM2", __OBS_M123, "SBS-MSM2-1102.json"],
    1103: ["SBS", "MSM3", __OBS_M123, "SBS-MSM3-1103.json"],
    1104: ["SBS", "MSM4", __OBS_M4567, "SBS-MSM4-1104.json"],
    1105: ["SBS", "MSM5", __OBS_M4567, "SBS-MSM5-1105.json"],
    1106: ["SBS", "MSM6", __OBS_M4567, "SBS-MSM6-1106.json"],
    1107: ["SBS", "MSM7", __OBS_M4567, "SBS-MSM7-1107.json"],
    1111: ["QZS", "MSM1", __OBS_M123, "QZS-MSM1-1111.json"],
    1112: ["QZS", "MSM2", __OBS_M123, "QZS-MSM2-1112.json"],
    1113: ["QZS", "MSM3", __OBS_M123, "QZS-MSM3-1113.json"],
    1114: ["QZS", "MSM4", __OBS_M4567, "QZS-MSM4-1114.json"],
    1115: ["QZS", "MSM5", __OBS_M4567, "QZS-MSM5-1115.json"],
    1116: ["QZS", "MSM6", __OBS_M4567, "QZS-MSM6-1116.json"],
    1117: ["QZS", "MSM7", __OBS_M4567, "QZS-MSM7-1117.json"],
    1121: ["BDS", "MSM1", __OBS_M123, "BDS-MSM1-1121.json"],
    1122: ["BDS", "MSM2", __OBS_M123, "BDS-MSM2-1122.json"],
    1123: ["BDS", "MSM3", __OBS_M123, "BDS-MSM3-1123.json"],
    1124: ["BDS", "MSM4", __OBS_M4567, "BDS-MSM4-1124.json"],
    1125: ["BDS", "MSM5", __OBS_M4567, "BDS-MSM5-1125.json"],
    1126: ["BDS", "MSM6", __OBS_M4567, "BDS-MSM6-1126.json"],
    1127: ["BDS", "MSM7", __OBS_M4567, "BDS-MSM7-1127.json"],
    1131: ["NAVIC", "MSM1", __OBS_M123, "NAVIC-MSM1-1131.json"],
    1132: ["NAVIC", "MSM2", __OBS_M123, "NAVIC-MSM2-1132.json"],
    1133: ["NAVIC", "MSM3", __OBS_M123, "NAVIC-MSM3-1133.json"],
    1134: ["NAVIC", "MSM4", __OBS_M4567, "NAVIC-MSM4-1134.json"],
    1135: ["NAVIC", "MSM5", __OBS_M4567, "NAVIC-MSM5-1135.json"],
    1136: ["NAVIC", "MSM6", __OBS_M4567, "NAVIC-MSM6-1136.json"],
    1137: ["NAVIC", "MSM7", __OBS_M4567, "NAVIC-MSM7-1137.json"],
    1019: ["GPS", "EPH", {EphGPS}, "GPS-EPH-1019.json"],
    1020: ["GLN", "EPH", {EphGLO}, "GLN-EPH-1020.json"],
    1041: ["NAVIC", "EPH", {EphNAVIC}, "NAVIC-EPH-1041.json"],
    1042: ["BDS", "EPH", {EphBDS}, "BDS-EPH-1042.json"],
    1044: ["QZS", "EPH", {EphQZS}, "QZS-EPH-1044.json"],
    1045: ["GAL", "EPH", {EphGALF}, "GAL-EPH-1045.json"],
    1046: ["GAL", "EPH", {EphGALI}, "GAL-EPH-1046.json"],
    1005: ["X", "BASE", {BaseRP}, "RefPoint-1005.json"],
    1006: ["X", "BASE", {BaseRPH}, "RefPointHeight-1006.json"],
    1007: ["X", "BASE", {BaseAD}, "AntDesc-1007.json"],
    1008: ["X", "BASE", {BaseADSN}, "AntDescSer-1008.json"],
    1013: ["X", "BASE", {BaseSP}, "SysPar-1013.json"],
    1029: ["X", "BASE", {BaseTS}, "TextStr-1029.json"],
    1033: ["X", "BASE", {BaseADSNRC}, "AntAndRcvDesc-1033.json"],
    1230: ["X", "BASE", {BaseGLBS}, "GloBias-1230.json"],
}


class JSONControls:
    """A DTO class for JSON printer controls."""

    __slots__ = ("enable_hdr_data", "enable_aux_data", "enable_pretty_view")

    def __init__(self) -> None:
        self.enable_hdr_data: bool = False
        self.enable_aux_data: bool = False
        self.enable_pretty_view: bool = False


class PrintJSON:
    """Provides functionality for printing RTCM data in JSON format."""

    def __init__(self, work_dir: str, controls: JSONControls | None = None):

        assert os.path.isdir(work_dir), f"Output directory {work_dir} not found"

        self.core = JSONCore(controls)
        self.__wd = work_dir
        self.__src_obj_type = type(object)
        # Create an empty dictionary of opened files
        # Members should have {message number:file_descriptor} form
        self.__ofiles: dict[int, io.TextIOWrapper] = {}

        self.io = SubPrinterInterface()
        self.io.data_spec = SubPrinterInterface.make_specs("JSON")

        self.io.actual_spec = set()
        for val in JSON_SPEC.values():
            self.io.actual_spec.update(val[2])

        self.io.print = self.__print
        self.io.close = self.__close
        self.io.format = "JSON"

    @staticmethod
    def make_opath(base: str, msgNum: int, mode: str) -> tuple[str, str, str]:
        """Utility function to acquire output products location.

        base: path to the source file to be converted.
        msgNum: message number supported by JSON converter, see spec above
        mode: conversion mode - 'JSON' or 'JSON-B'
        """

        fpath, fname = os.path.split(base)
        fname, ext = os.path.splitext(fname)  # pylint: disable = unused-variable
        odir = "-".join([fname, mode])
        odir = os.path.join(fpath, odir)
        olog = os.path.join(odir, "-".join([fname, "log.txt"]))
        atr = JSON_SPEC.get(msgNum)
        if atr is not None:
            ofile = os.path.join(odir, atr[1], atr[3])
        else:
            ofile = os.path.join(odir, "UNDEF", f"msg{msgNum}.json")

        return ofile, odir, olog

    def __close(self):
        """Close all opened files"""
        if len(self.__ofiles):
            for itm in self.__ofiles.values():
                if isinstance(itm, io.TextIOWrapper):
                    itm.write("\r]")
                    itm.close()
        self.__ofiles = {}

    def __create_ofile(self, msg_num: int):
        """Create new JSON file"""

        path = os.path.join(self.__wd, JSON_SPEC[msg_num][1])
        fname = JSON_SPEC[msg_num][3]

        try:
            if not os.path.isdir(path):
                os.makedirs(path)
            path = os.path.join(path, fname)
            self.__ofiles[msg_num] = open(path, "w", encoding="utf-8")
        except OSError as oe:
            raise AssertionError(
                f"Failed to create target file '{path}: " + f"{type(oe)}: {oe}"
            ) from oe

    def __append(self, msg_num: int, line: str):
        """Append a new row of observables to the file.
        If file doesn't exist, create new file, then append"""

        if msg_num not in self.__ofiles.keys():
            # open output file and add header line
            self.__create_ofile(msg_num)
            hdr = {"source_type": self.__src_obj_type.__name__}
            hdr = jdumps(hdr, indent=None)
            self.__ofiles[msg_num].write("[\r" + hdr)

        self.__ofiles[msg_num].write(line)

    # @catch_printer_asserts
    def __print(self, iblock: object):
        """JSON printer"""

        self.__src_obj_type = type(iblock)

        if isinstance(iblock, ObservablesMSM):
            data_string = self.core.ObservablesMSMtoPrintBuffer(iblock)
            msgNum = iblock.atr.msg_number
        elif isinstance(iblock, (BareObservablesMSM4567, BareObservablesMSM123)):
            data_string = self.core.BareObservablesMSMtoPrintBuffer(iblock)
            msgNum = iblock.atr.msg_number
        elif True is self.core.is_json_dataclass(iblock):
            data_string = self.core.dataClassToPrintBuffer(iblock)
            msgNum = getattr(iblock, "msgNum")
        else:
            raise AssertionError(f"JSON printer does not support {self.__src_obj_type}")

        assert (
            msgNum in JSON_SPEC.keys()
        ), f"JSON printer doesn't support msg {msgNum}. Arrived with {self.__src_obj_type}"

        data_string = ",\r" + data_string
        self.__append(msgNum, data_string)


class JSONCore:
    """Core utilities for JSON serialization"""

    def __init__(self, controls: JSONControls | None = None) -> None:
        if controls:
            self.ctrls = controls
        else:
            self.ctrls = JSONControls()

    def ObservablesMSMtoPrintBuffer(self, pdata: ObservablesMSM) -> str:
        """Return a JSON string encoding 'ObservablesMSM' data."""

        asStr = ""
        try:
            # Repack ObservablesMSM into a dictionary
            time = pdata.hdr.time + pdata.hdr.day * 86400000
            obs = {s: getattr(pdata.obs, s) for s in pdata.obs.__slots__}
            hdr = {s: getattr(pdata.hdr, s) for s in pdata.hdr.__slots__}
            aux = {s: getattr(pdata.aux, s) for s in pdata.aux.__slots__}

            summary = {}

            if self.ctrls.enable_hdr_data:
                summary.update({"hdr": hdr})

            if self.ctrls.enable_aux_data:
                summary.update({"aux": aux})

            summary.update({"obs": obs})

            # serialize to JSON string
            indent = 2 if self.ctrls.enable_pretty_view else None
            asStr = jdumps(
                {time: summary}, indent=indent, allow_nan=True, ensure_ascii=False
            )

        except AttributeError as ke:
            raise AssertionError(
                "'ObservablesMSM' wasn't converted to dict: " + f"{type(ke)}: {ke}"
            ) from ke
        except TypeError as te:
            raise AssertionError("JSON: can't serialize 'ObservablesMSM'") from te
        except Exception as ex:
            raise AssertionError(
                "JSON: unexpected error in ObservablesMSMtoPrintBuffer()"
            ) from ex

        return asStr

    def BareObservablesMSMtoPrintBuffer(
        self, pdata: BareObservablesMSM4567 | BareObservablesMSM123
    ) -> str:
        """Return a JSON string encoding 'BareObservables' data."""

        asStr = ""
        try:
            # Repack 'BareObservablesMSMxxx' into a dictionary
            time = pdata.time
            sat = {s: getattr(pdata.sat, s) for s in pdata.sat.__slots__}
            sgn = {s: getattr(pdata.sgn, s) for s in pdata.sgn.__slots__}
            hdr = {s: getattr(pdata.hdr, s) for s in pdata.hdr.__slots__}
            atr = {s: getattr(pdata.atr, s) for s in pdata.atr.__slots__}

            summary = dict()
            if self.ctrls.enable_hdr_data:
                summary.update({"hdr": hdr})
            if self.ctrls.enable_aux_data:
                summary.update({"aux": atr})

            summary.update({"sat": sat})
            summary.update({"sgn": sgn})

            # serialize to JSON string
            indent = 2 if self.ctrls.enable_pretty_view else None
            asStr = jdumps(
                {time: summary}, indent=indent, allow_nan=True, ensure_ascii=False
            )

        except AttributeError as ke:
            raise AssertionError(
                "'BareObservablesMSM' wasn't converted to dict:" + f"{type(ke)}: {ke}"
            ) from ke
        except TypeError as te:
            raise AssertionError("JSON: can't serialize 'BareObservablesMSM'") from te
        except Exception as ex:
            raise AssertionError(
                "JSON: unexpected error in BareObservablesMSMtoPrintBuffer()"
            ) from ex

        return asStr

    def is_json_dataclass(self, data: object) -> bool:
        """Validate minimal requirements to gnss data block"""

        return is_dataclass(data) and ("msgNum" in data.__dataclass_fields__.keys())

    def dataClassToPrintBuffer(self, pdata: object) -> str:
        """Return a JSON string encoding data class."""

        asStr = ""
        try:
            asDictionary = asdict(pdata)  # type: ignore
            indent = 2 if self.ctrls.enable_pretty_view else None
            asStr = jdumps(
                asDictionary, indent=indent, allow_nan=True, ensure_ascii=False
            )
        except TypeError as te:
            raise AssertionError(
                f"JSON: can't serialize {type(pdata)} dictionary"
            ) from te
        except Exception as ex:
            raise AssertionError(
                "JSON: unexpected error in BareObservablesMSMtoPrintBuffer()"
            ) from ex

        return asStr
