\ Copyright 2012, Sinclair R.F., Inc.

\ Example LED flasher using 8-bit data

\ loop for 256*n clock cycles
:pause ( - )
  0 :l00 1 - dup 0= .returnc .jump(l00)

\ repeat "pause" 256 times
:repause
  0 :l01 .call(pause) 1 - dup 0= .returnc .jump(l01)

\ main program (as an infinite loop)
\ T is the setting for the LED
0 :l02 1 xor dup C_LED out .call(repause) .jump(l02)
