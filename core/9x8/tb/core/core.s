; Copyright 2012, Sinclair R.F., Inc.
;
; Test the core instructions.

.memory RAM ram
.variable fred 3 -3
.variable joe  0*6

.main

  ; Test the left rotation instructions.
  -1 <<0 <<1 <<msb <<msb <<msb <<msb <<msb <<msb <<msb <<msb drop

  ; Test the right rotation instructions.
  -1 0>> 1>> msb>> msb>> msb>> msb>> msb>> msb>> lsb>> lsb>> drop

  ; Test the "dup" instruction.
  3 4 dup 0<> dup nip nip nip drop

  ; Test the "over" instruction.
  3 4 over 0<> nip nip drop

  ; Test the >r, r@, and r> instructions.
  3 >r -1 >r r@ r> r@ r> nip nip nip drop

  ; Test the "swap" instruction.
  3 4 swap nip drop

  ; Test the addition and subtraction instructions.
  8 5 - 7 + drop

  ; Test the comparison operations
  0  0=  drop 8  0=  drop 0xFF  0=  drop
  0  0<> drop 8  0<> drop 0xFF  0<> drop
  0 -1=  drop 8 -1=  drop 0xFF -1=  drop
  0 -1<> drop 8 -1<> drop 0xFF -1<> drop

  ; Test the bitwise logical operators
  0x11 0x12 &  drop
  0x11 0x12 or drop
  0x11 0x12 ^  drop

  ; Test the increment and decrement operators
  0xFE 1+ 1+ 1+ 1- 1- 1- drop

  ; Test the memory access operators
  .fetchvector(fred,2) drop drop
  ${size['ram']-1} :set_mem 0xFF swap .jumpc(set_mem,.store-(ram)) drop
  .fetchvector(fred,2) drop drop
  joe .fetch(ram) 1- joe .store(ram) drop .fetchvalue(joe) drop

  :infinite .jump(infinite)
