**9-bit opcode, 8-bit data stack-based micro controller**

Copyright 2012, 2018, Sinclair R.F., Inc.

This document describes the 9-bit opcode, 8-bit data, stack-based
microcontroller architecture, instructions, assembler, and macros.

Contents
========

[Introduction](#introduction)

[Design](#design)

[OPCODES](#opcodes)

[Assembler](#assembler)

[Macros](#macros)

Directory Contents
==================

This directory contains the assembler and the Verilog template for the
processor.  While the assember can be run by itself, it is more typically run by
the <tt>../../ssbcc</tt> script as part of making a complete computer core.

<a name="introduction"></a>
Introduction
============

This processor is a minimalist FPGA-based microcontroller.  It provides 8-bit
data manipulation operations and function calls.  There are no condition
registers as the results of tests are on the data stack.  The instruction space,
data stack size, return stack size, existence and sizes of RAMs and ROMs, and
peripherals are controlled by a configuration file so that the processor can be
configured for the problem at hand.  The configuration file also describes the
input and output ports and include 0 to 8 bit port widths and strobes.  A
complete processor can be implemented using just the configuration file and the
assembly file.

A 9-bit opcode was chosen because (1) it works well with Altera, Lattice, and
Xilinx SRAM widths and (2) it allows pushing 8-bit data onto the stack with a
single instruction.

An 8-bit data width was chosen because that's a practical minimal size.  It is
also common to many hardware interfaces such as I2C devices.

The machine has single-cycle instruction execution for all instructions.
However, some operations, such as a jump, require pushing the 8 lsb of the
target address onto the stack in one instruction, executing the jump with the
remaining 5 msb of the target address, and then a <tt>nop</tt> or other
instruction during the following clock cycle.

Only one data stack shift can be achieved per instruction cycle.  This means
that all operations that consume the top two elements of the stack, such as a
store instruction, can only remove one element from the stack and must be
followed by a "<tt>drop</tt>" instruction to remove what had been the second
element on the data stack.

This architecture accommodates up to a 13-bit instruction address space by first
pushing the 8 least significant bits of the destination address onto the stack
and then encoding the 5 most significant bits in the jump or call instruction.
This is the largest practicable instruction address width because (1) one bit of
the opcode is required to indicate pushing an 8-bit value onto the stack, (2)
one bit of the remaining 8 bits is required to indicate the presence of a jump
or call instruction, (3) one bit is required to indicate whether the jump or
call is always performed or is conditionally performed, and (4) one more bit is
required to distinguish between a jump and a call.  This consumes 4 bits and
leaves 5 bits of additional address space for the jump instruction.

This architecture also supports 0 to 4 pages of RAM and ROM with a combined
limit of 4 pages.  Each page of RAM or ROM can hold up to 256 bytes of data.
This means that the architecture provides up to 1 kB of RAM and ROM for the
micro controller.

<a name="design"></a>
Design
======

The processor is a mix of instructions that operate on the top element of the
data stack (such as left or right shifts); operations that combine the top two
elements of the data stack such as addition and subtraction; operations that
manipulate the data stack such as 8-bit pushes, <tt>drop</tt>, and <tt>nip</tt>;
operations that move data between the data stack and the return stack; jumps and
calls and their conditional variants; memory operations; and I/O operations.

This section describes these operations.  The next section defines these
instructions in detail.

- Data Stack Operations:

  The data stack 8 bits wide.  The top two elements of this data stack, called
  <tt>T</tt> for the top of the data stack and <tt>N</tt> for the next-to-top of
  the data stack, are stored in registers so that they are immediately available
  to the processor core.  The remaining values are stored in the 8-bit wide RAM
  comprising the stack.  This will usually be some form of distributed RAM on an
  FPGA.  The index to the top of the stack is retained in a register.

  A few examples illustrate how the data stack is manipulated:

  - A push instruction simultaneously moves <tt>N</tt> into the data stack RAM,
    increments the pointer into the data stack, replaces <tt>N</tt> with
    <tt>T</tt>, and replaces <tt>T</tt> with the value being pushed onto the
    data stack.

  - The <tt><<0</tt> instruction shifts the value in <tt>T</tt> left one
    bit and brings a zero in as the new lsb.  The data stack is otherwise left
    unchanged.

  - The <tt>swap</tt> instruction swaps the values in <tt>T</tt> and <tt>N</tt>
    and leaves the rest of the data stack unchanged.

  - The <tt>drop</tt> instruction moves <tt>N</tt> into <tt>T</tt>, the top of
    the data stack RAM into <tt>N</tt>, and decrements the pointer into the data
    stack.

  - The <tt>store</tt> instruction requires the value to be stored and the
    address to which it is to be stored.  Since the address cannot be encoded as
    part of the <tt>store</tt> instruction and since the multi-byte
    <tt>store+</tt> and <tt>store-</tt> instructions require the address to
    remain on the stack as the rest of the stack is consumed, the address for
    the <tt>store</tt> instruction is in <tt>T</tt> while the data to be stored
    is in <tt>N</tt>.  I.e., if the value to be stored is in <tt>T</tt>, then
    the address where it is to be stored is then pushed onto the data stack and
    the <tt>store</tt> instruction is issued.  The <tt>store</tt> instruction
    drops the top of the data stack, leaving the value that was stored on the
    top of the data stack.  The <tt>store+</tt> and <tt>store-</tt> instruction
    differ from this in that the value in <tt>N</tt> is dropped from the data
    stack and the altered address is retained in <tt>T</tt>.

  - The <tt>outport</tt> instruction is similar to the <tt>store</tt>
    instruction in that the port number is pushed onto the data stack prior to
    the <tt>outport</tt> instruction which then drops the port number from the
    data stack.

  The return stack is similar except that only the top-most value, <tt>R</tt>,
  is retained in a dedicated register.

  Separate registers are used for <tt>N</tt> and <tt>R</tt> rather than the
  outputs of the RAM because there there are multiple sources for their values.

  Faster stack implementations won't improve the processor speed because the 3
  levels of logic required to implement the core are slower than the storing
  <tt>N</tt> or <tt>R</tt> into their stack bodies.

- Jump and Call Instructions:

  The large SRAM on the FPGAs can have registers for their input addresses and
  registers for their output data.  These registers are needed to extract the
  fastest memory speed possible.  While it is possible to design the processor
  ROM to avoid these registers, it reduces the achievable processor speed.
  Including these registers means that the instruction immediately after a jump,
  call, or return is always executed before control is tranfered to the new
  instruction address.

  Specifically, if a jump instruction changes the program counter during cycle
  *n*, then the new input address is registered at the memory input the end of
  that clock cycle, the resulting instruction is registered at the end of the
  next clock cycle (clock cycle *n*), and the new opcode is available during
  cycle *n*+2.

  This means that the instruction immediately following a jump or call
  instruction will be performed before the first instruction at the target of
  the jump or call.  For an unconditional jump or call, i.e., <tt>jump</tt> or
  <tt>call</tt>, this subsequent instruction will normally be a <tt>nop</tt>.
  However, for a conditional jump or call, i.e., a <tt>jumpc</tt> or
  <tt>callc</tt> instruction, this will normally be a <tt>drop</tt> that
  eliminates the conditional used to determine whether or not the branch was
  taken.

  Some examples are:

  - The following block shows a conditional jump and an unconditional jump being
    used for an "<tt>if&nbsp;...&nbsp;else&nbsp;..&nbsp;endif</tt>" block.  The
    <tt>.jump</tt> and <tt>.jumpc</tt> macros are used to encode pushing the 8
    lsb of the target address onto the stack and to encode the 5 msb into the
    <tt>jump</tt> or <tt>jumpc</tt> instruction.  The macros also add the
    default <tt>nop</tt> and <tt>drop</tt> respectively.

    ```
    ; determine which value to put on the stack based on the value in T
    ; ( f - u )
    .jumpc(true_case)
      0x80 .jump(end_case)
    :true_case
      0x37
    :end_case
    ```

    The condition on the top of the data stack is consumed by the drop following
    the initial <tt>jumpc</tt>.  If <tt>T</tt> is non-zero then <tt>0x37</tt>
    will be pushed onto the data stack.  Otherwise <tt>0x80</tt> will be pushed
    onto the data stack.  This can be written slightly more efficienty by
    replacing the default <tt>nop</tt> instruction in the <tt>.jump</tt> macro
    as follows:

    ```
    .jumpc(true_case) .jump(end_case,0x80) :true_case 0x37 :end_case
    ```

    since the <tt>.jump(end_case)</tt> includes a <tt>nop</tt> that can be
    replaced by the <tt>push</tt> that had immediately preceded it.  This
    reduces the total number of instructions from 8 to 7.

  - The following statement shows how a function can return a flag used by a
    second conditional call:

    ```
    .call(data_pending) .callc(process_data)
    ```

    Here, the <tt>data_pending</tt> function returns a true or false flag on the
    top of the data stack.  The subsequent <tt>callc</tt> then does additional
    data processing only if there is data to process.  The conditional returned
    by <tt>data_pending</tt> is dropped by the default <tt>drop</tt> instruction
    following the <tt>callc</tt> instruction.

- <a name="memory">Memory Operations</a>:

  The fetch and store memory access instructions are designed such that four
  banks of memory can be accessed, each of which can hold up to 256 bytes.  This
  allows up to a total of 1 kB of memory to be accessed by the processor.

  There are three variants of the fetch instruction and three variants of the
  store instruction.

  The simplest fetch instruction exchanges the top of the data stack with the
  value it had indexed from the memory bank encoded in the store instruction.
  For example, the two instruction sequence

  ```
  0x10 .fetch(0)
  ```

  has the effect of pushing the value from <tt>00_0001_0000</tt> onto the data
  stack where the leading two zeros in the 10-bit address are the bank number
  encoded in the <tt>fetch</tt> instruction.

  The simplest store instruction similarly uses the top of the data stack as the
  address within the memory bank and stores the value in the next-to-top of the
  data stack at that location.  For example, the four instruction
  sequence

  ```
  0x5A 0x10 .store(0) drop
  ```

  has the effect of storing the value <tt>0x5A</tt> in the memory address
  <tt>00_0001_0000</tt>.

  The remaining two fetch and two store instructions are designed to facilitate
  storing and fetching multi-byte values.  These vectorized fetch and store
  instructions increment or decrement the top of the stack while reading from or
  storing to memory.  For example, the instruction sequence

  ```
  0x13 .fetch-(0) .fetch-(0) .fetch-(0) .fetch(0)
  ```

  will push the memory values from <tt>00_0001_0011</tt>, <tt>00_0001_0010</tt>,
  <tt>00_0001_0001</tt>, and <tt>00_0001_0000</tt> onto the data stack with the
  value from <tt>00_0001_0000</tt> on the top of the stack.  The instruction
  sequence

  ```
  0x10 .store+(0) .store+(0) .store+(0) .store(0) drop
  ```

  has the reverse effect in that it stores the top four values on the stack in
  memory with the value that had been at the top of the stack being stored at
  address <tt>00_0001_000</tt>.  That is, it has the effect of storing the
  values from the four-fetch instruction sequence into memory and preserving
  their order.

  If the values were in the reverse order on the stack the instruction sequence
  would have been

  ```
  0x13 .store-(0) .store-(0) .store-(0) .store-(0) drop
  ```

  In practice, the <tt>.fetch</tt> and <tt>.store</tt> macros do not use a
  hard-wired number for the bank address.  Instead the memory bank is specified
  by a symbolic name.  For example, a memory is defined in the micro controller
  architecture file using a statement such as:

  ```
  MEMORY RAM ram 32
  ```

  which defines a RAM named "<tt>ram</tt>" and allocates 32 bytes of
  storage.  The corresponding RAM in the assembler code is then selected by the
  directive:

  ```
  .memory RAM ram
  ```

  and variables within this bank of memory are defined using the
  "<tt>.variable</tt>" directive as follows:

  ```
  .variable single_value 0
  .variable multi_count 0*2
  ```

  The first of these defines "<tt>single_value</tt>" to be a single-byte value
  initialized to zero and the second defines "<tt>multi_count</tt>" to be a two
  byte value initialized to 0.  Variable order is preserved by the
  assembler.

  As an example, the following assembly code will initialize this block of
  memory to zero:

  ```
  ${size['ram']} :loop 0 swap .store-(ram) .jumpc(loop,nop) drop
  ```

  Note that the memory size is not hard-wired into the assembly code but is
  accessed through the calculation "<tt>${size['ram']}</tt>".  Also, since the
  <tt>.store-</tt> macro decrements the top of the stack before the conditional
  jump, the last value stored in memory before the loop exits will have been
  stored at address <tt>0x01</tt>.  However, since the size must be a power of
  two, the first value stored will be at the effective address <tt>0x00</tt>.
  The loop itself is 6 instructions.  This can be reduced to 5 instructions by
  moving the <tt>.store-(ram)</tt> instruction immediately after the
  <tt>jumpc</tt> instruction as follows:

  ```
  ${size['ram']-1} :loop 0 swap .jumpc(loop,.store-(ram)) drop
  ```

  Now the last iteration of the loop occurs when the memory index is <tt>0</tt>
  instead of <tt>-1</tt>, so the first memory index can be at the end of the
  memory as stated by the <tt>${size['ram']-1}$</tt> calculation.

  In both cases, the optional argument to the <tt>.jumpc</tt> macro is required
  so that the memory address is not dropped from the data stack after the
  conditional is tested.  The equivalent operation for the first formulation
  without replacing the <tt>drop</tt> instruction with a <tt>nop</tt>
  instruction would be:

  ```
  ${size['ram']} :loop 0 swap .store-(ram) dup .jumpc(loop,drop) drop
  ```

  where the <tt>drop</tt> has been explicitely included.

  Memories can be either "<tt>RAM</tt>" or "<tt>ROM</tt>" and must be declared
  as the same type in the architecture file and in the assembler files.  Within
  the assembler source the "<tt>.memory</tt>" directive can be repeated so that
  variables in one memory bank can be defined in multiple assembler files.  The
  "<tt>.memory</tt>" directive must be repeated if the source file changes and
  after function definitions.

  The Forth language requires that the MSB of multi-word values be stored on the
  top of the data stack.  Using the <tt>.store+</tt> and <tt>.fetch-</tt>
  instructions to write to and read from memory will keep the corresponding MSB
  at the top of the stack and as the first byte in memory.  If the LSB is at the
  top of the data stack then the <tt>.store-</tt> instruction can be used to
  store it in the Forth-preferred order.

  The macros facilitating memory operations are listed in [macros](#macros).

<a name="opcodes"></a>
OPCODES
=======

This section documents the opcodes.

Alphabetic listing:

[&](#amp),
[+](#plus),
[+c](#plus_c),
[-](#minus),
[-1<>](#minus_1_not_equal),
[-1=](#minus_1_equal),
[-c](#minus_c),
[0<>](#0_not_equal),
[0=](#0_equal),
[0>>](#0_gt_gt),
[1+](#1_plus),
[1-](#1_minus),
[1>>](#1_gt_gt),
[<<0](#lt_lt_0),
[<<1](#lt_lt_1),
[<<msb](#lt_lt_msb),
[>r](#gt_r),
[^](#carot),
[call](#call),
[callc](#callc),
[dis](#dis),
[drop](#drop),
[dup](#dup),
[ena](#ena),
[fetch](#fetch),
[fetch+](#fetch_plus),
[fetch-](#fetch_minus),
[inport](#inport),
[jump](#jump),
[jumpc](#jumpc),
[lsb>>](#lsb_gt_gt),
[msb>>](#msb_gt_gt),
[nip](#nip),
[nop](#nop),
[or](#or),
[outport](#outport),
[over](#over),
[push](#push),
[r>](#r_gt),
[r@](#r_at),
[return](#return),
[store](#store),
[store+](#store_plus),
[store-](#store_minus),
[swap](#swap)

<a name="opcode_mapping">Opcode Mapping</a>
-------------------------------------------

| Opcode                        |  8  |  7  |     |  6  |  5  |  4  |  3  |     |  2  |  1  |  0  | Description |
| ----------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------- |
| [nop](#nop)                   |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  0  |  0  |  0  | no operation |
| [<<0](#lt_lt_0)               |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  0  |  0  |  1  | left shift 1 bit and bring in a 0 |
| [<<1](#lt_lt_1)               |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  0  |  1  |  0  | left shift 1 bit and bring in a 1 |
| [<<msb](#lt_lt_msb)           |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  0  |  1  |  1  | left shift 1 bit and rotate the msb into the lsb |
| [0>>](#0_gt_gt)               |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  1  |  0  |  0  | right shift 1 bit and bring in a 0 |
| [1>>](#1_gt_gt)               |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  1  |  0  |  1  | right shift 1 bit and bring in a 1 |
| [msb>>](#msb_gt_gt)           |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  1  |  1  |  0  | right shift 1 bit and keep the msb the same |
| [lsb>>](#lsb_gt_gt)           |  0  |  0  |     |  0  |  0  |  0  |  0  |     |  1  |  1  |  1  | right shift 1 bit and rotate the lsb into the msb |
| [dup](#dup)                   |  0  |  0  |     |  0  |  0  |  0  |  1  |     |  0  |  0  |  0  | push a duplicate of the top of the data stack onto the data stack |
| [r@](#r_at)                   |  0  |  0  |     |  0  |  0  |  0  |  1  |     |  0  |  0  |  1  | push a duplicate of the top of the return stack onto the data stack |
| [over](#over)                 |  0  |  0  |     |  0  |  0  |  0  |  1  |     |  0  |  1  |  0  | push a duplicate of the next-to-top of the data stack onto the data stack |
| [+c](#plus_c)                 |  0  |  0  |     |  0  |  0  |  0  |  1  |     |  0  |  1  |  1  | push the carry bit for an addition onto the data stack |
| [-c](#minus_c)                |  0  |  0  |     |  0  |  0  |  0  |  1  |     |  1  |  1  |  1  | push the carry bit for a subtraction onto the data stack |
| [swap](#swap)                 |  0  |  0  |     |  0  |  0  |  1  |  0  |     |  0  |  1  |  0  | swap the top and the next-to-top of the data stack |
| [+](#plus)                    |  0  |  0  |     |  0  |  0  |  1  |  1  |     |  0  |  0  |  0  | pop the stack and replace the top with N+T |
| [-](#minus)                   |  0  |  0  |     |  0  |  0  |  1  |  1  |     |  1  |  0  |  0  | pop the stack and replace the top with N-T |
| [dis](#dis)                   |  0  |  0  |     |  0  |  0  |  1  |  1  |     |  0  |  0  |  0  | disable interrupts |
| [ena](#ena)                   |  0  |  0  |     |  0  |  0  |  1  |  1  |     |  0  |  0  |  1  | enable interrupts |
| [0=](#0_equal)                |  0  |  0  |     |  0  |  1  |  0  |  0  |     |  0  |  0  |  0  | replace the top of the stack with "<tt>0xFF</tt>" if it is "<tt>0x00</tt>" (i.e., it is zero), otherwise replace it with "<tt>0x00</tt>" |
| [0<>](#0_not_equal)           |  0  |  0  |     |  0  |  1  |  0  |  0  |     |  0  |  0  |  1  | replace the top of the stack with "<tt>0xFF</tt>" if it is not "<tt>0x00</tt>" (i.e., it is non-zero), otherwise replace it with "<tt>0x00</tt>" |
| [-1=](#minus_1_equal)         |  0  |  0  |     |  0  |  1  |  0  |  0  |     |  0  |  1  |  0  | replace the top of the stack with "<tt>0xFF</tt>" if it is "<tt>0xFF</tt>" (i.e., it is all ones), otherwise replace it with "<tt>0x00</tt>" |
| [-1<>](#minus_1_not_equal)    |  0  |  0  |     |  0  |  1  |  0  |  0  |     |  0  |  1  |  1  | replace the top of the stack with "<tt>0xFF</tt>" if it is not "<tt>0xFF</tt>" (i.e., it is not all ones), otherwise replace it with "<tt>0x00</tt>" |
| [return](#return)             |  0  |  0  |     |  0  |  1  |  0  |  1  |     |  0  |  0  |  0  | return from a function call |
| [inport](#inport)             |  0  |  0  |     |  0  |  1  |  1  |  0  |     |  0  |  0  |  0  | replace the top of the stack with the contents of the specified input port |
| [outport](#outport)           |  0  |  0  |     |  0  |  1  |  1  |  1  |     |  0  |  0  |  0  | write the next-to-top of the data stack to the output port specified by the top of the data stack |
| [>r](#gt_r)                   |  0  |  0  |     |  1  |  0  |  0  |  0  |     |  0  |  0  |  0  | Pop the top of the data stack and push it onto the return stack |
| [r>](#r_gt)                   |  0  |  0  |     |  1  |  0  |  0  |  1  |     |  0  |  0  |  1  | Pop the top of the return stack and push it onto the data stack |
| [&](#amp)                     |  0  |  0  |     |  1  |  0  |  1  |  0  |     |  0  |  0  |  0  | pop the stack and replace the top with N & T |
| [or](#or)                     |  0  |  0  |     |  1  |  0  |  1  |  0  |     |  0  |  0  |  1  | pop the stack and replace the top with N \| T |
| [^](#carot)                   |  0  |  0  |     |  1  |  0  |  1  |  0  |     |  0  |  1  |  0  | pop the stack and replace the top with N ^ T |
| [nip](#nip)                   |  0  |  0  |     |  1  |  0  |  1  |  0  |     |  0  |  1  |  1  | pop the next-to-top from the data stack |
| [drop](#drop)                 |  0  |  0  |     |  1  |  0  |  1  |  0  |     |  1  |  0  |  0  | drop the top value from the stack |
| [1+](#1_plus)                 |  0  |  0  |     |  1  |  0  |  1  |  1  |     |  0  |  0  |  0  | Add 1 to T |
| [1-](#1_minus)                |  0  |  0  |     |  1  |  0  |  1  |  1  |     |  1  |  0  |  0  | Subtract 1 from T |
| [store](#store)               |  0  |  0  |     |  1  |  1  |  0  |  0  |     |  0  |  m  |  m  | Store N in the T'th entry in bank "<tt>mm</tt>", drop the top of the data stack |
| [fetch](#fetch)               |  0  |  0  |     |  1  |  1  |  0  |  1  |     |  0  |  m  |  m  | Exchange the top of the stack with the T'th value from bank "<tt>mm</tt>" |
| [store+](#store_plus)         |  0  |  0  |     |  1  |  1  |  1  |  0  |     |  0  |  m  |  m  | Store N in the T'th entry in bank "<tt>mm</tt>", nip the data stack, and increment T |
| [store-](#store_minus)        |  0  |  0  |     |  1  |  1  |  1  |  0  |     |  1  |  m  |  m  | Store N in the T'th entry in bank "<tt>mm</tt>", nip the data stack, and decrement T |
| [fetch+](#fetch_plus)         |  0  |  0  |     |  1  |  1  |  1  |  1  |     |  0  |  m  |  m  | Push the T'th entry from bank "<tt>mm</tt>" into the data stack as N and increment T |
| [fetch-](#fetch_minus)        |  0  |  0  |     |  1  |  1  |  1  |  1  |     |  1  |  m  |  m  | Push the T'th entry from bank "<tt>mm</tt>" into the data stack as N and decrement T |
| [jump](#jump)                 |  0  |  1  |     |  0  |  0  |  x  |  x  |     |  x  |  x  |  x  | Jump to the 13-bit address "<tt>x_xxxx_TTTT_TTTT</tt>" |
| [jumpc](#jumpc)               |  0  |  1  |     |  0  |  1  |  x  |  x  |     |  x  |  x  |  x  | Conditionally jump to the 13-bit address "<tt>x_xxxx_TTTT_TTTT</tt>" |
| [call](#call)                 |  0  |  1  |     |  1  |  0  |  x  |  x  |     |  x  |  x  |  x  | Call the function at the 13-bit address "<tt>x_xxxx_TTTT_TTTT</tt>" |
| [callc](#callc)               |  0  |  1  |     |  1  |  1  |  x  |  x  |     |  x  |  x  |  x  | Conditionally call the function at the 13-bit address "<tt>x_xxxx_TTTT_TTTT</tt>" |
| [push](#push)                 |  1  |  x  |     |  x  |  x  |  x  |  x  |     |  x  |  x  |  x  | Push the 8-bit value "<tt>xxxx_xxxx</tt>" onto the data stack. |

**Nomenclature:**

| name | description |
| ---- | ----------- |
| <tt>PC</tt> | the program counter |
| <tt>T</tt> | the top of the data stack, stored in an 8-bit register |
| <tt>N</tt> | the next-to-top of the data stack, stored in an 8-bit register |
| <tt>stack</tt> | the pointer into the data stack |
| <tt>R</tt> | the top of the return stack, stored in a register |
| <tt>return</tt> | the pointer into the return stack |

<tt>N <= \*stack--</tt> means to move the value from the stack into <tt>N</tt>
and to decrement the pointer into the data stack.

<tt>\*++stack <= N</tt> means to increment the data stack pointer and to store
<tt>N</tt> in that location.

<tt>R</tt> wide enough to store data and to store the PC.

<tt>R <= \*return--</tt> and <tt>\*++return <= R</tt> are similar but refer to
the top of the return stack and the pointer into the return stack RAM.

<a name="amp">Instruction:  &</a>
-----------------------------------

**Description:**

Pop the data stack and replace the top with the bitwise and of the top and
next-to-top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T & N
N <= *stack--
```

<a name="plus">Instruction:  +</a>
-------------------------------

**Description:**

Pop the data stack and replace the top with the 8-bit sum of the top and
next-to-top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N + T
N <= *stack--
```

<a name="plus_c">Instruction:  +c</a>
---------------------------------

**Description:**

Push the carry bit from the 9-bit addition of the 8-bit unsigned next-to-top and
top of the data stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if the msb of { 0, N } + { 0, T } is 1
  T <= 0x01
else
  T <= 0x00
N <= T
*++stack <= N
```

<a name="minus">Instruction:  -</a>
-------------------------------

**Description:**

Pop the data stack and replace the top with the difference of the top and
next-to-top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N - T
N <= *stack--
```

<a name="minus_1_not_equal">Instruction:  -1<></a>
-------------------------------------

**Description:**

Set the top of the stack to all ones if it was not all ones, otherwise set it to
all zeros.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if T != 0xFF
  T <= 0xFF
else
  T <= 0x00
N and stack unchanged
```

<a name="minus_1_equal">Instruction:  -1=</a>
-----------------------------------

**Description:**

Set the top of the stack to all ones if it was all ones, otherwise set it to all
zeros.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if T == 0xFF
  T <= 0xFF
else
  T <= 0x00
N and stack unchanged
```

<a name="minus_c">Instruction:  -c</a>
---------------------------------

**Description:**

Push the carry bit from the 9-bit subtraction of the 8-bit unsigned top from the
next-to-top of the data stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if the msb of { 0, N } - { 0, T } is 1
  T <= 0x01
else
  T <= 0x00
N <= T
*++stack <= N
```

<a name="0_not_equal">Instruction:  0<></a>
-----------------------------------

**Description:**

Set the top of the stack to all ones if it was not all zeros, otherwise set it
to all zeros.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if T != 0x00
  T <= 0xFF
else
  T <= 0x00
N and stack unchanged
```

<a name="0_equal">Instruction:  0=</a>
---------------------------------

**Description:**

Set the top of the stack to all ones if it was all zeros, otherwise set it to
all zeros.

**Operation:**

```
PC <= PC + 1
R and return unchanged
if T == 0x00
  T <= 0xFF
else
  T <= 0x00
N and stack unchanged
```

<a name="0_gt_gt">Instruction:  0>></a>
-----------------------------------------

**Description:**

Right shift the top of the stack one bit, replacing the left-most bit with a
zero.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { 0, T[7], T[6], ..., T[1] }
N and stack unchanged
```

<a name="1_plus">Instruction:  1+</a>
---------------------------------

**Description:**

Increment the top of the data stack by 1.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T + 1
N and stack unchanged
```

<a name="1_minus">Instruction:  1-</a>
---------------------------------

**Description:**

Decrement the top of the data stack by 1.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T - 1
N and stack unchanged
```

<a name="1_gt_gt">Instruction:  1>></a>
-----------------------------------------

**Description:**

Right shift the top of the stack one bit, replacing the left-most bit with a
one.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { 1, T[7], T[6], ..., T[1] }
N and stack unchanged
```

<a name="lt_lt_0">Instruction:  <<0</a>
-----------------------------------------

**Description:**

Left shift the top of the stack one bit, replacing the right-most bit with a
zero.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { T[6], T[5], ..., T[0], 0 }
N and stack unchanged
```

<a name="lt_lt_1">Instruction:  <<1</a>
-----------------------------------------

**Description:**

Left shift the top of the stack one bit, replacing the right-most bit with a
one.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { T[6], T[5], ..., T[0], 1 }
N and stack unchanged
```

<a name="lt_lt_msb">Instruction:  &lt;&lt;msb</a>
---------------------------------------------

**Description:**

Rotate the top of the data stack left one bit.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { T[6], T[5], ..., T[0], T[7] }
N and stack unchanged
```

<a name="gt_r">Instruction:  &gt;r</a>
------------------------------------

**Description:**

Push the top of the data stack onto the return stack and pop the data stack.

**Operation:**

```
PC <= PC + 1
*++return <= R
R <= T
T <= N
N <= *stack--
```

<a name="carot">Instruction:  ^</a>
-------------------------------

**Description:**

Pop the data stack and replace the top with the bitwise exclusive or of the
top and next-to-top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T ^ N
N <= *stack--
```

<a name="call">Instruction:  call</a>
-------------------------------------

**Description:**

Call the function at the address constructed from the 5 lsb of the opcode and
the top of the data stack.  Discard the top of the data stack and push the PC
onto the return stack.

**Operation:**

```
PC <= { opcode[4], ..., opcode[0], T[7], T[6], ..., T[0] }
*++return <= R
R <= PC + 2
T <= N
N <= *stack--
```

**Special:**

The address pushed onto the return stack is two instructions after the address
of the <tt>call</tt> instruction.

The <tt>.call</tt> macro must be used to perform function calls.

Interrupts are disabled during the clock cycle immediately following a call
instruction.

<a name="callc">Instruction:  callc</a>
---------------------------------------

**Description:**

Conditionally call the function at the address constructed from the 5 lsb of the
opcode and the top of the data stack.  Discard the top of the data stack and
conditionally push the next PC onto the return stack.

**Operation:**

```
if N != 0 then
  PC <= { opcode[4], ..., opcode[0], T[7], T[6], ..., T[0] }
  *++return <= R
  R <= PC + 2
else
  PC <= PC + 1
  R and return unchanged
endif
T <= N
N <= *stack--
```

**Special:**

The address pushed onto the return stack is two instructions after the address
of the <tt>call</tt> instruction.

The <tt>.callc</tt> macro must be used to perform conditional function calls.

Interrupts are disabled during the clock cycle immediately following a callc
instruction.

<a name="dis">Instruction:  dis</a>
-----------------------------------

**Description:**

Disable interrupts.

**Operation:**

```
PC <= PC + 1
R, return, T, N, and stack unchanged
```

**Special:**

This instruction is only available if interrupts are enabled in computer
architecture.

<a name="drop">Instruction:  drop</a>
-------------------------------------

**Description:**

Pop the data stack, discarding the value that had been on the top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N
N <= *stack--
```

<a name="dup">Instruction:  dup</a>
-----------------------------------

**Description:**

Push a duplicate of the top of the data stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T
N <= T
*++stack <= N
```

<a name="ena">Instruction:  ena</a>
-----------------------------------

**Description:**

Enable interrupts.

**Operation:**

```
PC <= PC + 1
R, return, T, N, and stack unchanged</br>
```

**Special:**

This instruction is only available if interrupts are enabled in computer
architecture.

<a name="fetch">Instruction:  fetch</a>
---------------------------------------

**Description:**

Replace the top of the data stack with an 8 bit value from memory.  The memory
bank is specified by the two least-significant bits of the opcode.  The index
within the memory bank is specified by the the top of the stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= memory[T] where the memory bank is specified by <tt>opcode[1:0]</tt>
N and stack unchanged
```

<a name="fetch_plus">Instruction:  fetch+</a>
-----------------------------------------

**Description:**

Push the T'th entry from the specified memory onto the data stack as N and
increment the top of the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T + 1
N <= memory[T] where the memory bank is specified by <tt>opcode[1:0]</tt>
*++stack <= N
```

<a name="fetch_minus">Instruction:  fetch-</a>
-----------------------------------------

**Description:**

Push the T'th entry from the specified memory onto the data stack as N and
decrement the top of the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T - 1
N <= memory[T] where the memory bank is specified by <tt>opcode[1:0]</tt>
*++stack <= N
```

<a name="inport">Instruction:  inport</a>
-----------------------------------------

**Description:**

Replace the top of the data stack with the value from the port specified by the
top of the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= input_port[T]
N and stack unchanged
```

**Special:**

The recommended procedure to read from an input port is to use the
"<tt>[.inport](#dot_inport)</tt>" macro.

<a name="jump">Instruction:  jump</a>
-------------------------------------

**Description:**

Jump to the address constructed from the 5 lsb of the opcode and the top of the
data stack.  Discard the top of the data stack.

**Operation:**

```
PC <= { opcode[4], ..., opcode[0], T[7], T[6], ..., T[0] }
R and return unchanged
T <= N
N <= *stack--
```

**Special:**

The <tt>.jump</tt> macro must be used to perform jumps.

Interrupts are disabled during the clock cycle immediately following a jump
instruction.

<a name="jumpc">Instruction:  jumpc</a>
---------------------------------------

**Description:**

Jump to the address constructed from the the 5 lsb of the opcode and the top of
the data stack if the next-to-top of the data stack is non-zero.  Discard the
top of the data stack.

**Operation:**

```
if N != 0
  PC <= { opcode[4], ..., opcode[0], T[7], T[6], ..., T[0] }
else
  PC <= PC + 1
R and return unchanged
T <= N
N <= *stack--
```

**Special:**

The <tt>.jumpc</tt> macro must be used to perform conditional jumps.

Interrupts are disabled during the clock cycle immediately following a jumpc
instruction.

<a name="lsb_gt_gt">Instruction:  lsb>></a>
---------------------------------------------

**Description:**

Rotate the top of the data stack right one bit.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { T[0], T[7], T[6], ..., T[1] }
N and stack unchanged
```

<a name="msb_gt_gt">Instruction:  msb>></a>
---------------------------------------------

**Description:**

Right shift the top of the stack one bit, preserving the value of the left-most
bit.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= { T[7], T[7], T[6], ..., T[1] }
N and stack unchanged
```

<a name="nip">Instruction:  nip</a>
-----------------------------------

**Description:**

Discard the next-to-top value on the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T
N <= *stack--
```

<a name="nop">Instruction:  nop</a>
-----------------------------------

**Description:**

No operation.

**Operation:**

```
PC <= PC + 1
R, return, T, N, and stack unchanged
```

<a name="or">Instruction:  or</a>
---------------------------------

**Description:**

Pop the data stack and replace the top with the bitwise or of the top and
next-to-top.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T or N
N <= *stack--
```

<a name="outport">Instruction:  outport</a>
-------------------------------------------

**Description:**

Write the next-to-top of the data stack to the output port specified by the top
of the data stack and pop the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N
N <= *stack--
outport[T] <= N
```

**Special:**

The recommended procedure to write to an output port is to use the
<tt>[.outport](#dot_outport)</tt> and <tt>[.outstrobe](#dot_outstrobe)</tt> macros.
The <tt>.outport</tt> macro is required for output ports with bit widths and
optional strobes, the <tt>.outstrobe</tt> macro is required for output ports
that are strobe only.

<a name="over">Instruction:  over</a>
-------------------------------------

**Description:**

Push the next-to-top of the data stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N
N <= T
*++stack <= N
```

<a name="push">Instruction:  push</a>
-------------------------------------

**Description:**

Push the specified 8-bit value onto the 8-bit stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= opcode[7:0]
N <= T
*++stack <= N
```

<a name="r_gt">Instruction:  r&gt;</a>
------------------------------------

**Description:**

Pop the top of the return stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R <= *return--
T <= R
N <= T
*++stack <= N
```

<a name="r_at">Instruction:  r@</a>
---------------------------------

**Description:**

Push the top of the return stack onto the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= R
N <= T
*++stack <= N
```

<a name="return">Instruction:  return</a>
-----------------------------------------

**Description:**

Popd the top of the return stack into the PC.

**Operation:**

```
PC <= R
R <= *return--
T, N, and stack unchanged
```

**Special:**

The <tt>[.return](#dot_return)</tt> macro must be used to perform function returns.

Interrupts are disabled during the clock cycle immediately following a
<tt>return</tt> instruction.

<a name="store">Instruction:  store</a>
---------------------------------------

**Description:**

Store the next-to-top of the data stack at the memory location specified by the
top of the data stack and the 2-bit memory index embedded in the <tt>store</tt>
instruction and pop the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N
N <= *stack--
memory[T] <= N where the memory bank is specified by <tt>opcode[1:0]</tt>
```

**Special:**

The <tt>[.store](#dot_store)</tt> macro must be used to incorporate the memory bank
index into the instruction.

<a name="store_plus">Instruction:  store+</a>
-----------------------------------------

**Description:**

Store the next-to-top of the data stack at the memory location specified by the
top of the data stack and the 2-bit memory index embedded in the <tt>store+</tt>
instruction, increment the top of the data stack, and drop the next-to-top from
the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T + 1
N <= *stack--
memory[T] <= N where the memory bank is specified by <tt>opcode[1:0]</tt>
```

**Special:**

The <tt>[.store+](#dot_store_plus)</tt> macro must be used to incorporate the memory bank
index into the instruction.

<a name="store_minus">Instruction:  store-</a>
-----------------------------------------

**Description:**

Store the next-to-top of the data stack at the memory location specified by the
top of the data stack and the 2-bit memory index embedded in the <tt>store-</tt>
instruction, decrement the top of the data stack, and drop the next-to-top from
the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= T - 1
N <= *stack--
memory[T] <= N where the memory bank is specified by <tt>opcode[1:0]</tt>
```

**Special:**

The <tt>[.store-](#dot_store_minus)</tt> macro must be used to incorporate the memory bank
index into the instruction.

<a name="swap">Instruction:  swap</a>
-------------------------------------

**Description:**

Swap the top two values on the data stack.

**Operation:**

```
PC <= PC + 1
R and return unchanged
T <= N
N <= T
stack unchanged
```

<a name="assembler"></a>
Assembler
=========

This section describes the contents of an assembly language file and the
instruction format.

The following is a simple, 10 instruction sequence, demonstrating a
loop:

```
; consume 256*6+3 clock cycles
0 :l00 1 - dup .jumpc(l00) drop .return
```

This looks a lot like Forth code in that the operations are single words and are
strung together on a single line.  Unlike traditional assembly languages, there
are no source and destination registers, so most of the operations for this
stack-based processor simply manipulate the stack.  This can make it easier to
see the body of the assembly code since an instruction sequence can occupy a
single line of the file instead of tens of lines of vertical space.  The
exceptions to the single-operand format are labels, such as the "<tt>:l00</tt>"
which are declared with a single "<tt>:</tt>" immediately followed by the name
of the label with no intervening spaces; jump instructions such as the 3
instruction, "<tt>push&nbsp;jumpc&nbsp;drop</tt>", sequence created by the
"<tt>.jumpc</tt>" macro; and the 2 operand, "<tt>return&nbsp;nop</tt>", sequence
created by the "<tt>.return</tt>" macro.  The "<tt>.jump</tt>",
"<tt>.jumpc</tt>", "<tt>.call</tt>", and "<tt>.callc</tt>", macros are
pre-defined in the assembler and ensure that the correct sequence of operands is
generated for the jump, conditional jump, function call, and conditional
function call instructions.  Similarly, the "<tt>.return</tt>" macro is
pre-defined in the assember and ensures that the correct sequence of operations
is done for returning from a called function.

Memory does not have to be declared for the processor.  For example, the LED
flashing examples required no variable or constant storage, and therefore do not
declare or consume resources required for memory.  Variable declarations are
done within pages declared using the "<tt>.memory</tt>" and "<tt>.variable</tt>"
macros as follows:

```
.memory RAM myRAM
.variable save_count
.variable old_count 0x0a
.variable out_string 0*16
```

Here, the "<tt>.memory&nbsp;RAM</tt>" macro declares the start of a page of RAM.
The RAM will be allocated as prescribed in the processor description file.
Here, the variable "<tt>save_count</tt>" will be at memory address
"<tt>0x00</tt>" and will occupy a single, uninitialized slot of memory.  The
variable "<tt>old_count</tt>" will also occupy a single slot of memory at
address "<tt>0x01</tt>" and will be initialized to the hex value
"<tt>0x0a</tt>".  Note that if the processor is reset that this value will not
be re-initialized.  Finally, the variable "<tt>out_string</tt>" will start at
address "<tt>0x02</tt>" and will occupy 16 bytes of memory.

A ROM is declared similarly.  For example,

```
.memory ROM myROM
.variable hex_to_ascii '0' '1' '2' '3' '4' '5' '6' '7' ; first 8 characters
                       '8' '9' 'A' 'B' 'C' 'D' 'E' 'F' ; second 8 characters
```

declares a page of ROM with the 16 element array <tt>hex_to_ascii</tt>
initialized with the values required to convert a 4-bit value to the
corresponding hex ascii character.  This also illustrates how the initialization
sequence (and length determination) can be continued on multiple lines.  If
"<tt>outbyte</tt>" is a function that outputs a single byte to a port, then the
hex value of a one-byte value can be output using the following sequence:

```
dup 0>> 0>> 0>> 0>> hex_to_ascii + .fetch(myROM) .call(outbyte)
0x0F and hex_to_ascii + .fetch(myROM) .call(outbyte)
```

The first line extracts the most significant nibble of the byte by right
shifting it 4 times while filling the left with zeros, adding that value to the
address "<tt>hex_to_ascii</tt>" to get the corresponding ascii character,
fetching that value from the ROM named "<tt>myROM</tt>", and then calling the
function that consumes that value on the top of the stack while sending it to
the output port (this takes 11 instructions).  The second line extracts the
least significant nibble using an "<tt>and</tt>" instructions and then proceeds
similarly (this takes 8 instructions).  The "<tt>.fetch</tt>" macro generates
the "<tt>fetch</tt>" instruction using the 3 bit value of "<tt>myROM</tt>" as
part of the memory address generation.


The "<tt>.store</tt>" macro is similar to the "<tt>.fetch</tt>" macro except
that the assembler will generate an error message if a "<tt>store</tt>"
operation is attempted to a ROM page.


Two additional variants of the "<tt>.fetch</tt>" and "<tt>.store</tt>" macros
are provided.  The first, "<tt>.fetch(save_count)</tt>" will generate the 2
instruction sequence consisting of (1) the instruction to push the 8 bit address
of "<tt>save_count</tt>" onto the stack and (2) the "<tt>fetch</tt>" instruction
with the 3 bit page number associated with "<tt>save_count</tt>".  This helps
ensure the correct page is used when accessing "<tt>save_count</tt>".  The
instruction "<tt>store(save_count)</tt>" is similar.  The second variant of
these is for indexed fetches and stores.  For example, the preceding example to
convert the single-byte value to hex could be written as

```
dup 0>> 0>> 0>> 0>> .fetchindexed(hex_to_ascii) .call(outbyte)
0x0F and .fetchindexed(hex_to_ascii) .call(outbyte)
```

Here, the macro "<tt>.fetchindexed</tt>" consumes the top of the data stack as
an index into the array variable "<tt>hex_to_ascii</tt>" and pushes the indexed
value onto the top of the data stack.

The "<tt>store</tt>" instruction must be followed by a drop instruction since it
consumes the top two values in the data stack.  The "<tt>.store</tt>" and
"<tt>.storeindexed</tt>" macros generate this drop function automatically.
Thus, "<tt>.store(myRAM)</tt>" generates the 2 instruction sequence
"<tt>store&nbsp;drop</tt>", "<tt>.store(save_count)</tt>" generates the 3
instruction sequence "<tt>save_count&nbsp;store&nbsp;drop</tt>", and
"<tt>.storeindexed(out_string)</tt>" generates the 4 instruction sequence
"<tt>out_string&nbsp;+&nbsp;store&nbsp;drop</tt>", all with the proviso that the
"<tt>store</tt>" instructions include the 3 bit address
"<tt>myRAM</tt>".

Program Structure
-----------------

TODO

Directives
----------

Alphebetic listing:
[.constant](#dot_constant),
[.function](#dot_function),
[.include](#dot_include),
[.interrupt](#dot_interrupt),
[.main](#dot_main),
[.memory](#dot_memory),
and
[.variable](#dot_variable).

### <a name="dot_constant">.constant</a>

**Description:**

This directive defines a single constant with the specified body.

**Format:**

```
.constant name body
```

where <tt>name</tt> is an a previously undefined symbol and <tt>body</tt> is a
mandatory list of one or more bytes of data.

**Example:**

Determine whether or not a file has already been included.  If it hasn't then
indicate that it has been included and define it's body.

```
.IFNDEF FILE_S_INCLUDED
.constant FILE_S_INCLUDED 0
...
.ENDIF
```

Set a constant to a computed value:

```
.constant A ${4*3+2}
```

Set a constant to a string:

```
.constant STRING N"Hello World!"
```

### <a name="dot_function">.function</a>

**Description:**

Define a function.

**Format:**

```
.function name body
```

**Special:**

The function must end in a return or an unconditional jump.

**Example:**

```
; Add 5 to the top of the data stack.
; ( u - u+5 )
.function add5 5 .return(+)
```

### <a name="dot_include">.include</a>

**Description:**

Include the source code from the specified assembly file.

**Format:**

```
.include filename.s
```

### <a name="dot_interrupt">.interrupt</a>

**Description:**

Define the interrupt handler function.

**Format:**

```
.interrupt body
```

**Special:**

The function must end in a return or an unconditional jump.

**Example:**

Count the number of interrupts encountered.

```
.memory RAM ram
.variable interrupt_count
; Count the number of interrupts encountered.
.interrupt
  .fetchvalue(interrupt_count) 1+ .storevalue(interrupt_count) .return
```

### <a name="dot_main">.main</a>

**Description:**

Define the main function, i.e., the function called when the micro controller
starts.

**Format:**

```
.main body
```

**Special:**

The main function must end in an unconditional jump.

**Example:**

See the <tt>examples</tt> directory.

### <a name="dot_memory">.memory</a>

**Description:**

Identify the memory used for subsequent variable definitions.

**Format:**

```
.memory TYPE name
```

where <tt>TYPE</tt> is either <tt>RAM</tt> or <tt>ROM</tt> and <name> is the
name of the memory specified in the architecture file.

**Special:**

The memory <tt>TYPE</tt> and <tt>name</tt> must match their definition in the
architecture file.

**Example:**

See [.variable](#dot_variable).

### <a name="dot_variable">.variable</a>

**Description:**

Declare a variable, its length, and its initial value.

**Format:**

```
.variable name {value[\*count]}+
```

where <tt>value</tt> is a single-byte value, <tt>count</tt> is an optional
repetition count, and the <tt>value</tt> or <tt>value\*count</tt> entry can be
repeated.  Strings can also be used to initialize the variable.

**Example:**

Declare and initialize a single-byte value

```
.variable five 5
```

Declare and initialize a 5 element array with the last 3 elements initialized to
zero.

```
.variable five_element 1 2 0*3
```

Declare an array to convert 4-bit values to their hex character.

```
.variable nibble2hex "0123456789ABCDEF"
```

<a name="macros"></a>
Macros
======

Alphebetic listing:
[.call](#dot_call),
[.callc](#dot_callc),
[.fetch](#dot_fetch),
[.fetch+](#dot_fetch_plus),
[.fetch-](#dot_fetch_minus),
[.fetchindexed](#dot_fetchindexed),
[.fetchvalue](#dot_fetchvalue),
[.fetchvector](#dot_fetchvector),
[.inport](#dot_inport),
[.jump](#dot_jump),
[.jumpc](#dot_jumpc),
[.outport](#dot_outport),
[.outstrobe](#dot_outstrobe),
[.return](#dot_return),
[.store](#dot_store),
[.store+](#dot_store_plus),
[.store-](#dot_store_minus),
[.storeindexed](#dot_storeindexed),
[.storevalue](#dot_storevalue),
and
[.storevector](#dot_storevector).

### <a name="dot_call"></tt>.call(function[,instruction])</tt></a>

- <tt>function</tt> is the name of a function

- <tt>instruction</tt> is a single-cycle instruction

  Default:  <tt>nop</tt>

This generates the following 3 instruction sequence to [call](#call) the
specified function:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>function[7:0]</tt> | push the 8 lsb of the function address onto the data stack |
| 2 | <tt>call(function[12:8])</tt> | the call instruction with the 5 msb of the function address |
| 3 | <tt>instruction</tt> | the instruction following the call instruction |

### <a name="dot_callc"><tt>.callc(function[,instruction])</tt></a>

- <tt>function</tt> is the name of a function

- <tt>instruction</tt> is a single-cycle instruction

  Default:  <tt>nop</tt>

This generates the following 3 instruction sequence to conditionally
[call](#callc) the specified function:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>function[7:0]</tt> | push the 8 lsb of the function address onto the data stack |
| 2 | <tt>callc(function[12:8])</tt> | the callc instruction with the 5 msb of the function address |
| 3 | <tt>instruction</tt> | the instruction following the call instruction |

### <a name="dot_fetch"><tt>.fetch(ram)</tt></a>

- <tt>ram</tt> is the memory from which values are being fetched

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[fetch](#fetch)</tt> instruction.

### <a name="dot_fetch_minus"><tt>.fetch-(ram)</tt></a>

- <tt>ram</tt> is the memory from which values are being fetched

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[fetch-](#fetch_minus)</tt> instruction.

### <a name="dot_fetch_plus"><tt>.fetch+(ram)</tt></a>

- <tt>ram</tt> is the memory from which values are being fetched

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[fetch+](#fetch_plus)</tt> instruction.

### <a name="dot_fetchindexed"><tt>.fetchindexed(variable)</tt></a>

- <tt>variable</tt> is a variable name

This macro generates the following three instruction sequence to replace the top
of the data stack with <tt>variable[T]</tt>, i.e., treat <tt>variable</tt> as a
multi-element array and perform a fetch indexed by the top of the data stack.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>variable</tt> | push the location of the variable onto the data stack |
| 2 | <tt>+</tt> | add the variable location to the index previously on the top of the data stack |
| 3 | <tt>fetch(ram)</tt> | exchange the memory location for the variable value |

Here the variable is stored in the memory <tt>ram</tt>.

### <a name="dot_fetchvalue">.fetchvalue(variable)</a>

- <tt>variable</tt> is a variable name

This macro generates the following two instruction sequence to fetch the
value for the specified variable from memory.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>variable</tt> | push the location of the variable onto the data stack |
| 2 | <tt>fetch(ram)</tt> | exchange the memory location for the variable value |

Here the variable is stored in the memory <tt>ram</tt>.

### <a name="dot_fetchvector"><tt>.fetchvector(name,length)</tt></a>

- <tt>name</tt> is a variable name

- <tt>length</tt> is the length of the vector to transfer from the data stack to the RAM

Generate the <tt>length+1</tt> instruction sequence to copy <tt>length</tt>
values from the specified multi-element variable to the data stack in
Forth-preferred order.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>${name+length-1}</tt> | push the index ${variable+length-1} to the last element of the vector onto the data stack |
| 2 .. <tt>length</tt> | <tt>.fetch-(ram)</tt> | push the last element of the vector onto the data stack under the top and decrement the memory index |
| <tt>length+1</tt> | .fetch(ram) | replace the index with the first element of the variable |

### <a name="dot_inport"><tt>.inport(I_PORT)</tt></a>

- <tt>I_PORT</tt> is the input port number

This macro generates the two instruction sequence to read from the specified
input port.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>I_PORT</tt> | push the input port index onto the data stack |
| 2 | <tt>inport</tt> | the inport instruction |

### <a name="dot_jump"><tt>.jump(target[,instruction])</tt></a>

- <tt>target</tt> is the address of the jump target

- <tt>instruction</tt> is an optional instruction to perform immedidately after
  the <tt>jump</tt> instruction

  Default:  <tt>nop</tt>

This macro generates the three instruction sequence to jump to the specified
target address as follows:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>target[7:0]</tt> | push the 8 lsb of the target address onto the data stack |
| 2 | <tt>jump(target[12:8])</tt> | the <tt>jump</tt> instruction with the 5 msb of the target address |
| 3 | <tt>instruction</tt> | the instruction following the jump instruction |

### <a name="dot_jumpc"><tt>.jumpc(target[,instruction])</tt></a>

- <tt>target</tt> is the address of the jump target

- <tt>instruction</tt> is an optional instruction to perform immedidately after
  the <tt>jumpc</tt> instruction

  Default:  <tt>nop</tt>

This macro generates the three instruction sequence to conditionally jump to
the specified target address as follows:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>target[7:0]</tt> | push the 8 lsb of the target address onto the data stack |
| 2 | <tt>jumpc(target[12:8])</tt> | the <tt>jumpc</tt> instruction with the 5 msb of the target address |
| 3 | <tt>instruction</tt> | the instruction following the jumpc instruction |

### <a name="dot_outport"><tt>.outport(O_PORT[,instruction])</tt></a>

- <tt>O_PORT</tt> is the output port number

- <tt>instruction</tt> is an optional instruction to perform immedidately after
  the <tt>output</tt> instruction

  Default:  <tt>drop</tt>

This macro generates the three instruction sequence to write the value at the
top of the data stack to the specified output port as follows.  The default
<tt>drop</tt> instruction discards the value written to the output port.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>O_PORT</tt> | push the output port index onto the data stack |
| 2 | <tt>outport</tt> | the <tt>outport</tt> instruction |
| 3 | <tt>instruction</tt> | the instruction following the outport instruction |

### <a name="dot_outstrobe"><tt>.outstrobe(O_PORT)</tt></a>

- <tt>O_PORT</tt> is the output port number

This macro generates the two instruction sequence to write the value at the
top of the data stack to the specified output port as follows.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>O_PORT</tt> | push the output port index onto the data stack |
| 2 | <tt>outport</tt> | the <tt>outport</tt> instruction |

### <a name="dot_return"><tt>.return[(instruction)]</tt></a>

- <tt>instruction</tt> is an optional instruction to perform immedidately after
  the <tt>return</tt> instruction

  Default:  <tt>nop</tt>

This macro generates the two instruction sequence to return from a function as
follows:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>return</tt> | the <tt>return</tt> instruction |
| 2 | <tt>instruction</tt> | the instruction following the return instruction |

### <a name="dot_store"><tt>.store(ram)</tt></a>

- <tt>ram</tt> is the memory to which values are being stored

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[store](#store)</tt> instruction.

### <a name="dot_store_minus"><tt>.store-(ram)</tt></a>

- <tt>ram</tt> is the memory to which values are being stored

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[store-](#store_minus)</tt> instruction.

### <a name="dot_store_plus">.store+</a>

- <tt>ram</tt> is the memory to which values are being stored

This macro is used to incorporate the memory index for <tt>ram</tt> into the
<tt>[store+](#store_plus)</tt> instruction.

### <a name="dot_storeindexed"><tt>.storeindexed(variable[,instruction])</tt></a>

- <tt>variable</tt> is a variable name

- <tt>instruction</tt> is an optional instruction to perform at the end of the
  instruction sequence

  Default:  <tt>drop</tt>

This macro treats the top of the data stack as a index into the specified
multi-element variable as part of storing the next-to-top at that location.
I.e., it generates the four instruction sequence to store
<tt>variable[T]&nbsp;&lt;=&nbsp;N</tt> as follows:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>variable</tt> | push the variable location onto the data stack |
| 2 | + | compute the memory location to which the initial value of N is to be stored |
| 3 | <tt>store(ram)</tt> | store <tt>N</tt> at <tt>ram[T+variable]</tt> |
| 4 | <tt>instruction</tt> | the instruction following the store instruction |

### <a name="dot_storevalue"><tt>.storevalue(variable[,instruction])</tt></a>

- <tt>variable</tt> is a variable name

- <tt>instruction</tt> is an optional instruction to perform at the end of the
  instruction sequence

  Default:  <tt>drop</tt>

This macro generates the three instruction sequence to store the top of the
data stack at the specified variable.

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>variable</tt> | push the variable location onto the data stack |
| 2 | store(ram) | store the initial value of the top of the data stack at the specified variable |
| 3 | <tt>instruction</tt> | the instruction following the store instruction |

### <a name="dot_storevector"><tt>.storevector(variable,length[,instruction])</tt></a>

- <tt>variable</tt> is a variable name

- <tt>length</tt> is the length of the vector to transfer from RAM to the data
  stack

  Default:  <tt>drop</tt>

This macro generates the <tt>length+2</tt> instruction sequence to store the
top <tt>length</tt> values on the data stack to the array specified by
<tt>variable</tt> as follows:

| index | instruction | description |
| ----- | ----------- | ----------- |
| 1 | <tt>variable</tt> | push the variable location onto the data stack |
| 2 .. <tt>length+1</tt> | <tt>.store+(ram)</tt> | store the next-to-top value on the data stack at the location specified by the top of the data stack |
| <tt>length+2</tt> | <tt>drop</tt> | discard the incremented address at the top of the data stack |
