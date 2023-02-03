
[Home](Home.md)

## Command Line arguments

Run decoder with --help key to see command line arguments.

> \>>>py start_decoder.py --help   
>usage: Convert some RTCM files [-h] [-o FORMAT] [-i PATH] [-v] [-ext EXT] SRC [SRC ...]
>
>positional arguments:  
>  **SRC**                              List of source files to be processed   
>options:  
>  -**h**, --**help**                   Show this help message and exit  
>  -o **FORMAT**, --output **FORMAT**   Defines form of representation of output data. Choose from: MARGO | JSON | JSON-B.  
>  -i **PATH**, --ini **PATH**          PATH is a path to configuration file.   
>  -**v**, --**version**                Show program's version number and exit    
>  -ext **EXT**                         Regarded as an extension in RTCM file names.   Default: rtcm3

### SRC [SRC ...]

SRC provides path to the file to be decoded. Multiple files declaration is available - they will be processed one by one,
decoding products will be placed in separate folders. If SRC provides path to the directory, decoder will scan it for RTCM
files and prompt you to select files interactively. By default files with .rtcm3 extension regarded as RTCM files. Use
-ext option to change default.    

### -o, --output

Specifies output format conversion products to be represented in. Select from MARGO/JSON/JSON-B. 'MARGO' used by default.Find description of output formats [here](CommandLineArgs.md).

### -ext EXT

Provides alternative extension for interactive files selection mode.  

### -i PATH / --ini PATH

Provides path to *.ini file. This file may provide some additional options for decoder. Scop of options may be changed during
further decoder development. Check [here](../addons.ini) what do wee have at the moment.

>Notice ! That *.ini file is secondary. There is a defaults.ini file being parsed first. default.ini contains some must-have
parameters and should be placed in the root folder of decoder. It provides information about GLONASS work-point-to-literal
mapping and GPS-to-UTC time shift. File may be edited when default information is out of date.

### -v / --version 

Show decoder version and terminate program.

[Home](Home.md)
 