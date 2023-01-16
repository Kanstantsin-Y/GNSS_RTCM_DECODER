
import os
import shutil
import argparse
import glob

from cons_file_logger import LOGGER_CF as logger

from RTCM_decoder import DecoderTop as RtcmDecoderTop
from sub_decoders.RTCM_MSM import Subdecoder_RTCM_MSM47

from printer_top import PrinterTop
from margo_printer import MargoControls, MSMtoMARGO
from controls import BoxWithDecoderControls, DecoderControls

VERSION = "1.01"
DEFAULT_CONFIG = "decode_file.ini"

#..............................................................................               

def create_work_folder(src_file_path) -> str | None:
    '''
    Create a new folder for decoding products.
    If folder alraedy exists - delete content. 
    Return path to the folder if everything OK.
    Else return None.
    '''
        
    fld, ext = os.path.splitext(src_file_path)

    # Remove directory, if exists
    if os.path.isdir(fld):
        try:
            shutil.rmtree(fld)
        except OSError as oe:
            print(f"There was an error during directory deletion.")
            print(f"{type(oe)}: {oe}")
            return None
    
    # Create new empty directory
    try:
        os.makedirs(fld)
        print(f'Craeted work folder.')
    except OSError as oe:
        print(f"Work folder wasn't created")
        print(f"{type(oe)}: {oe}")
        return None
    else:
        return fld

#..............................................................................               

def make_log_file_name(src_file_path):
    '''Make name for log file. Based on source file name.'''

    fpath, fname = os.path.split(src_file_path)
    fname, ext = os.path.splitext(fname)

    return fname + '-log.txt'

#..............................................................................               

def init_logger(path):
    '''Create log file and init logger'''
        
    try:
        log = open(path,'w')
    except OSError as er:
        print(f"Failed to create log file." )
        print(f"{type(er)}: {er}")
    except:
        print(f"Undefined error in 'init_logger()'.")
        print(f"{type(er)}: {er}")
    else:
        #Initial record
        welcom_msg = f"New log file was created."
        log.write(welcom_msg+'\n')
        log.write('-'*len(welcom_msg)+'\n')
        log.close()
        print(welcom_msg)
        #Init logger. Opens file 'path' in append mode
        logger.init_2CH(path, 'RTCMDEC')

#..............................................................................               


def decode_rtcm_file(fpath: str, boxed_controls: BoxWithDecoderControls = None)->bool:

    rv = False

    if not os.path.isfile(fpath):
        print(f"Source file '{fpath}' not found.")
        return rv

    # Create work folder. Work folder will have the same name as source file.
    # There would be an empty text file in it to log decoding process.
    wfld = create_work_folder(fpath)
    if not wfld:
        return rv

    lfile = wfld + '//' + make_log_file_name(fpath)
    init_logger(lfile)

    # Init RTCM decoder and add subdecoders.
    main_rtcm_decoder = RtcmDecoderTop()
    msm47 = Subdecoder_RTCM_MSM47(bare_data=False)
    main_rtcm_decoder.register_decoder(msm47)

    # Use embedded defaults if there are no controls from caller.
    user_ctrls = boxed_controls.MARGO if boxed_controls != None else None
    
    # Implement printers
    main_margo_printer = PrinterTop('MARGO')
    msm47_to_margo = MSMtoMARGO(wfld, user_ctrls)
    if not main_margo_printer.register_printer(msm47_to_margo):
        logger.error(f"Sub-printer 'MSMtoMARGO' wasn't registered")

    if not main_margo_printer.ready:
        logger.error(f"Printer {main_margo_printer.format} wasn't created")
        logger.deinit()
        return
    
    try:
        f = open(fpath,'rb')

        logger.info(f'Opened file {fpath}.')
        file_size = os.path.getsize(fpath)
        bytes_processed = 0
        
        chunk = f.read(2**12)
        while len(chunk):
                        
            bytes_processed += len(chunk)
            rtcm3_lines = main_rtcm_decoder.catch_message(chunk)
            
            for msg in rtcm3_lines:
                xblock = main_rtcm_decoder.decode(msg)
                main_margo_printer.print(xblock)

            logger.console('Progress: {0:2.2%} bytes, {1:d} messages, {2:d} p-errors, {3:d} d-errors'.format(
                            float(bytes_processed)/float(file_size),
                            main_rtcm_decoder.dec_attempts,
                            main_rtcm_decoder.parce_errors,
                            main_rtcm_decoder.dec_errors ))
            
            chunk = f.read(2**12)
    
        # self._save_some_test_data(rtcm3_lines)
    
    except KeyboardInterrupt:
        logger.error(f"Processing terminated by user.")
    except FileNotFoundError as fe:
        logger.error(f"Got FileNotFoundError exception.")
        logger.error(f"{type(fe)}: {fe}")
    except Exception as ex:
        logger.error(f"Got unexpected exception.")
        logger.error(f"{type(ex)}: {ex}")
    else:
        rv = True
    finally:        
        if f:
            logger.info(f"Closing file {fpath}.")
            f.close()
        else:
            logger.info(f"Source file {fpath} wasn't opened.")

        main_margo_printer.close()
        logger.deinit()

    return rv



