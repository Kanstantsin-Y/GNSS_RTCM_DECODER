"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Functions/classes required for validation of MSM messages decoding.
"""

# pylint: disable = invalid-name, consider-iterating-dictionary, broad-exception-caught

import os
import csv
import glob
import json

from dataclasses import dataclass, field
from typing import Any

from gnss_types import DataClassMethods
from run_conversion import main as convert
from printers import PrintJSON as PJ


__all__ = ["test_msm_message"]


MSM_TEST_SCENARIO = {
    1077: (
        r"GPS",
        r"RTCM3_TEST_DATA\MSM7\msg1077.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1077-MARGO",
    ),
    1087: (
        r"GLN",
        r"RTCM3_TEST_DATA\MSM7\msg1087.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1087-MARGO",
    ),
    1097: (
        r"GAL",
        r"RTCM3_TEST_DATA\MSM7\msg1097.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1097-MARGO",
    ),
    1127: (
        r"BDS",
        r"RTCM3_TEST_DATA\MSM7\msg1127.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1127-MARGO",
    ),
    1137: (
        r"NAVIC",
        r"RTCM3_TEST_DATA\MSM7\msg1137.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1137-MARGO",
    ),
    1075: (
        r"GPS",
        r"RTCM3_TEST_DATA\MSM5\msg1075.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1075-MARGO",
    ),
    1085: (
        r"GLN",
        r"RTCM3_TEST_DATA\MSM5\msg1085.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1085-MARGO",
    ),
    1095: (
        r"GAL",
        r"RTCM3_TEST_DATA\MSM5\msg1095.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1095-MARGO",
    ),
    1125: (
        r"BDS",
        r"RTCM3_TEST_DATA\MSM5\msg1125.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1125-MARGO",
    ),
}

MSM_TEST_SCENARIO2 = {
    1075: (
        r"RTCM3_TEST_DATA\MSM5\msg1075.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1075-JSON\MSM5\GPS-MSM5-1075.json",
    ),
    1085: (
        r"RTCM3_TEST_DATA\MSM5\msg1085.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1085-JSON\MSM5\GLN-MSM5-1085.json",
    ),
    1095: (
        r"RTCM3_TEST_DATA\MSM5\msg1095.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1095-JSON\MSM5\GAL-MSM5-1095.json",
    ),
    1125: (
        r"RTCM3_TEST_DATA\MSM5\msg1125.rtcm3",
        r"RTCM3_TEST_DATA\MSM5\REF\msg1125-JSON\MSM5\BDS-MSM5-1125.json",
    ),
    1077: (
        r"RTCM3_TEST_DATA\MSM7\msg1077.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1077-JSON\MSM7\GPS-MSM7-1077.json",
    ),
    1087: (
        r"RTCM3_TEST_DATA\MSM7\msg1087.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1087-JSON\MSM7\GLN-MSM7-1087.json",
    ),
    1097: (
        r"RTCM3_TEST_DATA\MSM7\msg1097.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1097-JSON\MSM7\GAL-MSM7-1097.json",
    ),
    1127: (
        r"RTCM3_TEST_DATA\MSM7\msg1127.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1127-JSON\MSM7\BDS-MSM7-1127.json",
    ),
    1137: (
        r"RTCM3_TEST_DATA\MSM7\msg1137.rtcm3",
        r"RTCM3_TEST_DATA\MSM7\REF\msg1137-JSON\MSM7\NAVIC-MSM7-1137.json",
    ),
}


# ----------------------------------------------------------------------------
# Test MSM to MARGO conversion.


@dataclass
class Margo(DataClassMethods):
    """Container for observabes extracted from the MARGO folder."""

    L: list[tuple[int | float]] = field(default_factory=list)  # types: ignore
    C: list[tuple[int | float]] = field(default_factory=list)  # types: ignore
    S: list[tuple[int | float]] = field(default_factory=list)  # types: ignore
    D: list[tuple[int | float]] = field(default_factory=list)  # types: ignore
    T: list[tuple[int | float]] = field(default_factory=list)  # types: ignore
    A: list[tuple[int | float]] = field(default_factory=list)  # types: ignore


def csv_to_list_of_tuples(path: str) -> list[tuple[int | float | str,]]:
    """Read .csv file and convert it to a list of tuples."""

    obuf = []
    with open(path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for i, row in enumerate(reader):
            if i == 0:
                sats = tuple(int(sat, 10) for sat in row)
                obuf.append(sats)
            elif i == 1:
                frequencies = tuple(float(frq) for frq in row)
                obuf.append(frequencies)
            else:
                time = int(row.pop(0), 10)
                frequencies = tuple(float(frq) for frq in row)
                obuf.append(tuple([time]) + frequencies)

        return obuf


def extract_Margo(obs_dir: str) -> dict[str, Margo]:
    """Analyse MARGO folder and extract data from files"""

    # Check, weather f_arguments specifies directory.
    path = os.path.abspath(obs_dir)
    is_directory = (not os.path.isfile(path)) and os.path.isdir(path)
    assert is_directory, "specified path is not a directory."

    # scan directory for .obs files
    fpattern = ".".join(["*", "obs"])
    pattern = os.path.join(path, fpattern)
    # Find files matching pattern
    file_list = glob.glob(pattern)

    assert 0 != len(
        file_list
    ), f"There are no files matching {fpattern} in {path}."

    fnames = []
    for f in file_list:
        _, fname = os.path.split(f)
        fnames.append(fname)

    slots = set(f[2:4] for f in fnames)

    ret = {}
    for slot in slots:
        odict = {}
        for i, file_path in enumerate(file_list):
            if fnames[i][2:4] != slot:
                continue

            param = fnames[i][1]
            obs = csv_to_list_of_tuples(file_path)
            odict.update({param: obs})

        r = Margo(**odict)
        ret.update({slot: r})

    return ret


def make_opath_from(base_path: str) -> tuple[str, str]:
    """Utility function to acquire output products location."""
    mode = "MARGO"
    fpath, fname = os.path.split(base_path)
    fname, _ = os.path.splitext(fname)
    odir = "-".join([fname, mode])
    odir = os.path.join(fpath, odir)
    olog = os.path.join(odir, "-".join([fname, "log.txt"]))

    return odir, olog


def _test_msm_margo(msg_num: int) -> bool:
    """Convert test data and compare with the reference"""

    tscn = MSM_TEST_SCENARIO.get(msg_num)
    assert tscn is not None, f"No test scenario for message {msg_num}"

    (gnss, source_file, rdir) = tscn
    cargs = "-o MARGO" + " -i addons.ini " + source_file
    convert(cargs)

    odir, olog = make_opath_from(source_file)
    odir = os.path.join(odir, gnss)
    rdir = os.path.join(rdir, gnss)

    assert os.path.isdir(odir), "Output directory not found"
    assert os.path.isdir(rdir), "Reference directory not found"
    assert os.path.isfile(olog), "Output log file not found"

    conv_result = extract_Margo(odir)
    conv_reference = extract_Margo(rdir)

    assert (
        conv_result.keys() == conv_reference.keys()
    ), "Unexpected/absent slots in the result."

    for slot, obs in conv_result.items():
        if isinstance(obs, DataClassMethods):
            assert obs.compare(
                conv_reference[slot], 1e-15
            ), f"Product {slot} is not equal to reference."

    return True


# ----------------------------------------------------------------------------
# Test MSM to JSON conversion.


@dataclass
class Observables(DataClassMethods):
    """DTO object storing range measurements."""

    obs: dict[str, Any] = field(default_factory=dict)  # types: ignore
    hdr: dict[str, Any] = field(default_factory=dict)  # types: ignore
    aux: dict[str, Any] = field(default_factory=dict)  # types: ignore


def _json_to_Observables(file: str) -> list[Observables]:
    """Read and convert .json file to Observables list."""

    rvalues = []

    with open(file, "r", encoding="utf-8") as f:
        observabeles: list[dict[str, Any],] = json.load(f)

    observabeles.pop(0)

    for obs in observabeles:
        _, v = obs.popitem()
        rv = Observables(**v)
        rvalues.append(rv)

    return rvalues


def _test_msm_json(msg_num: int) -> bool:
    """Convert test data and compare with the reference"""

    tscn = MSM_TEST_SCENARIO2.get(msg_num)
    assert tscn is not None, f"No test scenario for message {msg_num}"

    (src, rfile) = tscn
    cargs = "-o JSON " + src

    convert(cargs)

    ofile, *_ = PJ.make_opath(src, msg_num, "JSON")
    assert os.path.isfile(ofile), "Output file not found."
    assert os.path.isfile(rfile), "Reference file not found."

    observables = _json_to_Observables(ofile)
    ref_values = _json_to_Observables(rfile)

    assert len(observables) == len(
        ref_values
    ), f"Unexpected number of output products: {len(observables)}."

    for i, _ in enumerate(observables):
        if isinstance(observables[i], DataClassMethods):
            assert observables[i].compare(
                ref_values[i], 1e-15
            ), f"Product {i} is not equal to reference."

    return True


# ----------------------------------------------------------------------------
# Test MSM messaage.


def test_msm_message(msgNum: int, mode: str) -> bool:
    """Test single MSM message."""

    print("-" * 80)
    print(f"TESTER: start conversion MSG{msgNum} to {mode}.")

    ret = False

    if not mode in ("MARGO", "JSON"):
        print(f"TESTER: format {mode} is not supported in this test")
        return ret

    try:
        if mode == "MARGO":
            ret = _test_msm_margo(msgNum)
        else:
            ret = _test_msm_json(msgNum)
        print("TESTER: status SUCCEED.")
    except AssertionError as asrt:
        print(f"TESTER: status FAILED. {asrt.args[0]}")
    except Exception:
        print("TESTER: status FAILED. Unexpected error")

    return ret
