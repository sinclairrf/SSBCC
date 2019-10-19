Copyright 2013-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Write a multi-byte signal.

Usage
=====

```
PERIPHERAL big_outport                          \
                        outport=O_name          \
                        outsignal=o_name        \
                        width=<N>
```

Where

- outport=O_name

  specifies the symbol used to write to the output port

- outsignal=o_name

  specifies the name of the signal output from the module

- width=<N>

  specifies the width of the I/O

Example
=======

Create a 26-bit output signal for output of 26-bit or 18-bit values
from the processor to external IP.

```
PORTCOMMENT 26-bit output for use by other modules
PERIPHERAL big_outport                                 \
                        output=O_26BIT_SIGNAL          \
                        outsignal=o_26bit_signal       \
                        width=26
OUTPORT strobe  o_wr_26bit      O_WR_26BIT
OUTPORT strobe  o_wr_18bit      O_WR_18BIT
```

Writing a 26-bit value requires 4 successive outports to O_26BIT_SIGNAL,
starting with the MSB as follows:

```
; Write a 26-bit value 0x024a_5b6c
0x02 .outport(O_26BIT_SIGNAL)
0x4a .outport(O_26BIT_SIGNAL)
0x5b .outport(O_26BIT_SIGNAL)
0x6c .outport(O_26BIT_SIGNAL)
.outstrobe(O_WR_26BIT)
```

Writing an 18-bit value requires 3 successive outports to O_26BIT_SIGNAL
starting with the MSB as illustrated by the following function:

```
; Read the 18-bit value from memory and then write it to a peripheral.
; Note:  The multi-byte value is stored MSB first in memory.
; ( u_addr - )

.function write_18bit_from_memory

  ; Read 3 bytes from the memory "ram" to the data stack.
  ; ( u_addr - u_addr[2] u_addr[1] u_addr[0] )
  2 + fetch-(ram) fetch-(ram) fetch(ram)

  ; Write the 3-byte value to the output port.
  ; ( u_addr[2] u_addr[1] u_addr[0] - )
  ; o_26bit_signal <= { ???, u_addr[0], u_addr[1], u_addr[2] }
  .outport(O_26BIT_SIGNAL) .outport(O_26BIT_SIGNAL) .outport(O_26BIT_SIGNAL)

  ; Issue the output strobe
  .outstrobe(O_WR_18BIT)

  ; Return
  .return
```

The function body can be written with slightly less code as follows:

```
.function write_18bit_from_memory

  ; Read 3 bytes from the memory "ram" MSB first and write them to the output
  ; port.
  ; ( u_addr - )
  ; o_26bit_signal <= { ???, u_addr[0], u_addr[1], u_addr[2] }
  ${3-1} :loop r>
    .fetch+(ram) swap .outport(O_26BIT_SIGNAL)
  >r .jumpc(loop,1-) drop drop

  ; Return and issue the output strobe.
  ; ( - )
  ; o_wr_18bit <= strobed
  O_WR_18BIT .return(outport)
```
