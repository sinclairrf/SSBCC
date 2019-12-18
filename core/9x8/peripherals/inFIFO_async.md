Copyright 2013-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Input FIFO with an asynchronous clock.

Usage
=====

```
PERIPHERAL inFIFO_async
                        inclk=<i_clock>         \
                        data=<i_data>           \
                        data_wr=<i_data_wr>     \
                        data_full=<o_data_full> \
                        inport=<I_data>         \
                        inempty=<I_empty>       \
                        depth=<N>               \
                        [width=<W>]
```

Where:

- inclk=<i_clock>

  specifies the name of the asynchronous clock

- data=<i_data>

  specifies the name of the 8-bit incoming data

- data_wr=<i_data_wr>

  specifies the name if the write strobe

- data_full=<o_data_full>

  specifies the name of the output "full" status of the FIFO

- inport=<I_data>

  specifies the name of the port to read from the FIFO

- inempty=<I_empty>

  specifies the symbol used by the inport instruction to read the "empty" status
  of the FIFO

- depth=<N>

  specifies the depth of the FIFO

  Note:  N must be a power of 2 and must be at least 16.

Example
=======

Provide a FIFO for an external device or IP that pushes 8-bit data
to the processor.

The PERIPHERAL statement would be:

```
PERIPHERAL inFIFO_async inclk=i_dev_clk                 \
                        data=i_dev_data                 \
                        data_wr=i_dev_data_wr           \
                        data_full=o_dev_full            \
                        inport=I_DATA_FIFO              \
                        inempty=I_DATA_FIFO_EMPTY       \
                        depth=32
```

To read from the FIFO and store the values on the data stack until the FIFO
is empty and to track the number of values received, do the following:

```
; ( - u_first ... u_last u_N )
0x00 :loop
  .inport(I_DATA_FIFO_EMPTY) .jumpc(done)
  .inport(I_DATA_FIFO) swap
  .jump(loop,1+)
:done
```
