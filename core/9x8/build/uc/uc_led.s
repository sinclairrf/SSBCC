; Copyright 2013, Sinclair R.F., Inc.
; Test bench for synthesis tools:  simple LED flasher

.main

  0x01 :forever O_LED outport 0xFF :outer 0xFF :inner .jumpc(inner,1-) drop .jumpc(outer) drop 0x01 ^ .jump(forever)
