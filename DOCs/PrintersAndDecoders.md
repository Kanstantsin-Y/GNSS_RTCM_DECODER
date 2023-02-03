
[Go Home](Home.md)

## Decoders and printers

A list of sub-decoders to be implemented.

| Sub-decoders     | RTCM subset             | Ready?        | Description            | Output data class
| -----------      | -----------             | -----------   | -----------            | -----------
| 'MSM47O'         | MSM4, MSM5, MSM6, MSM7  | yes           | Observables            | 'ObservablesMSM' or 'BareObservablesMSM4567' [1]
| 'MSM13O'         | MSM1, MSM2, MSM3        | yes           | Observables modulo 1ms | 'ObservablesMSM' or 'BareObservablesMSM123' [1]
| 'MSME'           | 1041, 1042, 1044..1046  | no yet        | Ephemerids             | Not defined   
| 'LEG0'           | 1001..1004, 1009..1012  | no yet        | Observable GPS, GLONASS| Not defined  
| 'LEGE'           | 1019, 1020              | no yet        | Ephemerids GPS, GLONASS| Not defined  

[1]: Sub-decoder 'MSM47O' and 'MSM13O' can produce optionally two types of outputs:

    - 'ObservablesMSM'. Contains data fields from the message, scaled in accordance with RTCM specification and represented in floating-point
    format (where needed).
    
    - 'BareObservablesMSM4567', 'BareObservablesMSM123'. Contains data from the message in integer, not scaled form as it was transmitted.
    Output data format defined during sub-decoder initialization.      

Top level decoder combines properties of sub-decoders and provides method to convert rtcm message into output data class. Message should be represented as a sequence of bytes (type 'bytes'), started with 0xD3 (aligned) and having 3 CRC bytes at the end. Top decoder checks message number and calls suitable sub-decoder. Decoding products stored in data class (see table above).

Printers are software entities used for saving decoding products in appropriate format. Akin decoder, printer is an aggregation of sub-printers each responsible for subset of input data classes. 

| Sub-Printer      | Implemented ?  | Input data class
| -----------      | -----------    | -----------
| 'MARGO'          |  yes           | 'ObservablesMSM'
| 'JSON'           |  yes           | 'ObservablesMSM'
| 'JSON-B'         |  yes           | 'BareObservablesMSM123', 'BareObservablesMSM456'

