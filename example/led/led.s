; Copyright 2012, Sinclair R.F., Inc.

; Example LED flasher using 8-bit data

; consume for 256*6+3 clock cycles
.function pause ; ( - )
  0 :inner 1 - dup .jumpc(inner) drop
  .return

; repeat "pause" 256 times
.function repeat ; ( - )
  0 :inner .call(pause) 1 - dup .jumpc(inner) drop
  .return

; main program (as an infinite loop)
; T is the setting for the LED
.main
0 :inner 1 ^ dup .outport(C_LED) .call(repause) .jump(inner)
