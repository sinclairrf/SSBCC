Copyright 2013-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Read a wide signal into two or more bytes.

Usage
=====

```
PERIPHERAL big_inport                           \
                        outlatch=O_name         \
                        inport=I_name           \
                        insignal=i_name         \
                        width=<N>
```

Where:

- outlatch=O_name

  specifies the symbol used to latch the incoming value

- inport=I_name

  specifies the symbol used to read from the output port

- insignal=i_name

  specifies the name of the signal input to the module

- width=<N>

  specifies the width of the I/O register

Example
=======

Create a 23-bit input signal to receive an external (synchronous) counter.

```
PORTCOMMENT 23-bit counter
PERIPHERAL big_inport                                   \
                        outlatch=O_LATCH_COUNTER        \
                        inport=I_COUNTER                \
                        insignal=i_counter              \
                        width=23
```

Reading the counter requires issuing a command to latch the current value and
then 3 reads to the I/O port as follows:

```
; Latch the external counter and then read the 3-byte value of the count.
; ( - u_LSB u u_MSB )
.outstrobe(O_LATCH_COUNTER)
.inport(I_COUNTER) .inport(I_COUNTER) .inport(I_COUNTER)
```
