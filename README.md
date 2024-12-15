

### GNSS_RTCM_DECODER

This project implements a tool for binary RTCM data unpacking and conversion into textual representation. Main purpose - representation of GNSS data in a readable, editable form convenient for further manual or automated analysis and geodetic computations. Run **main.py** with command line arguments to start conversion. See 
[Home](DOCs/Home.md) for details.

### Notes.

**Version 1.01.** 

Initial version.
MSM messages are decoded. Observables are available in JSON, JSON-B (data as-it-is in the message, no scaling) and MARGO formats.
MARGO stores measurements in comma-separated form following the principle "one parameter - one file"; can be loaded with Matlab, Excel, etc.

A tip regarding JSON: use .ini file to enable pretty view if you need readable representation; disable pretty view if you prefer data from a single message to be packed into a single line.
Find more details about formats and command line options here [Home](DOCs/Home.md).

-------------------------------------------------------------------------------------------------------------
**Version 1.10.**
1. New functionality. Ephemeris messages 1019, 1020, 1041, 1042, 1044, 1045, and 1046 are decoded. Decoded ephemeris is available in JSON or JSON-B formats.
2. Fixes. The header (1st line) format in JSON files has
been fixed. Files can be loaded using the standard JSON.load() method.
3. Renamed some instances:
   main.py -> run_conversion.py
   folder data_types -> gnss_types.
4. Added some test samples of .rtcm3 files with GPS, GLO, GAL-I, BDS, and NAVIC ephemeris.
5. The script test_run_conversion.py implements conversion and compares results to the reference data, validates correct decoding, and provides an example of conversion.
6. Check file RTCM_EPH.py for the units of ephemeris parameters after int->float scaling.


-------------------------------------------------------------------------------------------------------------
**Version 1.20.**

1. New functionality. Base Station Data messages 1005, 1006, 1007, 1008, 1013, 1029, 1033, and 1230 are decoded. The decoding products are available in JSON and JSON-B formats.
2. Fixes/Improvements:
   - Modified the implementation of JSON printer. It is better readable/comprehensible now.
   - Added test case for ephemeris message 1045.
   - Refactored tests, and added tests for Base Station Data messages.
3. ToDo.
   - Message 1013 (System Parameters) is undertested. Need some real data to develop a thorough test case.
   

 

