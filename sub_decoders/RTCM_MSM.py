
"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Implements subdecoder which transforms RTCM3 MSM message into a DTO
    object with observables. There are two types of DTOs:
    1. Bare integer data (as it is in the message);
    2. Reconstructed and scaled observables. 
"""


#--- Dependencies -------------------------------------------------------------------------

#from math import isnan
from gnss_types import ObservablesMSM, Attributes
from gnss_types import BareObservablesMSM4567, BareObservablesMSM123

from decoder_top import SubDecoderInterface
from utilities import MSMT
from utilities import Bits, ExceptionBitsError, catch_bits_exceptions

from logger import LOGGER_CF as logger


#--- Exceptions ----------------------------------------------------------------------------------

class ExceptionBareDataStructure(Exception):
    '''Hook error in BareObservablesMSM4567Decoder methods'''

#------------------------------------------------------------------------------------------------
    
class BareObservablesMSM17Decoder(Bits):
    '''Methods to extract bare data from MSM1..MSM7 message'''
    
    __MIN_HDR_LEN = 169
           
    __BIT_WIDTH_7 = (8,4,10,14,  20,24,10,1,10,15)
    __BIT_WIDTH_6 = (8,10,  20,24,10,1,10)
    __BIT_WIDTH_5 = (8,4,10,14,  15,22,4,1,6,15)
    __BIT_WIDTH_4 = (8,10,  15,22,4,1,6)
    __BIT_WIDTH_3 = (10, 15, 22, 4, 1)
    __BIT_WIDTH_2 = (10,     22, 4, 1)
    __BIT_WIDTH_1 = (10, 15)

    def __init__(self) -> None:
        super().__init__()
        self._ready: bool = False
        self.bd: BareObservablesMSM123|BareObservablesMSM4567

    @property
    def ready(self)->bool:
        return self._ready and self.bd != None

    @property
    def bare_data(self)->BareObservablesMSM123|BareObservablesMSM4567|None:
        return self.bd if self.ready else None

    def decode(self, buf:bytes):

        self._ready = False
        
        atr = Attributes()
        atr.msg_number = self.get_msg_num(buf)
        atr.gnss, atr.subset = MSMT.msm_subset(atr.msg_number)

        if atr.is_msm1 or atr.is_msm2 or atr.is_msm3:
            self.bd = BareObservablesMSM123()
        elif atr.is_msm4 or atr.is_msm5 or atr.is_msm6 or atr.is_msm7:
            self.bd = BareObservablesMSM4567()
        else:
            raise ExceptionBareDataStructure(f'Message {atr.msg_number} not supported.')
        
        self.bd.clear()
        self.bd.atr = atr

        offset = 24
        offset = self.__extract_hdr(buf, offset)

        # Finish if empty message
        if self.bd.hdr.sat_mask == 0:
            self._ready = True
            return

        if type(self.bd) == BareObservablesMSM4567:
            offset = self.__extract_observables4567(buf, offset)
        else:
            offset = self.__extract_observables123(buf, offset)
            
        self._ready = True
        return
    
    @catch_bits_exceptions
    def get_msg_num(self, buf: bytes)->int:
        return self.getbitu(buf, 24, 12)
    
    def __extract_hdr(self, buf:bytes, offset: int):
        '''Conv. binary header into integers'''    

        # Check minimal length
        bits_elapsed = (self.getbitu(buf, 14, 10)-3)*8
        if bits_elapsed < self.__MIN_HDR_LEN:
            raise ExceptionBareDataStructure(f'MSM hdr1 :{bits_elapsed=}')
        
        # Extract header
        msg_num, offset = self.getbitu(buf, offset, 12), offset+12
        self.bd.hdr.rs_id, offset = self.getbitu(buf, offset, 12), offset+12
        self.bd.hdr.time, offset = self.getbitu(buf, offset, 30), offset+30
        self.bd.hdr.MMB, offset = self.getbitu(buf, offset, 1), offset+1
        self.bd.hdr.IODS, offset = self.getbitu(buf, offset, 3), offset + (3+7)
        self.bd.hdr.clk_steer, offset = self.getbitu(buf, offset, 2), offset+2
        self.bd.hdr.clk_ext, offset = self.getbitu(buf, offset, 2), offset+2
        self.bd.hdr.smth_indc, offset = self.getbitu(buf, offset, 1), offset+1
        self.bd.hdr.smth_intr, offset = self.getbitu(buf, offset, 3), offset+3
        self.bd.hdr.sat_mask, offset = self.getbitu(buf, offset, 64), offset+64
        self.bd.hdr.sat_mask = self.revbitu(self.bd.hdr.sat_mask,64)
        self.bd.hdr.sgn_mask, offset = self.getbitu(buf, offset, 32), offset+32
        self.bd.hdr.sgn_mask = self.revbitu(self.bd.hdr.sgn_mask,32)        
        
        Nsat = self.bd.hdr.sat_mask.bit_count()
        Nsgn = self.bd.hdr.sgn_mask.bit_count()
        
        if Nsat == 0:
            # Do final length check
            Nbytes = (offset + 7)>>3
            if len(buf) != (Nbytes+3):
                raise ExceptionBareDataStructure(f'Failed final length check:{Nbytes=},buf_len={len(buf)}')
            else:
                return offset

        cell_bits = Nsat*Nsgn
        
        # Check consistency of cell mask's length
        bits_elapsed -= self.__MIN_HDR_LEN
        if cell_bits > 64:
            raise ExceptionBareDataStructure(f'MSM hdr2:{cell_bits=}')
        elif cell_bits > bits_elapsed:
            raise ExceptionBareDataStructure(f'MSM hdr3:{cell_bits=},{bits_elapsed=}')
        
        # Extract cell mask
        cell_mask, offset = self.getbitu(buf, offset, cell_bits), offset+cell_bits
        self.bd.hdr.cell_mask = self.revbitu(cell_mask, cell_bits)
        
        return offset

    def __extract_observables4567(self, buf:bytes, offset:int)->int:
        '''Unpack MSM4 .. MSM7 data fields'''

        Nsat = self.bd.hdr.sat_mask.bit_count()
        Nsgn = self.bd.hdr.sgn_mask.bit_count()
        Ncell = self.bd.hdr.cell_mask.bit_count()

        if (Nsat == 0) or (Nsgn == 0) or (Ncell == 0):
            raise ExceptionBareDataStructure(f'MSM hdr4: {Nsat=}, {Nsgn=}, {Ncell=}')
        
        # Check message length
        if self.bd.atr.is_msm7:
            est_len = ((offset + 36*Nsat + 80*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_7)
        elif self.bd.atr.is_msm6:
            est_len = ((offset + 18*Nsat + 65*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_6)
        elif self.bd.atr.is_msm5:
            est_len = ((offset + 36*Nsat + 63*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_5)
        else:
            est_len = ((offset + 18*Nsat + 48*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_4)
        
        if est_len != len(buf):
            raise ExceptionBareDataStructure(f'MSM data len1:{est_len=}, buf_len={len(buf)}')
        
        # Extract sat data
        bits = next(bw)
        self.bd.sat.rng_ms = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
        offset += bits*Nsat
        
        if self.bd.atr.is_msm5 or self.bd.atr.is_msm7:
            bits = next(bw)
            self.bd.sat.ext_info = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
            offset += bits*Nsat
        
        bits = next(bw)
        self.bd.sat.rng_rough = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
        offset += bits*Nsat    
        
        if self.bd.atr.is_msm5 or self.bd.atr.is_msm7:
            bits = next(bw)
            self.bd.sat.phase_rate_rough = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Nsat)))
            offset += bits*Nsat
        
        # Extract signal data
        bits = next(bw)
        self.bd.sgn.rng_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
        offset += bits*Ncell
        
        bits = next(bw)
        self.bd.sgn.phase_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))    
        offset += bits*Ncell
        
        bits = next(bw)
        self.bd.sgn.lock_time = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Ncell)))
        offset += bits*Ncell
        
        bits = next(bw)
        self.bd.sgn.hc_indc = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Ncell)))
        offset += bits*Ncell
        
        bits = next(bw)
        self.bd.sgn.c2n = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Ncell)))
        offset += bits*Ncell
        
        if self.bd.atr.is_msm5 or self.bd.atr.is_msm7:
            bits = next(bw)
            self.bd.sgn.phase_rate_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
        
        # Do final length check
        Nbytes = (offset + 7)>>3
        if len(buf) != (Nbytes+3):
            raise ExceptionBareDataStructure(f'Failed final length check:{Nbytes=},buf_len={len(buf)}')

        return offset

    def __extract_observables123(self, buf:bytes, offset:int)->int:
        '''Unpack MSM4 and MSM5 data fields'''

        Nsat = self.bd.hdr.sat_mask.bit_count()
        Nsgn = self.bd.hdr.sgn_mask.bit_count()
        Ncell = self.bd.hdr.cell_mask.bit_count()

        if (Nsat == 0) or (Nsgn == 0) or (Ncell == 0):
            raise ExceptionBareDataStructure(f'MSM hdr4: {Nsat=}, {Nsgn=}, {Ncell=}')
        
        # Check message length
        if self.bd.atr.is_msm1:
            est_len = ((offset + 10*Nsat + 15*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_1)
        elif self.bd.atr.is_msm2:
            est_len = ((offset + 10*Nsat + 28*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_2)
        elif self.bd.atr.is_msm3:
            est_len = ((offset + 10*Nsat + 43*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_3)
        else:
            est_len = 0
        
        if est_len != len(buf):
            raise ExceptionBareDataStructure(f'MSM data len1:{est_len=}, buf_len={len(buf)}')
        
        # Extract sat data
        bits = next(bw)
        self.bd.sat.rng_rough = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
        offset += bits*Nsat    
                
        # Extract signal data
        if self.bd.atr.is_msm1:
            bits = next(bw)
            self.bd.sgn.rng_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
        else:
            if self.bd.atr.is_msm3:
                bits = next(bw)
                self.bd.sgn.rng_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
                offset += bits*Ncell
  
            bits = next(bw)
            self.bd.sgn.phase_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))    
            offset += bits*Ncell
            
            bits = next(bw)
            self.bd.sgn.lock_time = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
            
            bits = next(bw)
            self.bd.sgn.hc_indc = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
                        
        # Do final length check
        Nbytes = (offset + 7)>>3
        if len(buf) != (Nbytes+3):
            raise ExceptionBareDataStructure(f'Failed final length check:{Nbytes=},buf_len={len(buf)}')

        return offset
#------------------------------------------------------------------------------------------------

class Bare2Scaled():

    __SCALERS67 = {
        'rng':(2**-29),
        'phs':(2**-31),
        'dpl':0.0001,
        'ltm':MSMT.unpack_tlock10,
        'c2n':0.0625
    }

    __SCALERS45 = {
        'rng':(2**-24),               #DF400
        'phs':(2**-29),               #DF401
        'dpl':(0.0001),               #DF404
        'ltm':MSMT.unpack_tlock4,     #DF402
        'c2n':1                       #DF403
    }

    __CHECKERS67 = {
        'rng':MSMT.isDF405_OK,
        'phs':MSMT.isDF406_OK,
        'dpl':MSMT.isDF404_OK,
    }

    __CHECKERS45 = {
        'rng':MSMT.isDF400_OK,
        'phs':MSMT.isDF401_OK,
        'dpl':MSMT.isDF404_OK,
    }

    def __init__(self) -> None:
        self.sgn_map : tuple[str, ...] = (str(),)
        self.slots_per_sat : tuple[int, ...] = (int(),)
        self.sat_list : tuple[int, ...] = (int(),)
        
    def convert(self, src: BareObservablesMSM4567|BareObservablesMSM123|None) -> ObservablesMSM|None:
        '''Converts bare data into IRTCM.Observables form.'''

        if not isinstance(src,(BareObservablesMSM4567,BareObservablesMSM123)):
            return None

        if (src.atr.gnss == ''):
            return None

        # Create empty return value
        rv = ObservablesMSM()
        rv.atr = src.atr

        rv.hdr.time = src.time
        rv.hdr.day = src.day

        rv.aux.rs_id = src.hdr.rs_id
        rv.aux.MMB = src.hdr.MMB
        rv.aux.IODS = src.hdr.IODS
        rv.aux.clk_steer['code'] = src.hdr.clk_steer
        rv.aux.clk_steer['val'] = MSMT.unpack_clk_steer(src.hdr.clk_steer)
        rv.aux.clk_ext['code'] = src.hdr.clk_ext
        rv.aux.clk_ext['val'] = MSMT.unpack_clk_ext(src.hdr.clk_ext)
        rv.aux.smth_indc['code'] = src.hdr.smth_indc
        rv.aux.smth_indc['val'] = MSMT.unpack_smth_indc(src.hdr.smth_indc)
        rv.aux.smth_intr['code'] = src.hdr.smth_intr
        rv.aux.smth_intr['val'] = MSMT.unpack_smth_intr(src.hdr.smth_intr)
        
        # Process empty message
        if src.hdr.sat_mask == 0:
            rv.hdr.sats = ()
            rv.hdr.signals = {}
            return rv

        # Make list of satellites
        self.sat_list = tuple((i+1 for i in range(0,64) if (src.hdr.sat_mask & (1<<i))))
        sat_num = len(self.sat_list)
        rv.hdr.sats = self.sat_list
        # Make list of signals
        self.sgn_map = (i+1 for i in range(0,32) if (src.hdr.sgn_mask & (1<<i)))
        self.sgn_map = tuple((MSMT.rnx_lit(src.atr.gnss, s) for s in self.sgn_map))
        rv.hdr.signals = {s:MSMT.crr_frq(src.atr.gnss, s) for s in self.sgn_map}

        # Calc. number of frequency bins per sat.
        M = src.hdr.sgn_mask.bit_count()
        mask = (1<<M)-1
        self.slots_per_sat = tuple((((src.hdr.cell_mask >> M*i) & mask) for i in range(0,sat_num)))
        
        if type(src) == BareObservablesMSM4567:
            self._convert_obs47(src, rv)
        else:
            self._convert_obs13(src, rv)

        return rv 

    def _convert_obs47(self, src : BareObservablesMSM4567, rv: ObservablesMSM)->None:
    
        # Choose scalers (fine/coarse resolution)
        if (src.atr.is_msm7 or src.atr.is_msm6):
            scalers = self.__SCALERS67
            checkers = self.__CHECKERS67
        else:
            scalers = self.__SCALERS45
            checkers = self.__CHECKERS45

        # Create frequency slots in output structure
        # Add empty dictionary for each frequency slot
        for sgn in self.sgn_map:
            rv.obs.rng.update({sgn:{}})
            rv.obs.c2n.update({sgn:{}})
            rv.obs.dpl.update({sgn:{}})
            rv.obs.phs.update({sgn:{}})
            rv.obs.ltm.update({sgn:{}})
            rv.obs.hca.update({sgn:{}})
                
        # Unpack measurements and fill empty dictionaries
        # Pair {sat:value} should be formed for each observable

        # Here 'sat_idx' and 'sgn_idx' are indexes in the lists of observables
        sat_idx, sgn_idx = 0, 0
        # Pass through satellites in the list
        for slots in self.slots_per_sat:
            # sat - satellite number
            sat = self.sat_list[sat_idx]

            # if self.is_msm7 or self.is_msm5:
            #     rv.aux.ext_info.append(src.sat.ext_info[sat_idx])
            
            rng_ok = src.sat.rng_ms[sat_idx] != 255
            if rng_ok:
                rng = float((src.sat.rng_ms[sat_idx]<<10) + src.sat.rng_rough[sat_idx])/1024.0
            else:
                logger.warning(f"No coarse range:gnss={src.atr.gnss},({sat=},{sgn=})")
            
            if src.atr.is_msm7 or src.atr.is_msm5:
                phase_rate_ok = (src.sat.phase_rate_rough[sat_idx] & 0x3fff) != 0x2000
                if phase_rate_ok:
                    phase_rate = float(src.sat.phase_rate_rough[sat_idx])
                else:
                    logger.warning(f"No coarse doppler:gnss={src.atr.gnss},({sat=},{sgn=})")
            else:
                phase_rate_ok = False
            
            # Pass through signals of satellite 'sat'
            i = 0
            while slots:
                
                # sgn - RINEX literal - code of signal
                sgn = self.sgn_map[i]
                i += 1
                slotExist = slots & 0x01
                slots = slots >> 1
    
                if (slotExist == 0):
                    continue
                
                # Make fine code range 
                if rng_ok:
                    if checkers['rng'](src.sgn.rng_fine[sgn_idx]):
                        tmp = (rng + float(src.sgn.rng_fine[sgn_idx])*scalers['rng'])*MSMT.CRNG_1MS
                        rv.obs.rng[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine range:gnss={src.atr.gnss},({sat=},{sgn=})")

                # Make fine phase range 
                if rng_ok:
                    if checkers['phs'](src.sgn.phase_fine[sgn_idx]):
                        tmp = (rng + float(src.sgn.phase_fine[sgn_idx])*scalers['phs'])*MSMT.CRNG_1MS
                        rv.obs.phs[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine phase:gnss={src.atr.gnss},({sat=},{sgn=})")
                    
                if phase_rate_ok:
                    # Make fine doppler
                    if checkers['dpl'](src.sgn.phase_rate_fine[sgn_idx]):
                        tmp = phase_rate + float(src.sgn.phase_rate_fine[sgn_idx])*scalers['dpl']
                        rv.obs.dpl[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine doppler:gnss={src.atr.gnss},({sat=},{sgn=})")

                # Make fine lock time
                tmp = scalers['ltm'] (src.sgn.lock_time[sgn_idx])
                rv.obs.ltm[sgn].update({sat:tmp})
                
                # Make fine C2N ratio
                tmp = float(src.sgn.c2n[sgn_idx])*scalers['c2n']
                rv.obs.c2n[sgn].update({sat:tmp})

                # Make phase half cycle ambiguity indicator
                tmp = src.sgn.hc_indc[sgn_idx] != 0
                rv.obs.hca[sgn].update({sat:tmp})

                sgn_idx += 1
            sat_idx += 1

        # Delete empty frequency slots.
        for sgn in self.sgn_map:
            if not len(rv.obs.dpl[sgn]) : del(rv.obs.dpl[sgn])
            if not len(rv.obs.rng[sgn]) : del(rv.obs.rng[sgn])
            if not len(rv.obs.c2n[sgn]) : del(rv.obs.c2n[sgn])
            if not len(rv.obs.phs[sgn]) : del(rv.obs.phs[sgn])
            if not len(rv.obs.ltm[sgn]) : del(rv.obs.ltm[sgn])
            if not len(rv.obs.hca[sgn]) : del(rv.obs.hca[sgn])

    
    def _convert_obs13(self, src : BareObservablesMSM123, rv: ObservablesMSM)->None:

        scalers = self.__SCALERS45
        
        # Create frequency slots in output structure
        # Add empty dictionary for each frequency slot
        for sgn in self.sgn_map:
            rv.obs.rng.update({sgn:{}})
            rv.obs.phs.update({sgn:{}})
            rv.obs.ltm.update({sgn:{}})
            rv.obs.hca.update({sgn:{}})
                
        # Unpack measurements and fill empty dictionaries
        # A pair {sat:value} should be formed for each observable

        # Here 'sat_idx' and 'sgn_idx' are indexes in the lists of observables
        sat_idx, sgn_idx = 0, 0
        # Pass through satellites in the list
        for slots in self.slots_per_sat:
            # sat - satellite number
            sat = self.sat_list[sat_idx]
            
            rng = float(src.sat.rng_rough[sat_idx])/1024.0
            rng_ok = src.atr.is_msm1 or src.atr.is_msm3
            ph_ok = src.atr.is_msm2 or src.atr.is_msm3
            
            # Pass through signals of satellite 'sat'
            i = 0
            while slots:
                
                # sgn - RINEX literal - code of signal
                sgn = self.sgn_map[i]
                i += 1
                slotExist = slots & 0x01
                slots = slots >> 1
    
                if (slotExist == 0):
                    continue

                # Make fine code range
                if rng_ok:
                    if (src.sgn.rng_fine[sgn_idx] & 0x7fff) != 0x4000:
                        tmp = (rng + float(src.sgn.rng_fine[sgn_idx])*scalers['rng'])*MSMT.CRNG_1MS
                        rv.obs.rng[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine range:gnss={src.atr.gnss},({sat=},{sgn=})")
                        ph_ok = False

                # Make fine phase range
                if ph_ok:
                    if (src.sgn.phase_fine[sgn_idx] & 0x3fffff) == 0x200000:
                        logger.info(f"No fine phase:gnss={src.atr.gnss},({sat=},{sgn=})")
                    else:
                        tmp = (rng + float(src.sgn.phase_fine[sgn_idx])*scalers['phs'])*MSMT.CRNG_1MS
                        rv.obs.phs[sgn].update({sat:tmp})
                    
                        # Make fine lock time
                        tmp = scalers['ltm'] (src.sgn.lock_time[sgn_idx])
                        rv.obs.ltm[sgn].update({sat:tmp})
                        
                        # Make phase half cycle ambiguity indicator
                        tmp = src.sgn.hc_indc[sgn_idx] != 0
                        rv.obs.hca[sgn].update({sat:tmp})

                sgn_idx += 1
            sat_idx += 1

        # Delete empty frequency slots.
        for sgn in self.sgn_map:
            if not len(rv.obs.rng[sgn]) : del(rv.obs.rng[sgn])
            if not len(rv.obs.phs[sgn]) : del(rv.obs.phs[sgn])
            if not len(rv.obs.ltm[sgn]) : del(rv.obs.ltm[sgn])
            if not len(rv.obs.hca[sgn]) : del(rv.obs.hca[sgn])

#------------------------------------------------------------------------------------------------

def decode_msm17(is_bare_output: bool, buf:bytes) -> BareObservablesMSM4567|BareObservablesMSM123|ObservablesMSM|None:
    """Process MSM1..MSM7 message"""
    
    msm = BareObservablesMSM17Decoder()
    mnum = msm.get_msg_num(buf)

    try:
        msm.decode(buf)
    except ExceptionBareDataStructure as ex:
        logger.error(f"Msg {mnum}. Decoding failed. " + ex.args[0])
    except ExceptionBitsError as ex:
        logger.error(f"Msg {mnum}. Decoding failed. " + ex.args[0])
    except IndexError as ie:
        logger.error(f"Msg {mnum}. Decoding failed. Indexing error: {type(ie)}: {ie}")
    except ArithmeticError as ae:
        logger.error(f"Msg {mnum}. Decoding failed. Arithm error: {type(ae)}: {ae}")
    except Exception as ex:
        logger.error(f"Msg {mnum}. Decoding failed. Unexpected error:" + f"{type(ex)}: {ex}")
    else:
        pass

    if not msm.ready:
        return None

    if is_bare_output:
        logger.info(f'Msg {mnum}. Decoding succeeded. t = {msm.bd.time}, sats = {msm.bd.hdr.sat_mask.bit_count()}.')
        return msm.bare_data
    
    scaler = Bare2Scaled()

    try:
        rv = scaler.convert(msm.bare_data)
    except IndexError as ie:
        logger.error(f"Indexing error in get_scaled_obs() {type(ie)}: {ie}")
    except ArithmeticError as ae:
        logger.error(f"Arithmetic error in get_scaled_obs() {type(ae)}: {ae}")
    except Exception as ex:
        logger.error(f"Undefined error in get_scaled_obs() {type(ex)}: {ex}")
    else:
        logger.info(f'Msg {mnum}. Decoding succeeded. t = {rv.hdr.time}, sats = {len(rv.hdr.sats)}.')

    return rv



class SubdecoderMSM4567():
    '''Implements decoding of RTCM MSM4, MSM5, MSM6, MSM7 messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__bare_data = bare_data
        self.io = SubDecoderInterface('MSM47O', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = set(self.io.io_spec.keys())
        pass
                
    def decode(self, buf:bytes) -> ObservablesMSM | BareObservablesMSM4567 | None:
        return decode_msm17(self.__bare_data,buf)


class SubdecoderMSM123():
    '''Implements decoding of RTCM MSM1, MSM2, MSM3 messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.__bare_data = bare_data
        self.io = SubDecoderInterface('MSM13O', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = set(self.io.io_spec.keys())
        pass
                
    def decode(self, buf:bytes) -> ObservablesMSM | BareObservablesMSM123 | None:
        return decode_msm17(self.__bare_data,buf)