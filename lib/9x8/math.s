; Copyright 2014, Sinclair R.F., Inc.
;
; Unsigned arithmetic operations.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Add two unsigned 8-bit values to produce an unsigned 16-bit value.
; Method:  Calculate the sum of the msb of the two raw values and the msb of the
;          sums of the 7 lsbs of the two values to get the msb of the sum and
;          the lsb of the MSB of the 16-bit sum.
; 36 instructions
;
; ( u1 u2 - (u1+u2)_LSB (u1+u2)_MSB )
.function math__add_u8_u8_u16
  ; and the two 7 lsbs and put the 7 lsb of that sum on the return stack
  over 0x7F & over 0x7F & + dup 0x7F & >r
  ; add the msb of the sum of the 7 lsbs and the two inputs
  0x80 & <<msb swap 0x80 & <<msb + swap 0x80 & <<msb +
  ; construct the MSB of the sum as bit 1 of the sums of the msbs
  dup 0>> swap
  ; set the msb of the LSB if the lsb of the sum of the msbs is non-zero
  0x01 & 0<> 0x80 & r> or
  ; swap the orders so that the MSB is on the top of the data stack
  .return(swap)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; miscellaneous unsigned addition operations

.function math__add_u16_u8_u16
  swap >r .call(math__add_u8_u8_u16) r> .return(+)

.function math__add_u16_u8_u24
  swap >r .call(math__add_u8_u8_u16) r> .call(math__add_u8_u8_u16) .return

.function math__add_u24_u8_u24
  swap >r .call(math__add_u16_u8_u24)
  r> .return(+)

.function math__add_u24_u8_u32
  swap >r .call(math__add_u16_u8_u24)
  r> .call(math__add_u8_u8_u16)
  .return

.function math__add_u32_u8_u32
  swap >r .call(math__add_u24_u8_u32)
  r> .return(+)

.function math__add_u32_u16_u32
  >r .call(math__add_u32_u8_u32)
  r> .call(math__add_u24_u8_u24)
  .return

.function math__add_u32_u24_u32
  >r .call(math__add_u32_u16_u32)
  r> .call(math__add_u16_u8_u16)
  .return

.function math__add_u32_u32_u32
  >r .call(math__add_u32_u24_u32)
  r> .return(+)
