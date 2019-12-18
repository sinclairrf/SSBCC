Copyright 2013-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Output FIFO with an asynchronous clock.

Usage
=====

```
PERIPHERAL outFIFO_async        outclk=<i_clock>                \
                                data=<o_data>                   \
                                data_rd=<i_data_rd>             \
                                data_empty=<o_data_empty>       \
                                outport=<O_data>                \
                                infull=<I_full>                 \
                                depth=<N>                       \
                                [outempty=I_empty]
```

Where

- outclk=<i_clock>

  specifies the name of the asynchronous read clock

- data=<o_data>

  specifies the name of the 8-bit outgoing data

- data_rd=<i_data_rd>

  specifies the name if the read strobe

- data_empty=<o_data_empty>

  specifies the name of the output "empty" status of the FIFO

- outport=<O_data>

  specifies the name of the port to write to the FIFO

- infull=<I_full>

  specifies the symbol used by the inport instruction to read the "full" status
  of the FIFO

- depth=<N>

  specifies the depth of the FIFO

  Note:  N must be a power of 2 and must be at least 16.

- outempty=O_empty

  optionally specifies the name of an input port for the processor to access the
  "empty" status of the FIFO\n

Example
=======

Provide a FIFO to an external device or IP.

The PERIPHERAL statement would be:

```
PERIPHERAL outFIFO_async        outclk=i_dev_clk        \
                                data=o_dev_data         \
                                data_rd=i_dev_data_rd   \
                                data_empty=o_dev_empty  \
                                outport=O_DATA_FIFO     \
                                infull=I_DATA_FIFO_FULL \
                                depth=32
```

To put a text message in the FIFO, similarly to a UART, do the following:

```
N"message"
:loop
  .inport(I_DATA_FIFO_FULL) .jumpc(loop)
  .outport(O_DATA_FIFO)
  .jumpc(loop,nop)
drop
```

Interrupt handler:  "!s__<data>__outempty_in" is is suitable input to an
interrupt handler where "<data>" is the name assigned to "data".  This signal is
high when the FIFO is empty, so a falling edge (the leading "!") is a suitable
condition for the interrupt to occur.
