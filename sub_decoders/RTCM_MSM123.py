
#--- Dependencies -------------------------------------------------------------------------

from math import isnan

from data_types.observables import ObservablesMSM
from data_types.observables import BareObservablesMSM123

from decoder_top import SubDecoderInterface
from utilities.RTCM_utilities import MSMT

from utilities.bits import Bits
from utilities.bits import ExceptionBitsError
from utilities.bits import catch_bits_exceptions

from logger import LOGGER_CF as logger


#--- Exceptions ----------------------------------------------------------------------------------

class ExceptionBareDataStructure(Exception):
    '''Hook error in BareObservablesMSM4567Decoder methods'''

#------------------------------------------------------------------------------------------------
    
class BareObservablesMSM123Decoder(Bits):
    '''Methods to extract bare data from MSM123 message'''
    
    __MIN_HDR_LEN = 169
    
    __SCALERS = {
        'rng':(2**-24),               #DF400
        'phs':(2**-29),               #DF401
        'dpl':0.0001,                 #DF404
        'ltm':MSMT.unpack_tlock4,     #DF402
        'c2n':1                       #DF403
    }
   
    __BIT_WIDTH_3 = (10, 15, 22, 4, 1)
    __BIT_WIDTH_2 = (10,     22, 4, 1)
    __BIT_WIDTH_1 = (10, 15)

    def __init__(self) -> None:
        super().__init__()

        self.bd = BareObservablesMSM123()
        self.subset = ''
        self.gnss = ''
        self.ready = False

    def decode(self, buf:bytes):

        self.bd.clear()
        self.ready = False

        mnum = self.get_msg_num(buf)
        gnss, subset = MSMT.msm_subset(mnum)

        if not subset in ('MSM1', 'MSM2', 'MSM3'):
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

        offset = self.__extract_observables123(buf, offset)
        self.ready = True
        return
    
    @catch_bits_exceptions
    def get_msg_num(self, buf: bytes)->bool:
        return self.getbitu(buf, 24, 12)
    
    def is_msm1(self)->bool:
        return self.subset == "MSM1" 

    def is_msm2(self)->bool:
        return self.subset == "MSM2"

    def is_msm3(self)->bool:
        return self.subset == "MSM3"

    def is_msm123(self)->bool:
        return self.is_msm1() or self.is_msm2() or self.is_msm3()

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

    def __extract_observables123(self, buf:bytes, offset:int)->int:
        '''Unpack MSM4 and MSM5 data fields'''

        Nsat = self.bd.hdr.sat_mask.bit_count()
        Nsgn = self.bd.hdr.sgn_mask.bit_count()
        Ncell = self.bd.hdr.cell_mask.bit_count()

        if (Nsat == 0) or (Nsgn == 0) or (Ncell == 0):
            raise ExceptionBareDataStructure(f'MSM hdr4: {Nsat=}, {Nsgn=}, {Ncell=}')
        
        # Check message length
        if self.is_msm1():
            est_len = ((offset + 10*Nsat + 15*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_1)
        elif self.is_msm2():
            est_len = ((offset + 10*Nsat + 28*Ncell + 7)>>3) + 3
            bw = (b for b in self.__BIT_WIDTH_2)
        elif self.is_msm3():
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
        if self.is_msm1():
            bits = next(bw)
            self.bd.sgn.rng_fine = tuple((self.getbits(buf, offset+i*bits, bits) for i in range(0,Ncell)))
            offset += bits*Ncell
        else:
            if self.is_msm3():
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

    def get_bare_obs(self)->BareObservablesMSM123:
        '''Returns bare (integer) unscaled data extracted from MSM1, MSM2, MSM3 messages'''
        return self.bd

    def get_scaled_obs(self)->ObservablesMSM:
        '''Converts bare data into IRTCM.Observables form.'''
        
        # Create empty data class
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
            rv.hdr.signals = {}
            return rv

        # Make list of satellites
        sat_list = tuple((i+1 for i in range(0,64) if (src.hdr.sat_mask & (1<<i))))
        sat_num = len(sat_list)
        rv.hdr.sats = sat_list

        # Make list of signals
        sgn_map = (i+1 for i in range(0,32) if (src.hdr.sgn_mask & (1<<i)))
        sgn_map = tuple((MSMT.rnx_lit(self.gnss, s) for s in sgn_map))
        rv.hdr.signals = {s:MSMT.crr_frq(self.gnss, s) for s in sgn_map}

        # Calc. number of frequency bins per sat.
        M = src.hdr.sgn_mask.bit_count()
        mask = (1<<M)-1
        slots_per_sat = tuple((((src.hdr.cell_mask >> M*i) & mask) for i in range(0,sat_num)))
        
        scalers = self.__SCALERS
        
        # Create frequency slots in output structure
        # Add empty dictionary for each frequency slot
        for sgn in sgn_map:
            rv.obs.rng.update({sgn:{}})
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
            
            rng = float(src.sat.rng_rough[sat_idx])/1024.0
            rng_ok = self.is_msm1() or self.is_msm3()
            ph_ok = self.is_msm2() or self.is_msm3()
            
            # Pass through signals of satellite 'sat'
            i = 0
            while slots:
                
                # sgn - RINEX literal - code of signal
                sgn = sgn_map[i]
                i += 1
                slotExist = slots & 0x01
                slots = slots >> 1
    
                if (slotExist == 0):
                    continue

                # Make fine code range
                if rng_ok:
                    if (src.sgn.rng_fine[sgn_idx] & 0x7fff) != 0x4000:
                        tmp = (rng + src.sgn.rng_fine[sgn_idx]*scalers['rng'])*MSMT.CRNG_1MS
                        rv.obs.rng[sgn].update({sat:tmp})
                    else:
                        logger.info(f"No fine range:gnss={self.gnss},({sat=},{sgn=})")
                        ph_ok = False

                # Make fine phase range
                if ph_ok:
                    if (src.sgn.phase_fine[sgn_idx] & 0x3fffff) == 0x200000:
                        logger.info(f"No fine phase:gnss={self.gnss},({sat=},{sgn=})")
                    else:
                        tmp = (rng + src.sgn.phase_fine[sgn_idx]*scalers['phs'])*MSMT.CRNG_1MS
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
        for sgn in sgn_map:
            if not len(rv.obs.rng[sgn]) : del(rv.obs.rng[sgn])
            if not len(rv.obs.phs[sgn]) : del(rv.obs.phs[sgn])
            if not len(rv.obs.ltm[sgn]) : del(rv.obs.ltm[sgn])
            if not len(rv.obs.hca[sgn]) : del(rv.obs.hca[sgn])

               
        return rv

class SubdecoderMSM123():
    '''Implements decoding of RTCM MSM1, MSM2, MSM3'''

    def __init__(self, bare_data:bool = False) -> None:
        self.io = SubDecoderInterface('MSM13O', bare_data)
        self.io.decode = self.decode
        self.io.actual_messages = set(self.io.io_spec.keys())
        pass
                
    def decode(self, buf:bytes):
        """Process MSM1..MSM3 message"""
        
        msm123 = BareObservablesMSM123Decoder()
        mnum = msm123.get_msg_num(buf)

        try:
            msm123.decode(buf)
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

        if not msm123.ready:
            return None

        rtype = self.io.io_spec.get(mnum)
        if rtype == BareObservablesMSM123:
            time = (msm123.bd.hdr.time & 0x7ffffff) if (msm123.gnss == 'R') else msm123.bd.hdr.time
            logger.info(f'Msg {mnum}. Decoding succeeded. t = {time}, sats = {msm123.bd.hdr.sat_mask.bit_count()}.')
            return msm123.bd
        
        try:
            rv = msm123.get_scaled_obs()
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
