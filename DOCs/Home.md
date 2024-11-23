

### GNSS_RTCM_DECODER

This project implements a tool for binary RTCM data unpacking and conversion into textual representation. Main purpose - representation of GNSS data in readable, editable form convenient for further manual or automated analysis and geodetic computations. Run **main.py** with command line arguments to do conversion. See [this](CommandLineArgs.md) file for details of command line interface. Function **main.main(args:str)** can be called from external python module as an alternative way of launching conversion.

### VERSIONS & FEATURES

2023-02-03. Version 1.01 available at the moment.Features:

- **Input**. Accepts binary RTCM file as input. Supports processing of RTCM messages from MSM subset (MSM1..MSM7). Message numbers 1077 to 1131.
- **Output**. Three modes of data representation available: MARGO, JSON, JSON-B. Find more information [here](OutputFormats.md) about output formats. Briefly
 1. MARGO - textual, CSV-like representation of observables. Can be opened by any CSV compatible editor (Excel, Matlab, etc.)
 2. JSON - content of RTCM message represented as a dictionary and saved as JSON object. Observables are in floating-point form, scaled and ready for use. Auxiliary information from MSM header available.
 3. JSON-B - same as JSON but represents bare integer data as it is transmitted in RTCM MSM message.
- **Interface**. Accepts some control parameters via command line arguments and/or *.ini file. File defaults.ini is mandatory. It provides some mandatory data required for conversion. An additional *.ini file may be provided to converter via command line. This file brings to user some control over converter behavior. Multi-file conversion available. See [description](CommandLineArgs.md) for details.
- **Logging**. Besides conversion products a textual log file generated. Provides information about conversion progress, errors and warnings.


### Some notes about project implementation

- Scalability. Source format - RTCM - implements plenty of messages having different purpose, content, format and transmission rules. On the other hand, there may be plenty of output data formats implementing different styles of representation of GNSS data. Depending of the post-processing aims user may be interested in bare integer data ("as it is" in RTCM message), proprietary format like RINEX, CSV representation for easy read and analysis or smth. else. So, the idea is to represent a conversion tool as a set of:
    - Sub-decoders, responsible for different subsets of RTCM scope (Legacy, MSM, SSR and so on).
    - Sub-printers, responsible for different styles of output data representation.  
    Scalability here means that software architecture and implementation provides an easy way to add a new sub-decoder or sub-printer. See [this](PrintersAndDecoders.md) file for details, about available printers and sub-decoders. A set of printers and sub-decoders combined in one item implements converter with concrete properties. As mentioned above there are three different converter implementations available in initial version 1.01. [Here](ConverterArch.md) is a class diagram introducing main idea of converter architecture.
- Low memory consumption. Input file processed in chunk-by-chunk manner, thus even big files will not cause any memory violation issues.
- Robust binary data decoder. Primary RTCM decoder implements extraction of RTCM messages from input byte flow. Supports processing of unaligned files, having data gaps or alien garbage. Anomalies in input byte flow reported via the logger. May be easily modified to process real time byte flow from COM port, socket, etc.
- Dual channel logger. Provides sending of service information to file and to console in parallel. Message severity levels could be configured individually.


## Key words.

- RTCM - Radio Technical Commission for Maritime Services - special committee developing 
RTCM STANDARD 10403.x.

- RTCM STANDARD 10403.x - A document describing special data format widely used in GNSS
and GNSS-related applications. RTCM format specifies a set of binary messages used for transmission and storage of GNSS related data (range measurements, corrections, ephemeris, auxiliary data and so on).

- GNSS - Global Navigation Satellite System.

- Legacy messages - Primary subset of RTCM messages developed for representation of various
types of GNSS data and suitable for GPS and GLONASS navigation systems.

- MSM - Relatively new subset of RTCM messages developed for representation of various types of GNSS data.
Unlike legacy messages, MSM subset covers all GNSS systems and signals available at the moment,
allows multiple signal representation. Implements different subsets of messages (MSM1, MSM2,.. MSM7)
to satisfy requirements of different GNSS applications. MSM1 - the most compact form, introduces some limitations.
MSM7 - most overall form with better accuracy. 
