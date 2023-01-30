

#__all__ = ['ObservablesMSM', 'BareObservablesMSM4567']




class ObservablesMSM():
    '''Represents products of MSMx message decoding'''
    
    __slots__ = ('hdr', 'obs', 'aux', 'atr')

    def __init__(self) -> None:

        self.obs = _ObservablesObs()
        self.hdr = _ObservablesHdrMSM()
        self.aux = _ObservablesAuxMSM()
        self.atr = Attributes()


class Attributes():
    """Some auxiliary parameters accompanying block of measurements"""

    __slots__ = ('gnss', 'subset', 'msg_number')

    def __init__(self) -> None:
        self.clear()

    def clear(self)->None:
        # 'gnss' encodes GNSS in RINEX style: G, R, E, B, I ... 
        # 'gnss' == '' - default value - indicates empty structure
        self.gnss: str = ''
        # String literal used to identify subset of RTCM MSM messages.
        # Range: { MSM1, MSM2, MSM3, MSM4, MSM5, MSM6, MSM7 }
        self.subset: str = ''
        self.msg_number: int = 0

    @property
    def is_msm7(self)->bool:
        return self.subset == "MSM7"
    
    @property
    def is_msm6(self)->bool:
        return self.subset == "MSM6" 
    
    @property
    def is_msm5(self)->bool:
        return self.subset == "MSM5"

    @property
    def is_msm4(self)->bool:
        return self.subset == "MSM4"

    @property
    def is_msm3(self)->bool:
        return self.subset == "MSM3"
    
    @property
    def is_msm2(self)->bool:
        return self.subset == "MSM2"

    @property
    def is_msm1(self)->bool:
        return self.subset == "MSM1"


class _ObservablesHdrMSM():
    ''' RTCM header data. Common for all sats.'''
    
    __slots__ = ('gnss', 'signals', 'sats', 'time', 'day')

    def __init__(self) -> None:
        # 'signals' lists available frequency slots/signals in RINEX style
        #  and encodes corresponding carrier frequencies. 
        self.signals: dict[str:float] = {}
        # 'sats' represents available satellites (1-based numbers),
        self.sats: tuple[int] = ()
        # GNSS time from RTCM header
        self.time : int = 0
        # Week day, zero based, valid only for GLONASS (gnss=='R')
        self.day : int = 0

    def _make_example(self):
        self.signals = {'1C':1575.42, '2C':1227.6 }  #[band:kHz]
        self.sats = (1, 2, 5, 32)
        self.time = 420525000                         # [ms]
        self.day = 0

class _ObservablesObs:
    ''' Implements container for observables.
    
    Here and below different observable are grouped in pairs in {'sat_number':'obs_value'}
    manner. Then, grouped by signal/frequency slot implication. Available signals encoded in
    RINEX manner. Number of available frequency slots, as well as 
    number of observables in each slot may deviate. See __make_example() to get a clue
    about data representation'''
   
    __slots__ = ('rng', 'phs', 'ltm', 'hca', 'dpl', 'c2n')
     
    def __init__(self) -> None:
        # 'rng' contains code range measurements grouped by signal
        #There would be an empty dict if there are no code measurements in this message
        self.rng : dict[str, dict[int,float]] = {}     # [m],
        # 'phs' contains carrier phase range measurements grouped by signal
        # There would be an empty dict if there are no phase measurements in this message
        self.phs : dict[str, dict[int,float]] = {}     # [m],
        # 'lock_time' contains time interval in [ms] 'phase' has been locked for the moment
        # There would be an empty dict if there are no lock-time data in this message
        self.ltm : dict[str, dict[int,int]] = {}      # [ms],
        # 'hca' depicts half-cycle ambiguity in phase measurements when True. 
        # There would be an empty dict if there are no HC info in this message. If so, HC
        # ambiguity assumed already resolved.
        self.hca : dict[str, dict[int,bool]] = {} 
        # 'dpl' contains phase rate measurements grouped by signal
        # There would be an empty dict if there are no doppler meas. in this message
        self.dpl : dict[str, dict[int,float]] = {}    # [Hz]
        # 'c2n' - carrier to noise ratio
        self.c2n : dict[str, dict[int,float]] = {}     # [dB/Hz]

    def __make_example(self):
        self.rng = {'1C': {1:24.2e6, 32:24.1e6}, '2C': {1:24.2e6, 32:24.1e6}}
        self.phs = {'1C': {1:24.2e6, 32:24.1e6}, '2C': {1:24.2e6,         } }
        self.ltm = {'1C': {1:125000, 32:300000}, '2C': {1:2000, 32:3000}    }
        self.hca = {'1C': {1:False, 32:True},    '2C':{1:False, 32:True}    }
        self.dpl = {'1C': {1:3000.0, 32:1231.0},                            }
        self.c2n = {'1C': {1:48.0, 32:45.0},     '2C': {1:43.0, 32:44.0}    }
        

