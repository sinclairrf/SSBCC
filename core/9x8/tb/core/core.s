; Copyright 2012, Sinclair R.F., Inc.
;
; Test the core instructions.

.main

  ; Test the left rotation instructions.
  -1 <<0 <<1 <<msb <<msb <<msb <<msb <<msb <<msb <<msb <<msb drop

  ; Test the right rotation instructions.
  -1 0>> 1>> msb>> msb>> msb>> msb>> msb>> msb>> lsb>> lsb>> drop

  ; Test the dup instruction
  0 1 dup 0<> dup nip nip nip drop

  :loop .jump(loop)
