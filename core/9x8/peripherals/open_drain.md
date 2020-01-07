Copyright 2012-2014, Sinclair R.F., Inc.<br/>
Copyright 2020, Rodney Sinclair

Open-drain I/O suitable for direct connection to a pin.

This can, for example, be used as an SCL or SDA I/O port for an I2C device.  Two
of these are required to implement a complete I2C bus.

Usage
=====

```
PERIPHERAL open_drain inport=I_name     \
                      outport=O_name    \
                      iosignal=io_name  \
                      [width=n]
```

Where:

- inport=I_name

  is the inport symbol to read the pin

- outport=O_name

  is the outport symbol to write to the pin

  Note:  A "0" value activates the open drain while a "1" value releases the
  open drain.

- iosignal=io_name

  is the tri-state pin for the open-drain I/O buffer

  Note:  The initial value of the pin is "open."

- width=n

  is the optional width of the port

  Note:  The default is one bit

The following OUTPORTs are provided by this peripheral:

- O_name

  this is the new output for the open drain I/O

The following INPORTs are provided by this peripheral:

- I_name

  this reads the current value of the open drain I/O

Example
=======

Configure two independent open-drain I/Os for an I2C bus master.

Add the following to the architecture file:

```
PORTCOMMENT I2C bus
PERIPHERAL open_drain inport=I_SCL outport=O_SCL iosignal=io_scl
PERIPHERAL open_drain inport=I_SDA outport=O_SDA iosignal=io_sda
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

See the I2C examples for a complete demonstration of using the open_drain
peripheral.

WARNING
=======

Some synthesis tools object to using "z" as a value.  You may need to use the
open_drain_tristate peripheral instead.