class _ObservablesAuxMSM:
    '''Auxiliary data specific for MSM messages.'''

    __slots__ = ('rs_id','MMB','IODS','clk_steer','clk_ext','smth_indc','smth_intr')
    
    def __init__(self) -> None:
        # [df003],b12, reference station ID
        self.rs_id: int = 42
         # [df393],b1, multiple message bit               
        self.MMB: int = 0
        # [df409],b3, issue of data station                
        self.IODS: int = 0
        # [df411],b2, clock steering indicator               
        self.clk_steer: dict[int,str] = {'code':2, 'val':"UNDEF"}
        # [df412],b2, external clock indicator       
        self.clk_ext: dict[int,str] = {'code':3, 'val':"UNDEF"}
        # [df417],b1, divergence free smoothing indicator       
        self.smth_indc: dict[int,str] = {'code':0, 'val':"UNDEF"}
        # [df418],b3, divergence free interval      
        self.smth_intr: dict[int,str] = {'code':0, 'val':"NOSMTH"}     
    
class _ObservablesAuxLeg:
    '''Auxiliary data specific for Legacy messages.'''

    __slots__ = ('rs_id',)
    
    def __init__(self) -> None:
        # [df003],b12, reference station ID
        self.rs_id: int = 42

# ----------------------------------------------------------------------------------

class _BareObservablesHdrMSM():
    ''' Bare RTCM MSM header data. Common for all sats.'''
    
    __slots__ = ('rs_id', 'time', 'MMB',
                 'IODS', 'clk_steer', 'clk_ext',
                 'smth_indc', 'smth_intr', 'sat_mask',
                 'sgn_mask', 'cell_mask')

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.rs_id : int = 0
        self.time : int = 0
        self.MMB : int = 0
        self.IODS : int = 0
        self.clk_steer : int = 0
        self.clk_ext : int = 0
        self.smth_indc : int = 0
        self.smth_intr : int = 0
        self.sat_mask : int = 0
        self.sgn_mask : int = 0
        self.cell_mask : int = 0
       
class _BareObservablesSatDataMSM4567():
    ''' Bare RTCM MSM4, MSM5, MSM6, MSM7 satellite data.'''

    __slots__ = ('rng_ms', 'ext_info', 'rng_rough', 'phase_rate_rough')

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.rng_ms : tuple[int] = ()
        self.ext_info : tuple[int] = () 
        self.rng_rough : tuple[int] = () 
        self.phase_rate_rough  : tuple[int] = ()

class _BareObservablesSignalDataMSM4567():
    ''' Bare RTCM MSM4, MSM5, MSM6, MSM7 signal data.'''

    __slots__ = ('rng_fine','phase_fine','lock_time','hc_indc','c2n','phase_rate_fine')
    
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.rng_fine : tuple[int] = ()
        self.phase_fine : tuple[int] = ()
        self.lock_time : tuple[int] = ()
        self.hc_indc : tuple[int] = ()
        self.c2n : tuple[int] = ()
        self.phase_rate_fine : tuple[int] = ()

class BareObservablesMSM4567():
    ''' Bare RTCM MSM4, MSM5, MSM6, MSM7 signal data.'''

    __slots__ = ('hdr', 'sat', 'sgn', 'atr')

    def __init__(self) -> None:
        self.atr = Attributes()
        self.hdr = _BareObservablesHdrMSM()
        self.sat = _BareObservablesSatDataMSM4567()
        self.sgn = _BareObservablesSignalDataMSM4567()

    def clear(self) -> None:
        self.atr.clear()
        self.hdr.clear()
        self.sat.clear()
        self.sgn.clear()
        
    @property
    def time(self) -> int:
        return self.hdr.time & 0x7ffffff if self.atr.gnss == 'R' else self.hdr.time

    @property
    def day(self) -> int:
        return (self.hdr.time>>27) & 0x07 if self.atr.gnss == 'R' else 0
    

class _BareObservablesSatDataMSM123():
    ''' Bare RTCM MSM1, MSM2, MSM3 satellite data.'''

    __slots__ = ('rng_rough')

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.rng_rough : tuple[int] = ()

class _BareObservablesSignalDataMSM123():
    ''' Bare RTCM MSM1, MSM2, MSM3 signal data.'''

    __slots__ = ('rng_fine','phase_fine','lock_time','hc_indc')
    
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.rng_fine : tuple[int] = ()
        self.phase_fine : tuple[int] = ()
        self.lock_time : tuple[int] = ()
        self.hc_indc : tuple[int] = ()

class BareObservablesMSM123():
    ''' Bare RTCM MSM4, MSM5, MSM6, MSM7 signal data.'''

    __slots__ = ('hdr', 'sat', 'sgn', 'gnss', 'subset')

    def __init__(self) -> None:
        self.atr = Attributes()
        self.hdr = _BareObservablesHdrMSM()
        self.sat = _BareObservablesSatDataMSM123()
        self.sgn = _BareObservablesSignalDataMSM123()

    def clear(self) -> None:
        self.atr.clear()
        self.hdr.clear()
        self.sat.clear()
        self.sgn.clear()