# astr = r"-c cfg.jsn RTCM3_TEST_DATA\H7-A2.rtcm3 RTCM3_TEST_DATA\H7-A3.rtcm3 RTCM3_TEST_DATA\\"
# ARGS = r"-c cfg.json RTCM3_TEST_DATA\\"
# ARGS = r"-c cfg.json RTCM3_TEST_DATA\H7-A2.rtcm3 RTCM3_TEST_DATA\reference-3msg.rtcm3 RTCM3_TEST_DATA\\"
ARGS = r"-i RTCM3_TEST_DATA\enable_HCA_and_TLOCK.ini RTCM3_TEST_DATA\reference-3msg.rtcm3"
# ARGS = None    

if __name__ == '__main__':

    ctrl_strg = DecoderControls()
    ctrl_strg.init_from_file(DEFAULT_CONFIG)
    boxed_controls = ctrl_strg.boxed_controls

    # sys.exit()

    #Setup argument parser. See https://docs.python.org/3/library/argparse.html#module-argparse for help
    arg_parser = argparse.ArgumentParser(description='Convert some RTCM files.')
    # Arbitrary argument: configuration file.
    arg_parser.add_argument (
        '-i','--ini',
        dest ='ini_file',
        metavar ='PATH',
        type = str,
        action = 'store',
        default = None,
        help = 'PATH is a path to configuration file. Default: %(prog)s.ini'
    )
    # Mandatory argument: list of source files or source directory.
    arg_parser.add_argument (
        'source',
        metavar = 'SRC',
        type = str,
        nargs = '+',
        help = 'List of source files to be processed'
    )
    # Arbitrary argument (action): show version.
    arg_parser.add_argument (
        '-v','--version',
        dest = 'ver',
        action = 'version',
        version = '%(prog)s ver. '+VERSION
    )
    # Arbitrary argument 'extension'. Files with extension 'rtcm_ext' are RTCM files. 
    arg_parser.add_argument (
        '-ext',
        dest = 'rtcm_ext',
        action = 'store',
        default = 'rtcm3',
        metavar = 'EXT',
        help = 'EXT regarded as an extension in RTCM file names. Default: rtcm3'
    )

    #Parse arguments
    if ARGS==None:
        args = arg_parser.parse_args()
    else:
        args = arg_parser.parse_args(ARGS.split(' '))
    
    # Process additional controls
    if args.ini_file != None:
        ctrl_strg.update_from_file(args.ini_file)
        print(args.ini_file)
        boxed_controls = ctrl_strg.boxed_controls

    # Make list of source files to be processed
    # Two scenarios:
    # 1. Files listed directly in args.source.
    # 2. Source folder specified in args.source. Folder should be scanned and
    #    list of source files should be specified interactively.    
    
    # Check, weather args.source is directory  
    src_is_dir = False
    if len(args.source) == 1:
        path = os.path.abspath(args.source[0])
        src_is_dir = (not os.path.isfile(path)) and os.path.isdir(path)

    files = []
    # If not directory, check files in args.source
    # for consistency and fill list of files.
    if not src_is_dir:
        for path in args.source:
            full_path = os.path.abspath(path)
            if (os.path.isfile(full_path)):
                files.append(full_path)
            else:
                print(f"{full_path} is not file.")
    # If args.source[0] is directory interact with user.
    else:
        fpattern = '.'.join(['*',args.rtcm_ext])
        path = os.path.abspath(args.source[0])
        pattern = os.path.join(path,fpattern)
        # Find files matching pattern
        dir = glob.glob(pattern)
        if not len(dir):
            print(f"There are no files matching {fpattern} in {path}.")
        else:
            print(f"Found {len(dir)} files matching {fpattern} pattern:")
            for idx,src in enumerate(dir,start=1):
                print(f"{idx:2d} : {src.__repr__()}") 
            
            idx = input("Please, select source files (use indexes and spaces):").split(' ')
            try:
                idx = [int(i)-1 for i in idx if 0 < int(i) <= len(dir)]
            except ValueError:
                print("Incorrect input. Use space separated indexes.")
            else:
                files = [dir[i] for i in idx]


    for file in files:
        print("-"*80)
        print(f"Started decoding: {file}")
        if decode_rtcm_file(file, boxed_controls):
            print("Finished successfuly.")
        else:
            print("Decoding was terminated.")

    pass