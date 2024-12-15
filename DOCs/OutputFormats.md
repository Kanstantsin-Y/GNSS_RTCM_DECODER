
[Home](Home.md)

## MARGO

MARGO is a method of representation of GNSS observables developed by NTLab company. The idea is to put each parameter being observed into 
separate textual, regular, comma separated file. So we have individual file for each parameter (range, phase, carrier-to-noise ratio, doppler, ...)
of each signal (GPS L1CA, L2CM,..., GLN L1CA, L2CA, ...) of each GNSS (GPS, GLONASS, BeiDou, Galileo, Navic). Such files have very simple structure
and may be easily opened by variety of CSV compatible tools (EXCEL, MATLAB, PYTHON, etc.) and analyzed in manual or automated manner. MARGO printer
sorts files by GNSS and puts them into separate file folders. As a result there will be file structure like this:

[SOURCE_FILE_NAME-MARGO]   
|   
|-> [GPS] -> GC1C_MS7.obs, GL1C_MS7.obs, GS1C_MS7.obs, GD1C_MS7.obs,...   
|-> [GLN] -> RC1C_MS7.obs, RL1C_MS7.obs, RS1C_MS7.obs, RD1C_MS7.obs,...    
|-> [GAL] -> EC1X_MS7.obs, EL1X_MS7.obs, ES1X_MS7.obs, ED1X_MS7.obs,...    
|-> [BDS] -> BC2I_MS7.obs, BL2I_MS7.obs, BS2I_MS7.obs, BD2I_MS7.obs,...    
|-> [NAVIC] -> IC5A_MS7.obs, IL5A_MS7.obs, IS5A_MS7.obs, ID5A_MS7.obs,...    

Top level folder named by the name of source file. GNSS-folders created if any GNSS-related data presents in decoding products.
File names has strict pattern and encode GNSS, signal, parameter, source of parameter.

File name pattern:

    XYZZ_SRC.obs

Where X encodes GNSS.

| X      | GNSS
| -----  | -----
| G      | GPS
| R      | GLONASS
| G      | GALILEO
| B      | BeiDou
| I      | NAVIC
| S      | SBAS
| Q      | QZSS

Y encodes parameter.

| Y      | Parameter       | Units
| ------ | --------------- | ------ 
| C      | Code range      | meters 
| L      | Phase range     | cycles
| S      | C/N             | dB
| D      | Doppler         | Hz
| H      | HC ambiguity    | 0/1, 1 - ambiguity present 
| T      | Phase lock time | sec

C,L,S and D files generated if appropriate data available in source file. Availability of H and T files additionally controlled via
user *.ini file (generation may be switched off). Setup options 'HCA' and 'LOCK_TIME' in section [MARGO].

