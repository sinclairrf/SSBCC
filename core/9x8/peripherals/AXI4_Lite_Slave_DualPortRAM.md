Copyright 2019, Rodney Sinclair

AXI-Lite slave implemented as a dual-port RAM.

The data is stored in little endian format (i.e., the LSB of the 32-bit word is
stored in the lowest numbered address).

Usage:

```
PERIPHERAL AXI4_Lite_Slave_DualPortRAM                  \
                                basePortName=<name>     \
                                address=<O_address>     \
                                read=<I_read>           \
                                write=<O_write>         \
                                [size=<N>]              \
                                [ram8|ram32]
```

Where:

  - basePortName=<name>

    specifies the name used to construct the multiple AXI4-Lite signals

  - address=<O_address>

    specifies the symbol used to set the address used for read and write
    operations from and to the dual-port memory

  - read=<I_read>

    specifies the symbol used to read from the dual-port memory

  - write=<O_write>

    specifies the symbol used to write to the dual-port memory

  - size=<N>

    optionally specify the size of the dual-port memory.

    Note:  N must be either a power of 2 in the range from 16 to 256 inclusive
    or it must be a local param with the same restrictions on its value.

    Note:  N=256, i.e., the largest memory possible, is the default.

    Note:  Using a localparam for the memory size provides a convenient way to
    use the size of the dual port RAM in the micro controller code.

  - ram8

    optionally specifies using an 8-bit RAM for the dual-port memory instantiation

    Note:  This is the default

  - ram32

    optionally specifies using a 32-bit RAM for the dual-port memory instantiation

    Note:  This is required for Vivado 2013.3.

Example:  Read from and write to the dual-port RAM.

  ```
  ; read an 8-bit value from the 8-bit address <addr>
  <addr> .outport(O_address) .inport(I_read)
  ; write an 8-bit value <value> to the 8-bit address <addr>
  <addr> .outport(O_address) <value> .outport(O_write)
  ```

Example:  Function to read the byte at the specified address:

  ```
  ; ( u_addr - u_value)
  .function als_read
    .outport(O_address) .inport(I_read) .return
  ```

  or

  ```
  ; ( u_addr - u_value)
  .function als_read
    .outport(O_address) I_read .return(inport)
  ```

  To invoke the function:

  ```
  <addr> .call(als_read)
  ```

  or

  ```
  .call(als_read,<addr>)
  ```

Example:  Function to write a byte at a specified 8-bit address:

  ```
  ; ( u_value u_addr - )
  .function als_write
    .outport(O_address) O_write outport .return(drop)
  ```

  To invoke the function:

  ```
  <value> <addr> .call(als_write)
  ```

  or

  ```
  <value> .call(als_write,<addr>)
  ```

Example:  Spin on an address, waiting for the host processor to write to the
first address in the RAM, do something when the address is written to, and then
clear its contents.

  ```
  0x00 .outport(O_address)
  :loop .inport(I_read) 0= .jumpc(loop)
  ; Avoid race conditions between the processor write and the micro controller
  ; read.
  .inport(I_read)
  ...
  ; clear the value and start waiting again
  0x00 O_address outport O_write outport .jump(loop,drop)
  ```

LEGAL NOTICE:  ARM has restrictions on what kinds of applications can use
interfaces based on their AXI protocol.  Ensure your application is in
compliance with their restrictions before using this peripheral for an AXI
interface.
