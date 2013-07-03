; Copyright 2013, Sinclair R.F., Inc.
;
; 8-bit unsigned vs. unsigned comparison operators

; Compare two unsigned 8-bit values for equality.
; ( u1 u2 - f"u1 = u2" )
.function cmp_8bit_uu_eq
  - .return(0=)

; Compare two unsigned 8-bit values for inequality.
; ( u1 u2 - f"u1 != u2" )
.function cmp_8bit_uu_ne
  - .return(0<>)

; Return true if the unsigned value u1 is less than the unsigned value u2.
; ( u1 u2 - f"u1 < u2" )
.function cmp_8bit_uu_lt
  - 0x80 & .return(0<>)

; Return true if the unsigned value u1 is greater than or equal to the unsigned
; value u2.
; ( u1 u2 - f"u1 >= u2" )
.function cmp_8bit_uu_ge
  - 0x80 & .return(0=)

; Return true if the unsigned value u1 is less than or equal to the unsigned
; value u2.
; Note:  Calling this function is equivalent to .call(cmp_8bit_uu_ge,swap)
; ( u1 u2 - f"u1 <= u2" )
.function cmp_8bit_uu_le
  swap - 0x80 & .return(0=)

; Return true if the unsigned value u1 is greater than the unsigned value u2.
; Note:  Calling this function is equivalent to .call(cmp_8bit_uu_lt,swap)
; ( u1 u2 - f"u1 > u2" )
.function cmp_8bit_uu_gt
  swap - 0x80 & .return(0<>)
