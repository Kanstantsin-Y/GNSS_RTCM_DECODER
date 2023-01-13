
#--- Dependencies -------------------------------------------------------------------------

from math import isnan

from data_types.observables import ObservablesMSM
from data_types.observables import BareObservablesMSM4567

from RTCM_decoder import SubDecoderInterface
from utilities.RTCM_utilities import MSMT

from utilities.bits import Bits
from utilities.bits import ExceptionBitsError
from utilities.bits import catch_bits_exceptions

from cons_file_logger import LOGGER_CF as logger


#--- Exceptions ----------------------------------------------------------------------------------

class ExceptionBareDataStructure(Exception):
    '''Hook error in BareObservablesMSM4567Decoder methods'''

#------------------------------------------------------------------------------------------------
    
class BareObservablesMSM4567Decoder(Bits):
    '''Methods to extract bare data from MSM4567 message'''
    
    __MIN_HDR_LEN = 169
    
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
        'dpl':0.0001,                 #DF404
        'ltm':MSMT.unpack_tlock4,     #DF402
        'c2n':1                       #DF403
    }

    __BIT_WIDTH_7 = (8,4,10,14,  20,24,10,1,10,15)
    __BIT_WIDTH_6 = (8,10,  20,24,10,1,10)
    __BIT_WIDTH_5 = (8,4,10,14,  15,22,4,1,6,15)
    __BIT_WIDTH_4 = (8,10,  15,22,4,1,6)

    def __init__(self) -> None:
        super().__init__()

        self.bd = BareObservablesMSM4567()
        self.subset = ''
        self.gnss = ''
        self.ready = False

    def decode(self, buf:bytes):

        self.bd.clear()
        self.ready = False

        mnum = self.get_msg_num(buf)
        gnss, subset = MSMT.msm_subset(mnum)

        if not subset in ('MSM7', 'MSM6', 'MSM5', 'MSM4'):
            raise ExceptionBareDataStructure(f'Message {mnum} not supported.')
        
        self.subset = subset
        self.gnss = gnss
        self.bd.hdr.msg_num = mnum
        
        offset = 24
        offset = self.__extract_hdr(buf, offset)

        # Finish if empty message
        if self.bd.hdr.sat_mask == 0:
            self.ready = True
            return

        offset = self.__extract_observables4567(buf, offset)
        self.ready = True
        return
    
    @catch_bits_exceptions
    def get_msg_num(self, buf: bytes)->bool:
        return self.getbitu(buf, 24, 12)
    
    def is_msm6(self)->bool:
        return self.subset == "MSM6" 

    def is_msm7(self)->bool:
        return self.subset == "MSM7"

    def is_msm5(self)->bool:
        return self.subset == "MSM5"

    def is_msm4(self)->bool:
        return self.subset == "MSM4"

    def is_msm4567(self)->bool:
        return self.is_msm4() or self.is_msm5() or self.is_msm6() or self.is_msm7()

    def __extract_hdr(self, buf:bytes, offset: int):
        '''Conv. binary header into integers'''    

        # Check minimal length
        bits_elapsed = (self.getbitu(buf, 14, 10)-3)*8
        if bits_elapsed < self.__MIN_HDR_LEN:
            raise ExceptionBareDataStructure(f'MSM hdr1 :{bits_elapsed=}')
        
        # Extract header
        self.bd.hdr.msg_num, offset = self.getbitu(buf, offset, 12), offset+12
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
        '''Unpack MSM4 and MSM5 data fields'''

        Nsat = self.bd.hdr.sat_mask.bit_count()
        Nsgn = self.bd.hdr.sgn_mask.bit_count()
        Ncell = self.bd.hdr.cell_mask.bit_count()

        if (Nsat == 0) or (Nsgn == 0) or (Ncell == 0):
            raise ExceptionBareDataStructure(f'MSM hdr4: {Nsat=}, {Nsgn=}, {Ncell=}')
        
        # Check message length
        if self.is_msm7():
            est_len = ((offset + 36*Nsat + 80*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_7)
        elif self.is_msm6():
            est_len = ((offset + 18*Nsat + 65*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_6)
        elif self.is_msm5():
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
        
        if self.is_msm5() or self.is_msm7():
            bits = next(bw)
            self.bd.sat.ext_info = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
            offset += bits*Nsat
        
        bits = next(bw)
        self.bd.sat.rng_rough = tuple((self.getbitu(buf, offset+i*bits, bits) for i in range(0,Nsat)))
        offset += bits*Nsat    
        
        if self.is_msm5() or self.is_msm7():
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
        
        if self.is_msm5() or self.is_msm7():
            bits = next(bw)
            self.bd.sgn.phase_rate_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
        
        # Do final length check
        Nbytes = (offset + 7)>>3
        if len(buf) != (Nbytes+3):
            raise ExceptionBareDataStructure(f'Failed final length check:{Nbytes=},buf_len={len(buf)}')

        return offset

#------------------------------------------------------------------------------------------------

    def get_bare_obs(self)->BareObservablesMSM4567:
        '''Returns bare (integer) unscaled data extracted from MSM4, MSM5, MSM6, MSM7 messages'''
        return self.bd

    def get_scaled_obs(self)->ObservablesMSM:
        '''Converts bare data into IRTCM.Observables form.'''
        
        # Create empty pattern
        rv = ObservablesMSM()
        
        if not self.ready:
            return rv
                
        src = self.bd           # shorter name
        rv.hdr.gnss = self.gnss
        rv.subset = self.subset

        if self.gnss == 'R':
            rv.hdr.time = src.hdr.time & 0x7ffffff
            rv.hdr.day = (src.hdr.time >> 27) & 0x07
        else:
            rv.hdr.time = src.hdr.time
            rv.hdr.day = 0

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
            rv.nsat = 0
            rv.hdr.signals = {}
            rv.nsign = 0
            return rv

        # Make list of satellites
        sat_list = tuple((i+1 for i in range(0,64) if (src.hdr.sat_mask & (1<<i))))
        sat_num = len(sat_list)
        rv.hdr.sats = sat_list
        rv.nsat = sat_num
        # Make list of signals
        sgn_map = (i+1 for i in range(0,32) if (src.hdr.sgn_mask & (1<<i)))
        sgn_map = tuple((MSMT.rnx_lit(self.gnss, s) for s in sgn_map))
        rv.hdr.signals = {s:MSMT.crr_frq(self.gnss, s) for s in sgn_map}
        rv.nsign = len(sgn_map)

        # Calc. number of frequency bins per sat.
        M = src.hdr.sgn_mask.bit_count()
        mask = (1<<M)-1
        slots_per_sat = tuple((((src.hdr.cell_mask >> M*i) & mask).bit_count() for i in range(0,sat_num)))
        
        # Choose scalers (fine/coarse resolution)
        if (self.is_msm7() or self.is_msm6()):
            scalers = self.__SCALERS67
        else:
            scalers = self.__SCALERS45

        # Create frequency slots in output structure
        # Add empty dictionary for each frequency slot
        for sgn in sgn_map:
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
        for slots in slots_per_sat:
            # sat - satellite number
            sat = sat_list[sat_idx]

            # if self.is_msm7() or self.is_msm5():
            #     rv.aux.ext_info.append(src.sat.ext_info[sat_idx])
            
            rng_ok = src.sat.rng_ms[sat_idx] != 255
            if rng_ok:
                rng = float((src.sat.rng_ms[sat_idx]<<10) + src.sat.rng_rough[sat_idx])/1024.0
            else:
                logger.warning(f"No coarse range:gnss={self.gnss},({sat=},{sgn=})")
            
            if self.is_msm7() or self.is_msm5():
                phase_rate_ok = (src.sat.phase_rate_rough[sat_idx] & 0x3fff) != 0x2000
                if phase_rate_ok:
                    phase_rate = float(src.sat.phase_rate_rough[sat_idx])
                else:
                    logger.warning(f"No coarse doppler:gnss={self.gnss},({sat=},{sgn=})")
            else:
                phase_rate_ok = False
            
            # Pass through signals of satellite 'sat'
            for i in range(slots):
                # sgn - RINEX literal - code of signal
                sgn = sgn_map[i]

                # Make fine code range 
                if rng_ok:
                    if (src.sgn.rng_fine[sgn_idx] & 0xfffff) != 0x80000:
                        tmp = (rng + src.sgn.rng_fine[sgn_idx]*scalers['rng'])*MSMT.CRNG_1MS
                        rv.obs.rng[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine range:gnss={self.gnss},({sat=},{sgn=})")

                # Make fine phase range 
                if rng_ok:
                    if (src.sgn.phase_fine[sgn_idx] & 0xffffff) != 0x800000:
                        tmp = (rng + src.sgn.phase_fine[sgn_idx]*scalers['phs'])*MSMT.CRNG_1MS
                        rv.obs.phs[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine phase:gnss={self.gnss},({sat=},{sgn=})")
                    
                if phase_rate_ok:
                    # Make fine doppler
                    if (src.sgn.phase_rate_fine[sgn_idx] & 0x7fff) != 0x4000:
                        tmp = phase_rate + src.sgn.phase_rate_fine[sgn_idx]*scalers['dpl']
                        rv.obs.dpl[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine doppler:gnss={self.gnss},({sat=},{sgn=})")

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
        for sgn in sgn_map:
            if not len(rv.obs.dpl[sgn]) : del(rv.obs.dpl[sgn])
            if not len(rv.obs.rng[sgn]) : del(rv.obs.rng[sgn])
            if not len(rv.obs.c2n[sgn]) : del(rv.obs.c2n[sgn])
            if not len(rv.obs.phs[sgn]) : del(rv.obs.phs[sgn])
            if not len(rv.obs.ltm[sgn]) : del(rv.obs.ltm[sgn])
            if not len(rv.obs.hca[sgn]) : del(rv.obs.hca[sgn])

               
        return rv

class Subdecoder_RTCM_MSM47():
    '''Implements decoding of RTCM MSM4, MSM5, MSM6, MSM7 messages'''

    def __init__(self, bare_data:bool = False) -> None:
        self.io = SubDecoderInterface('MSM47O', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = set(self.io.io_spec.keys())
        pass
                
    def decode(self, buf:bytes):
        """Process MSM4..MSM7 message"""
        
        msm47 = BareObservablesMSM4567Decoder()
        mnum = msm47.get_msg_num(buf)

        try:
            msm47.decode(buf)
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

        if not msm47.ready:
            return None

        rtype = self.io.io_spec.get(mnum)
        if rtype == BareObservablesMSM4567:
            time = (msm47.bd.hdr.time & 0x7ffffff) if (msm47.gnss == 'R') else msm47.bd.hdr.time
            logger.info(f'Msg {mnum}. Decoding succeeded. t = {time}, sats = {msm47.bd.hdr.sat_mask.bit_count()}.')
            return msm47.bd
        
        try:
            rv = msm47.get_scaled_obs()
        except IndexError as ie:
            logger.error(f"Indexing error in get_scaled_obs() {type(ie)}: {ie}")
            rv = None
        except ArithmeticError as ae:
            logger.error(f"Arithmetic error in get_scaled_obs() {type(ae)}: {ae}")
            rv = None
        except Exception as ex:
            logger.error(f"Undefined error in get_scaled_obs() {type(ex)}: {ex}")
            rv = None
        else:
            logger.info(f'Msg {mnum}. Decoding succeeded. t = {rv.hdr.time}, sats = {len(rv.hdr.sats)}.')

        return rv




