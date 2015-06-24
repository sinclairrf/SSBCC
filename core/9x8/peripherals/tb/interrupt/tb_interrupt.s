; Copyright 2015, Sinclair R.F., Inc.
; Test bench for interrupt peripheral.

.main

  ; Enable the interrupts.
  .ena

  ; Test conditional calls and jumps.
  ${2-1} :loop_test
    .callc(test_call,nop)
  .jumpc(loop_test,1-) drop

  ; Test against interrupt disable instruction.
  .dis

  ; Wait forever.
  :infinite .jump(infinite)

.interrupt
  ; Return from the interrupt handler.
  .returni

.function test_call
  .return
