
"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    
    This file is a top module of a project. Use main.main(argv) to launch RTCM converter.
    This module:
    - implements command line interface;
    - scans configuration files for user defined controls;
    - provides method to convert RTCM file(s) into textual format file(s).
"""

import os
import shutil
import glob

from logger import LOGGER_CF as logger
from controls import ConverterControls
from argparse import ArgumentParser as ArgParser
from converter_top import ConverterFactory, ConverterInterface

VERSION = "1.20"
DEFAULT_CONFIG = "defaults.ini"
FILE_CHUNCK_LEN: int = 2**12 
ARGS = None

#.......................................................................................................               

def create_work_folder(src_file_path: str, postfix: str) -> str | None:
    """ Create a new folder for decoding products.
    If folder already exists - delete content. 
    Return path to the folder if everything OK.
    Else return None."""
        
    fld, ext = os.path.splitext(src_file_path)
    fld = fld + '-' + postfix
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
        print(f'Created work folder.')
        return fld
    except OSError as oe:
        print(f"Work folder wasn't created")
        print(f"{type(oe)}: {oe}")
        return None

#.......................................................................................................               

def make_log_file_name(src_file_path: str):
    """Make name for log file. Based on source file name."""

    fpath, fname = os.path.split(src_file_path)
    fname, ext = os.path.splitext(fname)

    return fname + '-log.txt'

#.......................................................................................................               

def init_logger(path: str):
    """Create log file and init logger."""
        
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
        welcome_msg = f"New log file was created."
        log.write(welcome_msg+'\n')
        log.write('-'*len(welcome_msg)+'\n')
        log.close()
        print(welcome_msg)
        #Init logger. Opens file 'path' in append mode
        logger.init_2CH(path, 'RTCMDEC')

#.......................................................................................................               

def decode_rtcm_file(fpath: str, converter: ConverterInterface)->bool:
    
    try:
        f = open(fpath,'rb')

        logger.info(f'Opened file {fpath}.')
        file_size = os.path.getsize(fpath)
        bytes_processed = 0
        
        chunk = f.read(FILE_CHUNCK_LEN)
        while len(chunk):
                        
            bytes_processed += len(chunk)
            rtcm3_lines = converter.parse_bytes(chunk)
            
            for msg in rtcm3_lines:
                xblock = converter.decode(msg)
                if xblock != None:
                    converter.print(xblock)

            aux_data = converter.get_statistics()
            logger.progress('{0:2.2%}, {1:d} messages, prs-dec-prnt errors {2:d}-{3:d}-{4:d}.'.format(
                            float(bytes_processed)/float(file_size),
                            aux_data.decoding_attempts,
                            aux_data.parsing_errors,
                            aux_data.decoding_errors,
                            aux_data.printing_errors ))
            
            chunk = f.read(FILE_CHUNCK_LEN)
    
    except KeyboardInterrupt:
        logger.error(f"Processing terminated by the user.")
        return False
    except FileNotFoundError as fe:
        logger.error(f"Got FileNotFoundError exception.")
        logger.error(f"{type(fe)}: {fe}")
        return False
    except Exception as ex:
        logger.error(f"Got unexpected exception.")
        logger.error(f"{type(ex)}: {ex}")
        return False
    finally:
        converter.release()
            
        if f:
            logger.info(f"Closing file {fpath}.")
            f.close()
        else:
            logger.info(f"Source file {fpath} wasn't opened.")

    return True

#.......................................................................................................               

def create_argument_parser(description: str = 'No description') -> ArgParser:
    """ Setup argument parser.
    See https://docs.python.org/3/library/argparse.html#module-argparse for help.
    """
    arg_parser = ArgParser(description)
    
    # Arbitrary argument: output format.
    arg_parser.add_argument (
        '-o','--output',
        dest ='format',
        metavar ='FORMAT',
        type = str,
        action = 'store',
        default = 'MARGO',
        choices = ['MARGO', 'JSON', 'JSON-B'],
        help = 'FORMAT defines form of representation of output data. Choose from: MARGO | JSON | JSON-B.'
    )
    # Arbitrary argument: configuration file.
    arg_parser.add_argument (
        '-i','--ini',
        dest ='ini_file',
        metavar ='PATH',
        type = str,
        action = 'store',
        default = None,
        help = 'PATH is a path to configuration file.'
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

    return arg_parser

#.......................................................................................................               

def make_list_of_source_files(f_arguments: list[str], rtcm_ext: str='rtcm3') -> list[str]:
    """ Create list of source  files.
    Implements formal check of files listed in f_arguments.
    Implements interactive interface if 'f_arguments' specifies directory."""

    # Make list of source files to be processed
    # Two scenarios:
    # 1. Files listed directly in f_arguments.
    # 2. Source folder specified in f_arguments. Folder should be scanned and
    #    list of source files should be specified interactively.    
    
    # Check, weather f_arguments specifies directory.  
    src_is_dir = False
    if len(f_arguments) == 1:
        path = os.path.abspath(f_arguments[0])
        src_is_dir = (not os.path.isfile(path)) and os.path.isdir(path)

    files = []
    # If not directory, check files in args.source
    # for consistency and fill list of files.
    if not src_is_dir:
        for path in f_arguments:
            full_path = os.path.abspath(path)
            if (os.path.isfile(full_path)):
                files.append(full_path)
            else:
                print(f"{full_path} is not a file.")
    # If f_arguments[0] is a directory, interact with the user.
    else:
        fpattern = '.'.join(['*',rtcm_ext])
        path = os.path.abspath(f_arguments[0])
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
    
    return files

#.......................................................................................................               

def main(local_args: str|None = None)-> None:

    ctrl_strg = ConverterControls()
    ctrl_strg.init_from_file(DEFAULT_CONFIG)
    boxed_controls = ctrl_strg.boxed_controls

    #Parse arguments
    arg_parser = create_argument_parser("Convert some RTCM files")
    if local_args==None:
        # Parse command prompt args.
        args = arg_parser.parse_args()
    else:
        # Parse explicitly defined args.
        args = arg_parser.parse_args(local_args.split(' '))
    
    # Process additional controls
    if args.ini_file != None:
        ctrl_strg.update_from_file(args.ini_file)
        print(args.ini_file)
        boxed_controls = ctrl_strg.boxed_controls

    files = make_list_of_source_files(args.source, args.rtcm_ext)

    output_format = args.format

    for fpath in files:
        
        print("-"*80)
        print(f"Started decoding: {fpath}")

        # Create work folder. Work folder will have the same name as source file.
        # There would be an empty text file in it to log decoding process.
        wfld = create_work_folder(fpath, output_format)
        if not wfld:
            continue

        # Init logger
        lfile = os.path.join(wfld,make_log_file_name(fpath))
        init_logger(lfile)

        # Create converter.
        cf = ConverterFactory(output_format)
        converter = cf(wfld, boxed_controls)
        if not converter:
            logger.error(f"Conversion aborted.")
            logger.deinit()
            continue

        if decode_rtcm_file(fpath, converter):
            err = converter.get_statistics()
            if err.printing_errors or err.decoding_errors or err.printing_errors:
                logger.progress("Finished with errors.")
            else:
                logger.progress("Finished without errors.")
        else:
            logger.error("Decoding was terminated.")

        logger.deinit()

    pass




if __name__ == '__main__':
    
    main(ARGS)
