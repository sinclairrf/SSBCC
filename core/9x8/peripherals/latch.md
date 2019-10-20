Copyright 2012-2013, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Latch a large value for piecewise input.

This peripheral latches long external signals so that selected bytes can be
read.

This peripheral is used to input large values so that the pieces of the value
input to the processor are all valid at the same time.

Note:  The [big_inport](big_inport.md) provides similar functionality with the
restriction that byte selection is not provided.

Usage
=====

```
PERIPHERAL latch                        \
                outport_latch=O_latch   \
                outport_addr=O_addr     \
                inport=I_read           \
                insignal=i_name         \
                width=n
```

Where:

- outport_latch=O_latch

  specifies the symbol used by the processor to latch the input signal

  Note:  No data is associated with this output port, i.e., it is treated as a
  strobe.

- outport_addr=O_addr

  specifies the symbol used by the processor to indicate which byte of the
  registered input signal is to input by the next inport from I_name_READ

- inport=I_read

  specifies the symbol used by the processor to read the byte specified by the
  last outport to O_name_ADDR

- insignal=i_name

  specifies the name of the input signal

- width=n

  specified the width of the input signal

  Note:  The signal is broken into ceil(n/8) 8-bit words with indices from 0 to
  ceil(n/8)-1.

  Note:  This peripheral will issue an error if n<=8.

Example
=======

Capture an external 24-bit counter.

Within the processor architecture file include the configuration command:

```
PERIPHERAL latch                                \
                outport_latch=O_COUNT_LATCH     \
                outport_addr=O_COUNT_ADDR       \
                inport=I_COUNT_READ             \
                insignal=i_count                \
                width=24
```

To latch the counter and read the MSB of the latched count:

```
; Latch the count.
; ( - )
.outstrobe(O_COUNT_LATCH)

; Read the MSB of the 3-byte latched count.
; ( - u_count_MSB )
2 .outport(O_COUNT_ADDR) .inport(I_COUNT_READ)
```
