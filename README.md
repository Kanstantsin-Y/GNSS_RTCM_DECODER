

### GNSS_RTCM_DECODER

This project implements a tool for binary RTCM data unpacking and conversion into textual representation. Main purpose - representation of GNSS data in readable, editable form convenient for further manual or automated analysis and geodetic computations. Run **main.py** with command line arguments to start conversion. See 


###






### Main features

- Extendable architecture. Source format - RTCM - implements plenty of messages having different purpose, content, format and transmission rules. On the other hand, there may be plenty of output data formats implementing different styles of representation of GNSS data. Depending of the post-processing aims user may be interested in bare integer data ("as it is" in RTCM message), proprietary format like RINEX, CSV representation for easy read and analysis or smth. else. So, the idea is to represent a conversion tool as a set of:
    - Sub-decoders, responsible for different subsets of RTCM scope (Legacy, MSM, SSR and so on).
    - Printers, responsible for different styles of output data representation.

    Extendability here means that software architecture and implementation provides an easy way to add a new sub-decoder or printer.
    Check [this](DOCs/PrintersAndDecoders.md) for details, about available printers and decoders.

- Low memory consumption. Input file processed in chunk-by-chunk manner, thus even big files will not cause any memory violation issues.
- Robust binary data decoder. Primary RTCM decoder implements extraction of RTCM messages from input byte flow. Supports processing of files started with unaligned message, having data gaps or alien garbage. Anomalies in input byte flow reported via the logger. May be easily modified to process real time byte flow from COM port, socket, etc.
- Dual channel logger. Provides sending of service information to file and to console in parallel. Message severity levels could be configured individually.
- User interface implemented via command line options + .ini file parameters. There is one mandatory .ini file - contains some 'mast have' parameters for proper decoder operation and one additional file, which can be referenced from the command prompt to provide some additional settings.


Run **start_decoder.py** to decode RTCM file. Check [this](DOCs/CommandLineArgs.md) for command line arguments.


