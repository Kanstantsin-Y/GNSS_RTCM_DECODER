
[Home](Home.md)

## Decoders and printers

A list of sub-decoders to be implemented.

| Sub-decoders     | RTCM subset             | Ready?        | Description             | Output data class
| -----------      | -----------             | -----------   | -----------             | -----------
| 'MSM47O'         | MSM4, MSM5, MSM6, MSM7  | yes           | Observables             | 'ObservablesMSM' or 'BareObservablesMSM4567' [1]
| 'MSM13O'         | MSM1, MSM2, MSM3        | yes           | Observables modulo 1ms  | 'ObservablesMSM' or 'BareObservablesMSM123' [1]
| 'LEG0'           | 1001..1004, 1009..1012  | not yet       | Observables GPS, GLONASS| Not defined  
| 'EPH'            | 1019, 1020, 1041..1046  | yes           | ephemeris, all systems  | 'EphGPS', 'EphGLO', 'EphGALF', 'EphGALI', 'EphBDS', 'EphQZS', 'EphNAVIC' [2]

[1]: Sub-decoder 'MSM47O' and 'MSM13O' can produce optionally two types of outputs:

    - 'ObservablesMSM'. Contains data fields from the message, scaled following the RTCM specification and represented in floating-point
    format (where needed).
    
    - 'BareObservablesMSM4567', 'BareObservablesMSM123'. It contains data from the message in integer, not scaled form, as it was transmitted.
    Output data format defined during sub-decoder initialization.
[2]: The same class is used for bare integer and scaled representations.


Top-level decoder combines properties of sub-decoders and provides a method to convert RTCM message into an output data class. The message should be represented as a sequence of bytes (type 'bytes'), starting with 0xD3 (aligned) and having 3 CRC bytes at the end. The top decoder checks the message number and calls a suitable sub-decoder. Decoding products stored in a data class (see table above).

Printers are software entities used for saving products pf decoding in appropriate format. Akin decoder, a printer is an aggregation of sub-printers where each one is responsible for a subset of input data classes. 

| Sub-Printer      | Implemented ?  | Input data class
| -----------      | -----------    | -----------
| 'MARGO'          |  yes           | 'ObservablesMSM'
| 'JSON'           |  yes           | 'ObservablesMSM'
| 'JSON-B'         |  yes           | 'BareObservablesMSM123', 'BareObservablesMSM456'
| -----------      | -----------    | -----------
| 'MARGO'          |  no            | 'EphGPS', 'EphGLO', 'EphGALF', 'EphGALI', 'EphBDS', 'EphQZS', 'EphNAVIC'
| 'JSON'           |  yes           | 'EphGPS', 'EphGLO', 'EphGALF', 'EphGALI', 'EphBDS', 'EphQZS', 'EphNAVIC'
| 'JSON-B'         |  yes           | 'EphGPS', 'EphGLO', 'EphGALF', 'EphGALI', 'EphBDS', 'EphQZS', 'EphNAVIC'