ZZ - encodes signal in RINEX-manner. Values are GNSS-specific see RINEX [specification](http://acc.igs.org/misc/rinex304.pdf) for details.

SRC - postfix - doesn't have predefined values, encodes source of observables. For example:
* _MSM7 - observables extracted from MSM7 message,
* _LEG  - observables extracted from legacy message.

Postfix allows to identify measurements if there are multiple sources of the same parameter.

MARGO file structure.

| TYPE    | SAT1   | SAT2   | SAT3   | SAT4   | SAT5   | ...    | SATx 
| :-----: | :----: | :----: | :----: | :----: | :----: | :----: | ----
|   NaN   |  CF1   |  CF2   |  CF3   |  CF4   |  CF5   |  ...   |  CFx 
|  TIME1  | OBS11  |  NaN   |  OBS31 |  NaN   |  OBS51 |  ...   | OBSx1
|  TIME2  | OBS12  |  NaN   |  OBS32 |  NaN   |  OBS52 |  ...   | OBSx2
|  TIME3  | OBS13  | OBS23  |  OBS33 |  NaN   |  OBS53 |  ...   | OBSx3
|   ...   |  ...   |  ...   |  ...   |  ...   |  ...   |  ...   |  ...
|   ...   |  ...   |  ...   |  ...   |  ...   |  ...   |  ...   |  ...
|  TIMEy  |  NaN   | OBS2y  |  OBS3y |  NaN   |  OBS5y |  ...   | OBSxy

MARGO file consists of comma-separated numeric values and 'NaN' marks, indicating absence of measurement. First two rows are 
header which contains some utility data.

* TYPE - numeric value, encodes type of parameters stored in this file (0 - code range, 1 - phase range).
* SAT1, SAT2, ..., SATx - 1-based satellite number. Maximum number x is GNSS specific.
* CF1, CF2, CF3,..., CFx - carrier frequency of definite satellite/signal. CF1..CFx values will have equal values for all GNSS signals except GLONASS. GLONASS CF values consider literal numbers. Information about mapping of satellite numbers to literals provided to converter via .ini file. Edit file to change mapping if necessary.
* TIME1, TIME2, TIMEy - time marks. All measurements in the raw belong to the same time. Units - [ms]. Meaning - time starting from the beginning of current GPS week. Time marks in all files (GLONASS, GALILEO, ...) converted to GPS time. Such conversion requires an additional parameters - GPS2UTC shift - provided to converter via *.ini file. GPS2UTC may be edited when reasonable.
* OBS11,...,OBSxy - observables - values of target parameter. 'NaN' marks cases, when there are no available observables.

X - number of columns

| GNSS    | X      
| -----   | -----  
| GPS     | 32      
| GLONASS | 24      
| GALILEO | 32      
| BeiDou  | 37      
| NAVIC   | 14      
| SBAS    | 38      
| QZSS    | 5

TYPE - code of parameter

| TYPE    | Parameter
| :-----: | -----
| 0       | code range
| 1       | phase range
| 2       | doppler
| 3       | signal-to-noise
| 4       | phase lock time
| 5       | half cycle ambiguity indicator

Phase range derivative and doppler have opposite signs. MARGO follows RINEX rules in doppler sign representation.

Example. File IC5A_MS0.obs.

|    0,    |          1,    |          2,    |          3,    |          4,    |          5,    |          6,    | ...,|        14
| ---------|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|:---:|:-----------:
|   NaN,   |      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,| ...,|    1176.4500
|210390000,|            NaN,|   36807474.929,|   40540406.124,|            NaN,|            NaN,|   38633538.891,| ...,|          NaN
|210391000,|            NaN,|   36807418.133,|   40540409.828,|            NaN,|            NaN,|   38633554.172,| ...,|          NaN
|210392000,|            NaN,|   36807362.001,|   40540422.215,|            NaN,|            NaN,|   38633568.849,| ...,|          NaN
|210393000,|            NaN,|   36807304.972,|   40540429.757,|            NaN,|            NaN,|   38633587.221,| ...,|          NaN
|   ...    |     ...        |    ...         |    ...         |      ...       |       ...      |      ...       | ...,|     ...


[Home](Home.md)


## JSON

Akin MARGO, JSON printer also sorts conversion products by GNSS and puts results into appropriate folders.

[SOURCE_FILE_NAME-JSON]   
|   
|-> [BASE] -> RefPoint-1005.json, RefPointHeight-1006.json, ..., GloBias-1230.json   
|-> [EPH] -> GPS-EPH-1019.json, GLN-EPH-1020.json, NAVIC-EPH-1041.json, ... GAL-EPH-1046.json      
|-> [MSM7] -> GPS-MSM7-1077.json, GLN-MSM7-1087.json, ..., NAVIC-MSM7-1137.json            
| ...       
|-> [MSM1] -> GPS-MSM1-1071.json, GLN-MSM1-1081.json, ..., NAVIC-MSM1-1131.json             
  
MSMx.

Each file accepts observables derived from definite MSM subset. That can help sort conversion products if multiple subsets used simultaneously.
Particular output file has following structure:

```json
[
 Welcome string,
{ TIME1 : OBJ1 },
{ TIME2 : OBJ2 },
{ TIME3 : OBJ3 },
...
]
```
At the upper level it is a list of JSON objects having time mark as a key and another JSON object as a value. The time mark derived from 
MSM message header. With GLONASS time mark = (header time + header day*86400000), shows time from the start of GLONASS week. The value is a JSON object, at the upper level looks like:

```json
{
    "hdr": {...},
    "aux": {...},
    "obs": {...}
}
```

Where:

"hdr" - header info, a dictionary - has MSM header data fields inside.

"aux" - auxiliary info, a dictionary - provides, GNSS, message number, MSM subset.

"obs" - observables, a dictionary - provides observables, an example below

```json
"obs": {
      "rng": {
        "1C": { "2": 22388353.703525275, "6": 23766575.24993011},
        "2S": { "6": 23766579.421788566, "11": 21741722.95303451}
      },
      "phs": {
        "1C": {"2": 22388353.974631857, "6": 23766578.899817653},
        "2S": {"6": 23766572.804665998, "11": 21741724.736725967}
      },
      "ltm": {
        "1C": {"2": 196608, "6": 204800},
        "2S": {"6": 155648, "11": 155648}
      },
      "hca": {
        "1C": {"2": false, "6": false},
        "2S": {"6": false, "11": false}
      },
      "dpl": {
        "1C": {"2": -490.3699, "6": 626.3713},
        "2S": {"6": 626.3929, "11": 258.949}
      },
      "c2n": {
        "1C": {"2": 45.0, "6": 40.0},
        "2S": {"6": 39.0, "11": 48.0}
      }
}

```
Where:

"rng" - [m] - code range measurements

"phs" - [m] - carrier range measurements

"ltm" - [msec] - carrier phase lock time

"hca" - [bool] - half cycle ambiguity flag

"dpl" - [m/s] - carrier phase rate

"c2n" - [dB/Hz] - carrier-to-noise ratio.

All observables are grouped by signal. Signals are encoded in accordance with RINEX rules.

Phase range derivative and doppler have equal signs. In this case sine representation sticks to original RTCM method. 

Sections "hdr" and "aux" are optional. Their printing out may be switched off via user *.ini file arguments. Use 'ENABLE_HDR_DATA' and  'ENABLE_AUX_DATA' options to switch them on/off. Another option useful for output file reduction - 'ENABLE_PRETTY_VIEW'. Disable pretty view to reduce output file size. All indentation spaces will be deleted. 

## JSON-B

This output format implements the same idea as JSON. The difference is in objects structure. JSON-B objects represent data fields and their values extracted from RTCM messages. Units and physical meaning of fields kept untouched. Key names follow RTCM standard naming, so there is no sense to list here objects structure - it is native to message structure. INI file controls (ENABLE_PRETTY_VIEW, ENABLE_HDR_DATA, ENABLE_AUX_DATA) work here as well.

[Home](Home.md)
