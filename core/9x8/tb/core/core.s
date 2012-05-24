; Copyright 2012, Sinclair R.F., Inc.
;
; Test the core instructions.

.main

  ; Test the rotation instructions
  -1 <<0 <<1 <<msb <<msb <<msb <<msb <<msb <<msb <<msb <<msb drop

  :loop .jump(loop)
