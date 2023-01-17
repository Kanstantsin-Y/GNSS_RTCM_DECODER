
## Key words.

- RTCM - Radio Technical Commission for Maritime Services - special committee developing 
RTCM STANDARD 10403.x.

- RTCM STANDARD 10403.x - A document describing special data format widely used in GNSS
and GNSS-related applications. RTCM format specifies a set of binary messages used for transmission and storage of GNSS related data (range measurements, corrections, ephemerids, auxiliary data and so on).

- GNSS - Global Navigation Satellite System.

- Legacy messages - Primary subset of RTCM messages developed for representation of various
types of GNSS data and suitable for GPS and GLONASS navigation systems.

- MSM - Relatively new subset of RTCM messages developed for representation various types of GNSS data.
Unlike legacy messages, MSM subset covers all GNSS systems and signals available at the moment,
allows multiple signal representation. Implements different subsets of messages (MSM1, MSM2,.. MSM7)
to satisfy tarde off between compactness and plenitude of observables. MSM1 - most compact form,
MSM7 - most overall form with better accuracy. 

### GNSS_RTCM_DECODER

This project implements a tool for binary RTCM data unpacking and 
conversion into textual representation. Main purpose - representation of GNSS data in readable, editable form convenient for further manual and automated analysis and geodetic computations.

### Main features

- Extendable architecture. Source format - RTCM - implements plenty of messages having different purpose, content, format and transmission rules. On the other hand, there may be plenty of output data formats implementing different styles of representation of GNSS data. Depending of the post-processing aims user may be interested in bare integer data ("as it is" in RTCM message), proprietary format like RINEX, CSV representation for easy read and analysis or smth. else. So, the idea is to represent a conversion tool as a set of:
    1. Sub-decoders, responsible for different subsets of RTCM scope (Legacy, MSM, SSR and so on).
    2. Printers, responsible for different styles of output data representation.

    Extendability here means that software architecture and implementation provides an easy way to add a new sub-decoder or printer.

- Low memory consumption. Input file processed in chunk-by-chunk manner, thus even big files will not cause any memory violation issues.
- Robust binary data decoder. Primary RTCM decoder implements extraction of RTCM messages from input byte flow. Supports processing of files started with unaligned message, data gaps. Anomalies in input byte flow reported via the logger. May be easily modified to process real time byte flow from COM port, socket, etc.
- Dual channel logger. Provides sending of service information to file and to console in parallel. Message severity levels could be configured individually.
- User interface implemented via command prompt options + .ini file parameters. There is one mandatory .ini file - contains some 'mast have' parameters for proper decoder operation and one additional file, which can be referenced from the command prompt to provide some additional settings.
