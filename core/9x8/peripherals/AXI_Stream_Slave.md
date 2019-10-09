Copyright 2016, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

AXI-Stream Slave port.

The AXI-Stream Slave port is synchronous to the micro controller clock.

Usage
=====

```
PERIPHERAL AXI_Stream_Slave                             \
                                basePortName=<name>     \
                                instatus=<I_status>     \
                                outlatch=<O_latch>      \
                                indata=<I_data>         \
                                data_width=<N>          \
                                [noTLast|hasTLast]
```

where:

  - basePortName=&lt;name&gt;

    specifies the name used to construct the multiple AXI-Stream signals

  - instatus=&lt;I_status&gt;

    specifies the symbol used to read the status as to whether or not data is
    available on the port

    Note:  Data is available if bit 0x01 is set.  If data is not available the
    byte will be 0x00.

    Note:  If "hasTLast" is specified, bit 0x02 of the status will be the value
    of the TLast signal coincident with the data that will be latched by the
    outlatch strobe.

  - outlatch=&lt;O_latch&gt;

    specifies the symbol used for the outport strobe that latches the AXI-Stream
    data so that it can be read by the indata inport symbol

    Note:  This also generates the acknowledgement signal that allows the data
    on the AXI-Stream to advance (which is why the TLast value cannot be sampled
    after this strobe is generated).

  - indata=&lt;I_data&gt;

    specifies the symbol used to read the data portion of the AXI-Stream latched
    by the outlatch symbol

    Note:  Data is read LSB first.

  - data_width=&lt;N&gt;

    specifies the width of the data portion of the AXI-Stream

    Note:  N must be a positive multiple of 8.

  - noTLast

    optionally specifies that the incoming AXI-Stream does not have a TLast signal

    Note:  This is the default.

  - hasTLast

    optionally specifies that the incoming AXI-Stream does have a TLast signal

Example
=======

Receive data from a 32-bit wide AXI-Stream and preserve the value of the TLast
signal.

```
PERIPHERAL AXI_Stream_Slave                                     \
                                basePortName=s_axis_32bit       \
                                instatus=I_S_AXIS_32BIT_STATUS  \
                                outlatch=O_LATCH_S_AXIS_32BIT   \
                                indata=I_S_AXIS_32BIT_DATA      \
                                data_width=32                   \
                                hasTLast
```

The value of the "tlast" signal and the 4 bytes of data can be received and
pushed onto the data stack as follows:

```
; Wait for data to arrive on the AXI-Stream.
; ( - )
:loop_wait .inport(I_S_AXIS_32BIT_STATUS) 0= .jumpc(loop_wait)

; Push the status of the TLast signal onto the data stack.
; ( - f_tlast )
.inport(I_S_AXIS_32BIT_STATUS) 0x02 and 0<>

; Latch and read the AXI-Stream data.
; ( f_tlast - f_tlast u_LSB ... u_MSB )
.outstrobe(O_LATCH_S_AXIS_32BIT)
${4-1} :loop_read >r .inport(I_S_AXIS_32BIT_DATA) r> .jumpc(loop_read,1-) drop
```

LEGAL NOTICE
============

ARM has restrictions on what kinds of applications can use interfaces based on
their AXI protocol.  Ensure your application is in compliance with their
restrictions before using this peripheral for an AXI interface.
