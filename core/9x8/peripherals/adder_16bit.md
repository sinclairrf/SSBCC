Copyright 2012-2013, Sinclair R.F., Inc.<br/>
Copyright 2019, Rodney Sinclair

The "adder_16bit" peripheral adds or subtracts two 16 bit values.

Usage
=====

```
PERIPHERAL adder_16bit
```

The following OUTPORTs are provided by the peripheral:

| port | description |
| ---- | ----------- |
| O_ADDER_16BIT_MSB1 | MSB of first argument |
| O_ADDER_16BIT_LSB1 | LSB of first argument |
| O_ADDER_16BIT_MSB2 | MSB of second argument |
| O_ADDER_16BIT_LSB2 | LSB of second argument |
| O_ADDER_16BIT_OP | 0 ==> add, 1 ==> subtract |

The following INPORTs are provided by the peripheral:

| port | description |
| ---- | ----------- |
| I_ADDER_16BIT_MSB | MSB of the sum/difference |
| I_ADDER_16BIT_LSB | LSB of the sum/difference |

The file adder_16bit.s provides a function to add or subtract two 16-bit
values.

Example
=======

Add an 8-bit value and a 16-bit value from the stack.

Within the processor architecture file include the configuration command:

```
PERIPHERAL adder_16bit
```

Use the following assembly code to perform the addition to implement a function
that adds an 8-bit value at the top of the data stack to the 16-bit value
immediately below it:

```
; Add an 8 bit value to a 16-bit value.
; ( u2_LSB u2_MSB u1 - (u1+u2)_LSB (u1+u2)_MSB
.function add_u8_u16__u16

  ; write the 8-bit value to the peripheral (after converting it to a 16 bit
  ; value)
  0 .outport(O_ADDER_16BIT_MSB1) .outport(O_ADDER_16BIT_LSB1)

  ; write the 16-bit value to the peripheral
  .outport(O_ADDER_16BIT_MSB2) .outport(O_ADDER_16BIT_LSB2)

  ; command an addition
  0 .outport(O_ADDER_16BIT_OP)

  ; push the 16-bit sum onto the stack and return
  .inport(I_ADDER_16BIT_LSB) I_ADDER_16BIT_MSB .return(inport)
```
