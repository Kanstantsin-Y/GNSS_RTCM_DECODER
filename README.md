

### GNSS_RTCM_DECODER

This project implements a tool for binary RTCM data unpacking and conversion into textual representation. Main purpose - representation of GNSS data in a readable, editable form convenient for further manual or automated analysis and geodetic computations. Run **main.py** with command line arguments to start conversion. See 
[Home](DOCs/Home.md) for details.

### Notes.

**Version 1.01.** 

2023.02.05. Tested with MSM7 messages as input and MARGO, JSON, JSON-B as output. MSM1 .. MSM6 not tested.
-------------------------------------------------------------------------------------------------------------
**Version 1.10.**
1. New functionality. Ephemeris messages 1019, 1020, 1041, 1042, 1044, 1045, and 1046 are decoded. Decoded ephemeris is available in JSON or JSON-B formats.
2. Fixes. The header (1st line) format in JSON files has been fixed. Files can be loaded with the standard JSON.load() method.
3. Renamed some instances:
   main.py -> run_conversion.py
   folder data_types -> gnss_types.
4. Added some test samples of .rtcm3 files with GPS, GLO, GAL-I, BDS, and NAVIC ephemeris.
5. The script test_run_conversion.py implements conversion and compares results to the reference data, validates correct decoding, and provides an example of conversion.
6. Check file RTCM_EPH.py for the units of ephemeris parameters after int->float scaling.
   
   

 

