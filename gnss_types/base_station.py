"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    This file implements DTO classes for base station and antenna description data.
    It includes messages 1005, 1006, 1007, 1008, 1013, 1029, 1033, 1230
"""

# pylint: disable = invalid-name, too-many-instance-attributes

from dataclasses import dataclass, field
from .data_class_methods import DataClassMethods

__all__ = [
    "BaseRP",
    "BaseRPH",
    "BaseAD",
    "BaseADSN",
    "BaseSP",
    "BaseTS",
    "BaseADSNRC",
    "BaseGLBS",
    "BaseSPitem",
]


@dataclass
class BaseRP(DataClassMethods):
    """DTO object for base station position and properties, msg 1005"""

    msgNum: int = 0  # DF002
    bsID: int = 0  # DF003
    ITRF_Year: int = 0  # DF021
    GPS_OK: int | bool = 0  # DF022
    GLO_OK: int | bool = 0  # DF023
    GAL_OK: int | bool = 0  # DF024
    isVirtual: int | bool = 0  # DF141
    refPoint_X: int | float = 0  # DF025
    singleOsc: int | bool = 0  # DF142
    refPoint_Y: int | float = 0  # DF026
    QC_bias: int | str = 0  # DF364
    refPoint_Z: int | float = 0  # DF027


@dataclass
class BaseRPH(BaseRP):
    """DTO object for base station position and height, msg 1006"""

    height: int | float = 0  # DF028


@dataclass
class BaseAD(DataClassMethods):
    """DTO object for antenna descriptor, msg 1007"""

    msgNum: int = 0
    bsID: int = 0
    descrLength: int = 0
    descr: str = ""
    setupID: int = 0


@dataclass
class BaseADSN(BaseAD):
    """DTO object for antenna descriptor and serial number, msg 1008"""

    # BaseAD+
    serialNumberLength: int = 0
    serialNumber: str = ""


@dataclass
class BaseADSNRC(BaseADSN):
    """ "DTO object for antenna descriptor, serial number and receiver type, msg 1033"""

    # BaseADSN+
    rcvDescriptorLength: int = 0
    rcvDescriptor: str = ""
    rcvFWVersionLength: int = 0
    rcvFWVersion: str = ""
    rcvSerNumLength: int = 0
    rcvSerNum: str = ""


@dataclass(slots=True, eq=True)
class BaseSPitem:
    """DTO object for single item of System Parameters"""

    ID: int = 0  # DF055
    isPeriodic: int | bool = 0  # DF056
    period: int | float = 0  # DF057


@dataclass
class BaseSP(DataClassMethods):
    """DTO object for system parameters, msg 1013"""

    msgNum: int = 0  # DF002
    bsID: int = 0  # DF003
    modifiedJulianDay: int = 0  # DF051
    daySec: int = 0  # DF052
    Nm: int = 0  # DF053
    leapSec: int = 0  # DF054

    # nested dataclasses are not good when loading from json file
    # shedule: list[BaseSPitem] = field(default_factory=list)

    # let it be a dictionary:
    # {MsgID:(SyncFlag,Period),}
    shedule: dict[int, tuple[int, int]] = field(default_factory=dict)


@dataclass
class BaseTS(DataClassMethods):
    """DTO object for Unicode Text String, msg 1029"""

    msgNum: int = 0  # DF002
    bsID: int = 0  # DF003
    modifiedJulianDay: int = 0  # DF051
    daySec: int = 0  # DF052
    charNum: int = 0  # DF138
    unitsNum: int = 0  # DF139
    message: str = ""  # DF140


@dataclass
class BaseGLBS(DataClassMethods):
    """ "DTO object for Glonass code-phase biases, msg 1230.

    If isCorrected == false, appropriate corrections shall be added to
    carrier phase range measurements to compensate for code-phase bias
    (alignment). If isCorrected == True, then correction values can be
    used for reversing of phase measurements' alignment.
    """

    msgNum: int = 0
    bsID: int = 0
    isCorrected: int | bool = 0
    validity: dict[str, int | bool] = field(default_factory=dict)
    correction: dict[str, int | float] = field(default_factory=dict)

    def __post_init__(self):
        # !! This creates an assumption about the order of initialisation
        # msgNum shall be initialized first: A = BaseGLBS(msgNum=1230,...)
        if self.msgNum != 1230:
            self.validity = {"1C": 0, "1P": 0, "2C": 0, "2P": 0}
            self.correction = {"1C": 0, "1P": 0, "2C": 0, "2P": 0}
