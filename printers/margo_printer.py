"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    There are 3 classes here:
    1. MSMtoMARGO() - top level. Receives DTO objects with observables at the input and
    saves them into MARGO files. Implements sub-decoder interface.
    2. MargoCore() - utility methods.
    3. MargoControls() - DTO for control parameters.
"""

# pylint: disable = invalid-name, unused-import, consider-iterating-dictionary

import io
import os

from printer_top import SubPrinterInterface
from gnss_types import ObservablesMSM, BareObservablesMSM4567
from utilities import MSMT

from logger import LOGGER_CF as logger


class MargoControls:
    """Defines some parameters to control MARGO performance"""

    __slots__ = (
        "half_cycle_enable",
        "lock_time_enable",
        "gps_utc_shift",
        "glo_lit_tab",
    )

    def __init__(self) -> None:
        self.half_cycle_enable = False
        self.lock_time_enable = False
        self.gps_utc_shift = 18
        self.glo_lit_tab = {
            1: 1,
            2: -4,
            3: 5,
            4: 6,
            5: 1,
            6: -4,
            7: 5,
            8: 6,
            9: -2,
            10: -7,
            11: 0,
            12: -1,
            13: -2,
            14: -7,
            15: 0,
            16: -1,
            17: 4,
            18: -3,
            19: 3,
            20: 2,
            21: 4,
            22: -3,
            23: 3,
            24: 2,
        }


class MargoCore:
    """Utility methods of MARGO converter"""

    _DEFAULT_CONTROLS = MargoControls()

    def __init__(self, ctrl: MargoControls) -> None:
        self.ctrl = ctrl if ctrl is not None else self._DEFAULT_CONTROLS

    @property
    def literals(self):
        """Get GLONASS literals."""
        return self.ctrl.glo_lit_tab

    @property
    def utc_shift(self):
        """Get UTC shift."""
        return self.ctrl.gps_utc_shift

    @property
    def HC_EN(self):
        """Return True if Half Cycle Correction info is available."""
        return self.ctrl.half_cycle_enable

    @property
    def LT_EN(self):
        """Return True if Lock Time info is available."""
        return self.ctrl.lock_time_enable

    # Defines supported GNSS systems and appropriate output folders
    __OFILE_LT1 = {
        "G": "GPS",
        "R": "GLN",
        "E": "GAL",
        "S": "SBS",
        "Q": "QZS",
        "B": "BDS",
        "I": "NAVIC",
    }

    @classmethod
    def DIRNAME(cls, gnss):
        """Make MARGO directory name."""
        rv = cls.__OFILE_LT1.get(gnss)
        assert rv is not None, f"GNSS {gnss} not supported by DIRNAME()."
        return rv

    @classmethod
    def GNSSTUPLE(cls):
        """Return tuple ("GNSS Literal", "Message Subset")"""
        return cls.__OFILE_LT1.keys()

    # Controls total width and fractional part width in representation of observables.
    __FORMAT_COLUMNS = {
        "C": (15, 3),
        "L": (15, 4),
        "D": (15, 3),
        "S": (15, 2),
        "T": (10, 3),
        "A": (4, 0),
    }

    # Encodes file type in accordance with MARGO spec.
    __MARGO_FILE_ID = {"C": 0, "L": 1, "D": 2, "S": 3, "T": 4, "A": 5}

    # Defines max. number of sats for each constellation (number of columns in .obs file)
    __MAX_SATS = {"G": 32, "R": 24, "E": 36, "S": 38, "Q": 5, "B": 37, "I": 14}

    @classmethod
    def FORMAT(cls, parameter):
        """Return tuple with column formatting data."""
        rv = cls.__FORMAT_COLUMNS.get(parameter)
        assert (
            rv is not None
        ), f"parameter {parameter} not supported by FORMAT()."
        return rv

    @classmethod
    def MARGO_FILE_ID(cls, parameter):
        """Return first letter of file name."""
        rv = cls.__MARGO_FILE_ID.get(parameter)
        assert (
            rv is not None
        ), f"Parameter {parameter} not supported by MARGO_FILE_ID()."
        return rv

    @classmethod
    def MAX_SATS(cls, gnss):
        """Get the number of satellites in the GNSS constellation."""
        rv = cls.__MAX_SATS.get(gnss)
        assert rv is not None, f"GNSS {gnss} not supported by MAX_SATS()."
        return rv

    @classmethod
    def make_obs_file_name(cls, gnss, param, sgn, postf):
        """
        Compose file name to write parameter 'param' of signal 'sgn' of GNSS 'gnss'.
        'postf' may be any 0..5 characters string.
        Check input arguments. Return '' if any input argument is incorrect.
        Else - return file name.
        """
        rv = ""
        if not gnss in cls.GNSSTUPLE():
            return rv
        if len(sgn) != 2 or len(param) != 1:
            return rv
        if len(postf) > 5:
            postf = postf[0:5]
        rv = gnss + param + sgn + "_" + postf + ".obs"
        return rv

    @classmethod
    def conv_to_gps_time(
        cls, time: int, day: int, utc_shift: int, src_gnss: str
    ):
        """Convert any time to GPS time."""

        if src_gnss == "B":
            rv = time + 14000
            return rv - 604800000 if (rv >= 604800000) else rv
        elif src_gnss == "R":
            rv = time + day * 86400000 - (10800 - utc_shift) * 1000
            return rv + 604800000 if rv < 0 else rv
        else:
            return time

    def make_crr_frq(self, gnss, sgn) -> tuple[float, ...]:
        """Create tuple of carrier frequencies for all sats of given GNSS and signal, [MHz]"""
        frq = (MSMT.crr_frq(gnss, sgn),) * self.MAX_SATS(gnss)
        if gnss != "R":
            return frq
        if sgn not in ("1C", "1P", "2C", "2P"):
            return frq

        df = 0.5625 if sgn in ("1C", "1P") else 0.4375
        LT = self.literals
        frq = tuple((fc + df * LT[sat]) for sat, fc in enumerate(frq, start=1))
        return frq

    def make_lambdas(self, gnss, sgn) -> tuple[float, ...]:
        """Create dict of carrier wave lengths for all sats of a given GNSS and signal, [m]
        There will be equal values in a tuple for all sats for all GNSS except Glonass
        """
        frequencies = self.make_crr_frq(gnss, sgn)  # [MHz]
        lm = ((MSMT.CRNG_1MS * 1e-3) / f for f in frequencies)
        return tuple(lm)

    def ObservablesMSMtoPrintBuffer(
        self, pdata: ObservablesMSM
    ) -> dict[str, list[int | float | str]]:
        """
        Return a dictionary of the form {'file_name':'string of observables'}.
        Return empty dictionary if 'pdata' is empty or inconsistent.
        """

        rv = dict()
        gnss = pdata.atr.gnss

        assert (
            gnss in self.GNSSTUPLE()
        ), f"Got {gnss=} in ObservablesMSM. Not supported"

        if gnss != "G":
            time = self.conv_to_gps_time(
                pdata.hdr.time, pdata.hdr.day, self.utc_shift, gnss
            )
        else:
            time = pdata.hdr.time

        max_sats = self.MAX_SATS(gnss)
        pattern: list[int | str | float] = [time]

        # Code range observables
        for slot, obs in pdata.obs.rng.items():
            fn = self.make_obs_file_name(gnss, "C", slot, pdata.atr.subset)
            if fn == "":
                continue

            values = pattern[:]
            for sat in range(1, max_sats + 1):
                value = obs[sat] if sat in obs.keys() else "NaN"
                values.append(value)

            rv.update({fn: values})

        # Carrier phase observables
        for slot, obs in pdata.obs.phs.items():
            fn = self.make_obs_file_name(gnss, "L", slot, pdata.atr.subset)
            if fn == "":
                continue
            values = pattern[:]
            lam = self.make_lambdas(gnss, slot)
            for sat in range(1, max_sats + 1):

                if not sat in obs.keys():
                    values.append("NaN")
                    continue

                # Mesaurement available.
                # Is ambiguity allowed?
                if self.HC_EN:
                    amb_ok = True
                # check hca indicator if not allowed
                elif slot in pdata.obs.hca.keys():
                    # .hca not empty - extract indicator
                    if sat in pdata.obs.hca[slot].keys():
                        # Is ambiguity absent?
                        amb_ok = not pdata.obs.hca[slot][sat]
                    else:
                        # No data about ambiguity, unexpected condition.
                        amb_ok = False
                else:
                    # hca is absent, amb. supposed to be resolved
                    amb_ok = True

                value = obs[sat] / lam[sat - 1] if amb_ok else "NaN"
                values.append(value)

            rv.update({fn: values})

        # Doppler measurements
        for slot, obs in pdata.obs.dpl.items():
            fn = self.make_obs_file_name(gnss, "D", slot, pdata.atr.subset)
            if fn == "":
                continue

            values = pattern[:]
            lam = self.make_lambdas(gnss, slot)
            for sat in range(1, max_sats + 1):
                value = -obs[sat] / lam[sat - 1] if sat in obs.keys() else "NaN"
                values.append(value)

            rv.update({fn: values})

        # Carrier-to-noise ratio
        for slot, obs in pdata.obs.c2n.items():
            fn = self.make_obs_file_name(gnss, "S", slot, pdata.atr.subset)
            if fn == "":
                continue

            values = pattern[:]
            for sat in range(1, max_sats + 1):
                value = obs[sat] if sat in obs.keys() else "NaN"
                values.append(value)

            rv.update({fn: values})

        # Lock time
        if self.LT_EN:
            for slot, obs in pdata.obs.ltm.items():
                fn = self.make_obs_file_name(gnss, "T", slot, pdata.atr.subset)
                if fn == "":
                    continue

                values = pattern[:]
                for sat in range(1, max_sats + 1):
                    value = obs[sat] * 0.001 if sat in obs.keys() else "NaN"
                    values.append(value)

                rv.update({fn: values})

        # Half cycle ambiguity indicator
        if self.HC_EN:
            for slot, obs in pdata.obs.hca.items():
                fn = self.make_obs_file_name(gnss, "A", slot, pdata.atr.subset)
                if fn == "":
                    continue

                values = pattern[:]
                for sat in range(1, max_sats + 1):
                    if sat in obs.keys():
                        value = 1.0 if obs[sat] else 0.0
                    else:
                        value = "NaN"
                    values.append(value)

                rv.update({fn: values})

        return rv

    @staticmethod
    def format_obs_string(obs: list, width: int = 15, frc: int = 3):
        """Converts list of observables into MARGO-string"""
        g = (x for x in obs)
        # Time - integer field
        time_str = f"{next(g):10d},"
        # Observables
        obs_str = ",".join([f"{float(x):{width}.{frc}f}" for x in g])

        rv = time_str + obs_str + "\n"
        return rv

    def make_header(self, ofile_name: str):
        """Generate two string of a header for MARGO file"""
        gnss = ofile_name[0]
        param = ofile_name[1]
        width, frc = self.FORMAT(param)

        line1 = (sat + 1 for sat in range(self.MAX_SATS(gnss)))
        line1 = ",".join([f"{x:{width}d}" for x in line1])
        line1 = ",".join([f"{self.MARGO_FILE_ID(param):10d}", line1]) + "\n"

        # Set minimal width to represent frequencies correctly
        width = 9 if width < 9 else width
        frc = 4 if frc < 4 else frc

        sgn = ofile_name[2:4]
        frequencies = self.make_crr_frq(gnss, sgn)
        cf = MSMT.crr_frq(gnss, sgn)
        line2 = ",".join([f"{float(x):{width}.{frc}f}" for x in frequencies])
        line2 = ",".join([f"{float(cf):{10}.{frc}f}", line2]) + "\n"

        return line1, line2


class PrintMARGO:
    """Provides methods to print RTCM data in MARGO format."""

    def __init__(
        self, work_dir: str, ctrls: MargoControls, mode: str = "MARGO"
    ):

        assert os.path.isdir(work_dir), f"Output directory {work_dir} not found"

        self.core = MargoCore(ctrls)
        self.__wd = work_dir
        # Create an empty dictionary of opened files
        # Members should have 'file_name':file_descriptor form
        self.__ofiles: dict[str, io.TextIOWrapper] = {}

        self.io = SubPrinterInterface()
        self.io.data_spec = SubPrinterInterface.make_specs(mode)
        self.io.actual_spec = {ObservablesMSM}  # shall match self.__print()
        self.io.print = self.__print
        self.io.close = self.__close
        self.io.format = mode

    def __close(self):
        """Close all opened files"""
        if len(self.__ofiles):
            for itm in self.__ofiles.values():
                if isinstance(itm, io.TextIOWrapper):
                    itm.close()
        self.__ofiles = {}

    def __create_ofile(self, oname: str) -> bool:
        """Create new MARGO file and fill header"""

        path = os.path.join(self.__wd, self.core.DIRNAME(oname[0]))

        try:
            if not os.path.isdir(path):
                os.makedirs(path)
            path = os.path.join(path, oname)
            self.__ofiles[oname] = open(path, "w", encoding="utf-8")
            return True
        except OSError as oe:
            logger.error(f"Failed to create target file '{path}'.")
            logger.error(f"{type(oe)}: {oe}")
            return False

    def __append(self, ofile: str, line: str) -> bool:
        """Append a new row of observables to the file.
        If file doesn't exist, create new file and fill header, then append"""
        if ofile not in self.__ofiles.keys():
            if self.__create_ofile(ofile):
                h1, h2 = self.core.make_header(ofile)
                self.__ofiles[ofile].write(h1)
                self.__ofiles[ofile].write(h2)
            else:
                return False

        self.__ofiles[ofile].write(line)
        return True

    def __print_ObservablesMSM(self, obs: ObservablesMSM):
        """Print data from ObservablesMSM data block"""
        # Make raw-of-values for each parameter to be printed
        pbuf = self.core.ObservablesMSMtoPrintBuffer(obs)

        if not pbuf:
            return

        for f, observables in pbuf.items():
            ptype = f[1]  # C, L, D, S,...
            # Make textual representation of values
            column_format = self.core.FORMAT(ptype)
            obs_string = self.core.format_obs_string(
                observables, *column_format
            )
            self.__append(f, obs_string)

    # def __print_BareObservablesMSM4567(self, obs: BareObservablesMSM4567):
    #     pass

    def __print(self, iblock: object):
        """Margo printer"""

        assert isinstance(
            iblock, tuple(self.io.actual_spec)
        ), f"Printer does not support {type(iblock)}"

        if isinstance(iblock, ObservablesMSM):
            self.__print_ObservablesMSM(iblock)
        else:
            assert False, f"Printer does not support {type(iblock)}"
