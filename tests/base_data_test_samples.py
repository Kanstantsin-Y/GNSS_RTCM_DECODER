

import os
import json
import gnss_types as gt

from dataclasses import asdict
from run_conversion import main as convert
from sub_decoders import BaseStationDataDecoder as BSDD
from printers import PrintJSON as PJ


__all__ = ['test_base_message']

BASE_TEST_SCENARIO = {
    1005 : [r'RTCM3_TEST_DATA\BASE\msg1005.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\RefPoint-1005.json'],
    1006 : [r'RTCM3_TEST_DATA\BASE\msg1006.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\RefPointHeight-1006.json'],
    1007 : [r'RTCM3_TEST_DATA\BASE\msg1007.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\AntDesc-1007.json'],
    1029 : [r'RTCM3_TEST_DATA\BASE\msg1029.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\TextStr-1029.json'],
    1033 : [r'RTCM3_TEST_DATA\BASE\msg1033.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\AntAndRcvDesc-1033.json'],
    1230 : [r'RTCM3_TEST_DATA\BASE\msg1230.rtcm3', r'RTCM3_TEST_DATA\BASE\REF\GloBias-1230.json']
    }

    # 1008 : 'AntDescSer-1008.json',
    # 1013 : 'SysPar-1013.json',

def make_1029():

    # an example from the standard spec.
    bts = [ 0xD3, 0x00, 0x27, 0x40, 0x50, 0x17, 0x00, 0x84,
            0x73, 0x6E, 0x15, 0x1E, 0x55, 0x54, 0x46, 0x2D,
            0x38, 0x20, 0xD0, 0xBF, 0xD1, 0x80, 0xD0, 0xBE,
            0xD0, 0xB2, 0xD0, 0xB5, 0xD1, 0x80, 0xD0, 0xBA,
            0xD0, 0xB0, 0x20, 0x77, 0xC3, 0xB6, 0x72, 0x74,
            0x65, 0x72, 0xED, 0xA3, 0x3B ]

    bts = bytes(bts)
    f = open('msg1029.rtcm3','wb')
    f.write(bts)
    f.close()
        
def __test_compare_method1(N:int=0):

    C = gt.BaseSP()
    C.Nm = 2
    C.shedule.append(gt.BaseSPitem(1001,1,10)) 
    C.shedule.append(gt.BaseSPitem(1009,1,10))

    D = C.deepcopy()
    match N:
        case 0:
            pass
        case 1:
            D.Nm = 1
        case 2:
            D.shedule[0].period = 15
        case 3:
            A = gt.BaseAD(descr = 'Ant1')
            D.shedule[0] = A

    cmp = D.compare(C)
    if cmp:
        print(f'Case {N}: Equal')
    else:
        print(f'Case {N}: Not Equal')

    pass

def __test_compare_method2(N:int=0):
    
    C = gt.BaseSP()
    C.Nm = 2
    C.shedule.update( {1001:(1,10)} ) 
    C.shedule.update( {1009:(1,10)} )

    D = C.deepcopy()
    match N:
        case 0:
            pass
        case 1:
            D.Nm = 1
        case 2:
            D.shedule[1001] = (1,15)
        case 3:
            A = gt.BaseAD(descr = 'Ant1')
            D.shedule[1001] = A

    cmp = D.compare(C)
    if cmp:
        print(f'Case {N}: Equal')
    else:
        print(f'Case {N}: Not Equal')

    pass

def test_compare_method():

    # __test_compare_method1(0)
    # __test_compare_method1(1)
    # __test_compare_method1(2)
    # __test_compare_method1(3)

    __test_compare_method2(0)
    __test_compare_method2(1)
    __test_compare_method2(2)
    __test_compare_method2(3)


def try_base_messages():

    A = gt.BaseAD(descr = 'Ant1')
    B = A.copy()
    A.descr = 'Ant2'
    B.descr = 'Ant3'

    print (B.descr)
    print (A.descr)

    C = gt.BaseSP()
    C.Nm = 1
    C.shedule.append(gt.BaseSPitem(1001,1,10)) 
    C.shedule.append(gt.BaseSPitem(1009,1,10))

    D = asdict(C)

    D = C.deepcopy()
    D.shedule[0] = A
    
    cmp = D.compare(C)
    pass


def _determin_type(tname:str):
    """Returns data class by the textual name of data class."""
    
    assert tname in gt.__dict__.keys(), f'Product type is absent in the module "gnss_types"'
    return gt.__dict__.get(tname)

    
def _test_base(msgNum:int, mode:str):
    """Convert test data and compare with the reference"""

    ts = BASE_TEST_SCENARIO.get(msgNum)
    tpath = ts[0]
    
    cargs = "-o " + mode + ' ' + tpath
    #cargs = "-o " + mode + ' -i addons.ini' + ' ' + tpath

    convert(cargs)

    ofile, *x = PJ.make_opath(tpath, msgNum, mode)
    
    assert os.path.isfile(ofile), f'Output file not found'

    with open(ofile, 'r', encoding='utf-8') as file:
        baseMsgs = json.load(file)

    tp = baseMsgs.pop(0)
    tp = _determin_type(tp['source_type'])
    
    rfile = ts[1]
    assert os.path.isfile(rfile), f'Reference file not found'
    with open(rfile, 'r', encoding='utf-8') as file2:
        refMsgs = json.load(file2)

    ref_tp = refMsgs.pop(0)
    ref_tp = _determin_type(ref_tp['source_type'])
    
    assert ref_tp == tp, f'Unexpected type of output product: {tp.__name__}.'
    assert len(baseMsgs) == len(refMsgs), f'Unexpected number of output products: {len(baseMsgs)}.'

    for i,_ in enumerate(baseMsgs):
        base = tp(**baseMsgs[i])
        ref = tp(**refMsgs[i])
        if mode == 'JSON-B':
            base = BSDD.scale(base)
        assert base.compare(ref,1e-15), f'Product {i} is not equal to reference.'

    return True


def test_base_message(msgNum:int, mode:str):

    print(f'-'*80)
    print(f'TESTER: start conversion MSG{msgNum} to {mode}.')
    
    ret = False
    
    if not msgNum in BASE_TEST_SCENARIO.keys():
        print(f'TESTER: no test data for MSG{msgNum}')
        return ret
    
    if not mode in ('JSON', 'JSON-B'):
        print(f'TESTER: format {mode} is not supported in this test')
        return ret
    
    try:
        ret =_test_base(msgNum, mode)
        print(f'TESTER: status SUCCEED.')
    except AssertionError as asrt:
        print(f'TESTER: status FAILED. {asrt.args[0]}')
    except Exception as expt:
        print(f'TESTER: status FAILED. Unexpected error')
    finally:
        return ret
    


