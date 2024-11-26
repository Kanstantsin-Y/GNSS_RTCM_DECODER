
import os
import json
import gnss_types as gt

from run_conversion import main as convert
from tests.ephemeris_test_samples import EPH_TEST_SCENARIO
from sub_decoders import EphemerisDecoder as ED


def _make_eph_path(base:str, msgNum:int, mode:str) -> tuple[str,str,str]:

    __OFILES = {
            1019:'GPS-EPH-1019.json',
            1020:'GLN-EPH-1020.json',
            1045:'GAL-EPH-1045.json',
            1046:'GAL-EPH-1046.json',
            1044:'QZS-EPH-1044.json',
            1042:'BDS-EPH-1042.json',
            1041:'NAVIC-EPH-1041.json'
        }
    
    fpath, fname = os.path.split(base)
    fname, ext = os.path.splitext(fname)
    odir = '-'.join([fname,mode])
    odir = os.path.join(fpath, odir)
    olog = os.path.join(odir, '-'.join([fname,'log.txt']))
    ofile = __OFILES.get(msgNum)
    ofile = os.path.join(odir, 'EPH', ofile)

    return ofile, odir, olog

def _determin_type(tname:str):

    dtype = None
    match tname:
        case 'GpsLNAV':
            dtype = gt.GpsLNAV
        case 'GloL1L2':
            dtype = gt.GloL1L2
        case 'GalFNAV':
            dtype = gt.GalFNAV
        case 'GalINAV':
            dtype = gt.GalINAV
        case 'BdsD1':
            dtype = gt.BdsD1
        case 'QzssL1':
            dtype = gt.QzssL1
        case 'NavicL5':
            dtype = gt.NavicL5
        
    return dtype


def _test_eph(msgNum:int, mode:str):
    """Convert test data and compare with the reference"""

    ts = EPH_TEST_SCENARIO.get(msgNum)
    tpath = ts[0]
    #cargs = "-o " + mode + ' ' + tpath
    cargs = "-o " + mode + ' -i addons.ini' + ' ' + tpath
    
    ofile, *x = _make_eph_path(tpath, msgNum, mode)
    
    convert(cargs)

    assert os.path.isfile(ofile), f'Output file not found'

    with open(ofile, 'r') as file:
        ephs = json.load(file)

    tp = ephs.pop(0)
    tp = _determin_type(tp['source_type'])
    
    refs = ts[1]
    assert len(ephs) == len(refs), f'Unexpected number of output products: {len(ephs)}.'

    for i,_ in enumerate(ephs):
        ref = refs[i]
        eph = tp(**ephs[i])
        if mode == 'JSON-B':
            eph = ED.scale(eph)
        assert eph.compare(ref,1e-15), f'Product {i} is not equal to reference.'

    return True


def test_eph(msgNum:int, mode:str):

    print(f'-'*80)
    print(f'TESTER: start conversion MSG{msgNum} to {mode}.')
    
    ret = False
    
    if not msgNum in EPH_TEST_SCENARIO.keys():
        print(f'TESTER: no test data for MSG{msgNum}')
        return ret
    
    if not mode in ('JSON', 'JSON-B'):
        print(f'TESTER: format {mode} is not supported in this test')
        return ret
    
    try:
        ret =_test_eph(msgNum, mode)
        print(f'TESTER: status SUCCEED.')
    except AssertionError as asrt:
        print(f'TESTER: status FAILED. {asrt.args[0]}')
    except Exception as expt:
        print(f'TESTER: status FAILED. Unexpected error')
    finally:
        return ret
        


if __name__ == '__main__':

    summary = True
    print(f'Start ephemeris test procedure.')

    summary = []
    summary.append( test_eph(1019, 'JSON') )
    summary.append( test_eph(1020, 'JSON') )
    summary.append( test_eph(1041, 'JSON') )
    summary.append( test_eph(1042, 'JSON') )
    summary.append( test_eph(1046, 'JSON') )

    summary.append( test_eph(1019, 'JSON-B') )
    summary.append( test_eph(1020, 'JSON-B') )
    summary.append( test_eph(1041, 'JSON-B') )
    summary.append( test_eph(1042, 'JSON-B') )
    summary.append( test_eph(1046, 'JSON-B') )
    
    print(f'-'*80)
    summary = 'FAILED' if False in summary else 'SUCCEED'
    print(f'End ephemeris test procedure. Final result: {summary}')
