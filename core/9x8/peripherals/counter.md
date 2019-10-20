Copyright 2013-2014, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

Count received strobes.

Usage
=====

```
PERIPHERAL counter                              \
                insignal=i_name                 \
                inport=I_NAME                   \
                [width=<N> outlatch=O_NAME]
```

Where:

- insignal=i_name

  specifies the name of the signal input to the micro controller

- input=I_NAME

  specifies the symbol use to read the count

- width=<N>

  optionally specifies the width of the counter

  Note:  The default is 8 bits.

  Note:  If the width is more than 8 bits then the optional outlatch needs to be
  provided.  This is strobe outport is used to latch the value of the counter so
  that it can be input from its LSB to its MSB.

Note:  The counter is not cleared when it is read.  Software must maintain the
       previous value of the count if delta-counts are required.

Example
=======

Create an 8-bit count for the number of strobe events received.

```
PORTCOMMENT external strobe (input to 8-bit counter)
PERIPHERAL counter                      \
                insignal=i_strobe       \
                inport=I_STROBE_COUNT
```

Read the count:

```
.inport(I_STROBE_COUNT)
```

Example
=======

Create a 12-bit count for the number of strobe events received.

```
PORTCOMMENT external strobe (input to 12-bit counter)
PERIPHERAL counter                              \
                insignal=i_strobe               \
                inport=I_STROBE_COUNT           \
                width=12                        \
                outlatch=O_LATCH_STROBE_COUNT
```

Read the count:

```
; latch the count
.outstrobe(O_LATCH_STROBE_COUNT)

; read the count LSB first
; ( - u_LSB u_MSB )
.inport(I_STROBE_COUNT) .inport(I_STROBE_COUNT)
```
