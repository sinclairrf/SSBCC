; Copyright 2012, Sinclair R.F., Inc.
;
; Test the memory functions for various system architectures -- no memory tests.

.main

  ; test the data stack
  1 2 3 4 drop drop drop drop

  ; test data movements onto and off of the return stack
  1 >r 2 >r 3 4 >r >r r@ drop r> drop r> r> nip drop r@ r> nip drop

  ; test function calls mixed with return stack operations
  .call(testfn,3) drop

  ; terminate the simulation
  O_DONE_STROBE outport

  :infinite .jump(infinite)

.function testfn
  >r r@ 1- .callc(testfn,nop) r>
  .return(+)
