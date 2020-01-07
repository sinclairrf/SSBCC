Copyright 2020, Rodney Sinclair

Open-drain I/O with tri-state pins.

This can, for example, be used as an SCL or SDA I/O port for an I2C device.  Two
of these are required to implement a complete I2C bus.

Usage
=====

```
PERIPHERAL open_drain_tristate \
                        basesignal=name   \
                        inport=I_name     \
                        outport=O_name
```

Where:

- inport=I_name

  is the inport symbol to read the "i_name_i" pin

- outport=O_name

  is the outport symbol to write to the "o_name_t" pin

  Note:  A "0" value activates the open drain while a "1" value releases the
  open drain.

- basesignal=name

  specifies the name used to contruct the 3 tri-state I/O pins as follows:

  | signal | description |
  | ------ | ---------- |
  | i_name_i | input value from the bus |
  | o_name_o | constant value of 0 |
  | o_name_t | tri-state pin (1 ==> tri-stated, 0 ==> output 0 on o_name_o) |

  Note:  This means the bus will be pulled down when the tri-state pin is set to
  the value&nbsp;0.

The following OUTPORT is provided by this peripheral:

- O_name

  this is the new output for the o_name_t signal

The following INPORT is provided by this peripheral:

- I_name

  this reads the current value of i_name_i

Example
=======

Configure the tri-state signals to drive two independent open-drain I/Os for an
I2C bus master.

Add the following to the architecture file:

```
PORTCOMMENT I2C bus
PERIPHERAL open_drain_tristate inport=I_SCL outport=O_SCL basesignal=scl
PERIPHERAL open_drain_tristate inport=I_SDA outport=O_SDA basesignal=sda
```

The following assembly will transmit the start condition for an I2C bus by
pulling SDA low and then pulling SCL low.

```
; Set SDA low
0 .outport(O_SDA)

; delay one fourth of a 400 kHz cycle (based on a 100 MHz clock)
${int(100.e6/400.e3/3)-1} :delay .jumpc(delay,1-) drop

; Set SCL low
0 .outport(O_SCL)
```

This peripheral is used identically to the open_drain peripheral except that
three signals are provided to connect to the I/O buffer instead of inferring the
tri-state I/O using "z" as a signal value.

See the I2C examples for a complete demonstration of using the open_drain
peripheral.
