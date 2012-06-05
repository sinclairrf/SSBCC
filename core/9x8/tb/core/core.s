; Copyright 2012, Sinclair R.F., Inc.
;
; Test the core instructions.

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

  :loop .jump(loop)
