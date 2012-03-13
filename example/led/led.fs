\ Copyright 2012, Sinclair R.F., Inc.

\ Example LED flasher using 8-bit data

\ loop for 255*n clock cycles
: pause ( - )
  255
  begin dup while
    1-
  repeat
  drop
  ;

\ repeat "pause" 255 times
: repause ( - )
  255
  begin dup while
    pause
    1-
  repeat
  drop
  ;

\ main program (as an infinite loop)
: main ( -- )
  \ initialize the setting for the LED
  0
  begin
    \ change the on/off value of the LED
    1 xor
    \ output the new value to the LED port
    dup C_LED out
    \ wait a while
    repause
  again
  ;
main
