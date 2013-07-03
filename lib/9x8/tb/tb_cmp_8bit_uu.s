; Copyright 2013, Sinclair R.F., Inc.
; Test bench for ../cmp_8bit_uu.s

.include cmp_8bit_uu.s

.constant C_LARGER 8
.constant C_SMALLR 4

.main

  C_LARGER C_SMALLR .call(cmp_8bit_uu_eq) .outport(O_VALUE) ;  0
  C_SMALLR C_LARGER .call(cmp_8bit_uu_eq) .outport(O_VALUE) ;  0
  C_LARGER C_LARGER .call(cmp_8bit_uu_eq) .outport(O_VALUE) ; -1

  C_LARGER C_SMALLR .call(cmp_8bit_uu_ne) .outport(O_VALUE) ; -1
  C_SMALLR C_LARGER .call(cmp_8bit_uu_ne) .outport(O_VALUE) ; -1
  C_LARGER C_LARGER .call(cmp_8bit_uu_ne) .outport(O_VALUE) ;  0

  C_LARGER C_SMALLR .call(cmp_8bit_uu_lt) .outport(O_VALUE) ;  0
  C_SMALLR C_LARGER .call(cmp_8bit_uu_lt) .outport(O_VALUE) ; -1
  C_LARGER C_LARGER .call(cmp_8bit_uu_lt) .outport(O_VALUE) ;  0

  C_LARGER C_SMALLR .call(cmp_8bit_uu_ge) .outport(O_VALUE) ; -1
  C_SMALLR C_LARGER .call(cmp_8bit_uu_ge) .outport(O_VALUE) ;  0
  C_LARGER C_LARGER .call(cmp_8bit_uu_ge) .outport(O_VALUE) ; -1

  C_LARGER C_SMALLR .call(cmp_8bit_uu_le) .outport(O_VALUE) ;  0
  C_SMALLR C_LARGER .call(cmp_8bit_uu_le) .outport(O_VALUE) ; -1
  C_LARGER C_LARGER .call(cmp_8bit_uu_le) .outport(O_VALUE) ; -1

  C_LARGER C_SMALLR .call(cmp_8bit_uu_gt) .outport(O_VALUE) ; -1
  C_SMALLR C_LARGER .call(cmp_8bit_uu_gt) .outport(O_VALUE) ;  0
  C_LARGER C_LARGER .call(cmp_8bit_uu_gt) .outport(O_VALUE) ;  0

  ; signal termination of the test
  O_TERMINATE outport

  ; wait forever
  :infinite .jump(infinite)
