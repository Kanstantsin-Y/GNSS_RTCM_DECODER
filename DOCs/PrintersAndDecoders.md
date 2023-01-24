
## Decoders and printers


| Sub-decoders     | RTCM subset             | Implemented ? | Description            | Output data class
| -----------      | -----------             | -----------   | -----------            | -----------
| 'MSM47O'         | MSM4, MSM5, MSM6, MSM7  | yes           | Observables            | 'ObservablesMSM' or 'BareObservablesMSM4567' [1]
| 'MSM13O'         | MSM1, MSM2, MSM3        | yes           | Observables modulo 1ms | 'ObservablesMSM' or 'BareObservablesMSM123' [1]
| 'MSME'           | 1041, 1042, 1044..1046  | no            | Ephemerids             | Not defined   
| 'LEG0'           | 1001..1004, 1009..1012  | no            | Observable GPS, GLONASS| Not defined  
| 'LEGE'           | 1019, 1020              | no            | Ephemerids GPS, GLONASS| Not defined  

[1]: 'MSM47O' and 'MSM13O' decoders may produce optionally two types of outputs:

    - 'ObservablesMSM'. Contains data fields from the message, scaled in accordance with RTCM specification and represented in floating-point
    format (where needed).
    
    - 'BareObservablesMSM4567', 'BareObservablesMSM123'. Contains data from the message in integer, not scaled form as it was transmitted.
    Output data format defined during sub-decoder initialization.      

Top level decoder combines properties of sub-decoders and provides method to convert rtcm message into output data class. Message should be represented as a sequence of bytes (type 'bytes'), started with 0xD3 (aligned) and having 3 CRC bytes at the end. Top decoder checks message number and calls suitable sub-decoder. Decoding products stored in data class (see table above).

Printers are software entities used for saving decoding products in appropriate format. Akin decoder, printer is an aggregation of sub-printers
each responsible for subset of input data classes. 

| Sub-Printer      | Implemented ?  | Input data class
| -----------      | -----------    | -----------
| 'MARGO'          |  yes           | 'ObservablesMSM'
| 'JSON'           |  no            | 'ObservablesMSM'
| 'JSON-B'         |  no            | 'BareObservablesMSM123', 'BareObservablesMSM456'


## MARGO

MARGO is a method of representation of GNSS observables developed by NTLab company. The idea is to put each parameter being observed into 
separate textual, regular, comma separated file. So we have individual file for each parameter (range, phase, carrier-to-noise ratio, doppler, ...)
of each signal (GPS L1CA, L2CM,..., GLN L1CA, L2CA, ...) of each GNSS (GPS, GLONASS, BeiDou, Galileo, Navic). Such files have very simple structure
and may be easily opened by variety of CSV compatible tools (EXCEL, MATLAB, PYTHON, etc.) and analyzed in manual or automated manner. MARGO printer
sorts files by GNSS and puts them into separate file folders. As a result there will be file structure like this:

[SOURCE_FILE_NAME]   
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

ZZ - encodes signal in RINEX-manner. Values are GNSS-specific see RINEX specification for [details](http://acc.igs.org/misc/rinex304.pdf). 

SRC - postfix - doesn't have predefined values, encodes source of observables. For example:
* _MSM7 - observables extracted from MSM7 message,
* _LEG  - observables extracted from legacy message.

Postfix allows to identify measurements if there are multiple sources of the same data.

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
* CF1, CF2, CF3,..., CFx - carrier frequency of definite satellite/signal. CF1..CFx values will have equal values for all GNSS signals except GLONASS.
GLONASS CF values consider literal numbers. Information about mapping of satellite numbers to literals provided to converter via .ini file. Edit file to change mapping if necessary.
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

Example. File IC5A_MS0.obs.

|    0,    |          1,    |          2,    |          3,    |          4,    |          5,    |          6,    | ...,|        14
| ---------|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|:---:|:-----------:
|   NaN,   |      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,|      1176.4500,| ...,|    1176.4500
|210390000,|            NaN,|   36807474.929,|   40540406.124,|            NaN,|            NaN,|   38633538.891,| ...,|          NaN
|210391000,|            NaN,|   36807418.133,|   40540409.828,|            NaN,|            NaN,|   38633554.172,| ...,|          NaN
|210392000,|            NaN,|   36807362.001,|   40540422.215,|            NaN,|            NaN,|   38633568.849,| ...,|          NaN
|210393000,|            NaN,|   36807304.972,|   40540429.757,|            NaN,|            NaN,|   38633587.221,| ...,|          NaN
|   ...    |     ...        |    ...         |    ...         |      ...       |       ...      |      ...       | ...,|     ...

