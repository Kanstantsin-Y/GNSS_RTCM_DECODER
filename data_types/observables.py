

#__all__ = ['ObservablesMSM', 'BareObservablesMSM4567']




class ObservablesMSM():
    '''Represents products of MSMx or Legacy messsage decoding'''
    
    __slots__ = ('hdr', 'obs', 'aux', 'subset', 'nsat', 'nsign')

    def __init__(self) -> None:

        # 'subset' may have value from {MSM1, MSM2,...,MSM7}
        # 'subset' == '' indicates default state of all fields.
        self.subset = ''
        self.obs = _ObservablesObs()
        self.hdr = _ObservablesHdrMSM()
        self.aux = _ObservablesAuxMSM()
        
class _ObservablesHdrMSM():
    ''' RTCM header data. Common for all sats.'''
    
    __slots__ = ('gnss', 'signals', 'sats', 'time', 'day')

    def __init__(self) -> None:
        # 'gnss' encodes GNSS in RINEX style: G, R, E, B, I ... 
        # 'gnss' == '' - default value - indicates empty structure
        # Defaults for other fields do not indicate 'initial state'
        # as their defaults are valid values for empty message.
        self.gnss : str = ''
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
        self. gnss = 'G'
        self.signals = {'1C':1575.42, '2C':1227.6 }  #[band:kHz]
        self.sats = (1, 2, 5, 32)
        self.time = 420525000                         # [ms]
        self.day = 0

class _ObservablesObs:
    ''' Iplements container for observables.
    
    Here and below diffrent observable are grouped in pairs in {'sat_number':'obs_value'}
    manner. Then, grouped by signal/frequency slot implication. Available signals encoded in
    RINEX manner. Number of available frequency slots, as well as 
    number of observables in each slot may deviate. See __make_example() to get a clue
    about data representation'''
   
    __slots__ = ('rng', 'phs', 'ltm', 'hca', 'dpl', 'c2n')
     
    def __init__(self) -> None:
        # 'rng' containes code range measurements grouped by signal
        #There would be an empty dict if there are no code measurements in this message
        self.rng : dict[str, dict[int,float]] = {}     # [m],
        # 'phs' containes carrier phase range measurements grouped by signal
        # There would be an empty dict if there are no phase measurements in this message
        self.phs : dict[str, dict[int,float]] = {}     # [m],
        # 'lock_time' contains time interval in [ms] 'phase' has been locked for the moment
        # There would be an empty dict if there are no lock-time data in this message
        self.ltm : dict[str, dict[int,int]] = {}      # [ms],
        # 'hca' depicts half-cycle ambiguity in phase measurements when True. 
        # There would be an empty dict if there are no HC info in this message. If so, HC
        # ambigiuty assumed already resolved.
        self.hca : dict[str, dict[int,bool]] = {} 
        # 'dpl' containes phase rate measurements grouped by signal
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
        # [df417],b1, divergence free smothing indicator       
        self.smth_indc: dict[int,str] = {'code':0, 'val':"UNDEF"}
        # [df418],b3, divergence free interval      
        self.smth_intr: dict[int,str] = {'code':0, 'val':"NOSMTH"}     
    
class _ObservablesAuxLeg:
    '''Auxiliary data specific for MSM messages.'''

    __slots__ = ('rs_id',)
    
    def __init__(self) -> None:
        # [df003],b12, reference station ID
        self.rs_id: int = 42

# ----------------------------------------------------------------------------------

class BareObservablesMSM4567():
    ''' Bare RTCM MSM4, MSM5, MSM6, MSM7 signal data.'''

    __slots__ = ('hdr', 'sat', 'sgn')

    def __init__(self) -> None:
        self.hdr = _BareObservablesHdrMSM()
        self.sat = _BareObservablesSatDataMSM4567()
        self.sgn = _BareObservablesSignalDataMSM4567()

    def clear(self) -> None:
        self.hdr.clear()
        self.sat.clear()
        self.sgn.clear()

class _BareObservablesHdrMSM():
    ''' Bare RTCM MSM header data. Common for all sats.'''
    
    __slots__ = ('msg_num', 'rs_id', 'time', 'MMB',
                 'IODS', 'clk_steer', 'clk_ext',
                 'smth_indc', 'smth_intr', 'sat_mask',
                 'sgn_mask', 'cell_mask')

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.msg_num : int = 0
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

