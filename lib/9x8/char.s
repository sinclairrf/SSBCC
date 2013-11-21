; Copyright 2013, Sinclair R.F., Inc.
;
; Character manipulation functions

.IFNDEF C__INCLUDED__CHAR_S__
.constant C__INCLUDED__CHAR_S__ 0

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Conversion to and from hex.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; Convert a byte to its 2-digit hex representation with the digit for the most
; significant nible at the top of the data stack.
; ( u - u_hex_lsn u_hex_msn )
.function char__byte_to_2hex
  ; ( u - u u_hex_low )
  dup 0x0F .call(char__nibble_to_hex,&)
  ; ( u u_hex_low - u_hex_low u_hex_high )
  swap 0>> 0>> 0>> .call(char__nibble_to_hex,0>>)
  .return

; Convert a nibble between 0x00 and 0x0F inclusive to it hex digit.
; ( u - u_hex_n )
.function char__nibble_to_hex
  0x09 over - 0x80 & 0<> ${ord('A')-ord('9')-1} & + '0' .return(+)

; Convert two hex digits to their byte value.  Return 0x00 on success and 0xFF
; on failure.
; ( u_hex_lsn u_hex_msn - u f )
.function char__2hex_to_byte
  ; convert the msn to its position and save the error indication
  ; ( u_hex_lsn u_hex_lsn - u_hex_msn u_msn ) r:( - f_msn )
  .call(char__hex_to_nibble) >r <<0 <<0 <<0 <<0
  ; ( u_hex_lsn u_msn - u ) r:( f_msn - f_lsn f_msn )
  ; convert the lsn to its position, save the error indication, and combine the two nibble conversions
  .call(char__hex_to_nibble,swap) >r or
  ; compute the return status and return
  ; ( u - u f ) r:( f_lsn f_msn - )
  r> r> .return(or)

; Convert a single hex digit to its nibble value.  Return 0x00 on success and
; 0xFF on failure.
; ( u_hex_n - u f )
.function char__hex_to_nibble
  dup        0x80 & .jumpc(error)
  dup '0'  - 0x80 & .jumpc(error)
  '9' over - 0x80 & .jumpc(not_value_0_to_9) '0' - .return(0)
  :not_value_0_to_9
  dup 'A'  - 0x80 & .jumpc(error)
  'F' over - 0x80 & .jumpc(not_value_A_to_F) ${ord('A')-10} - .return(0)
  :not_value_A_to_F
  dup 'a'  - 0x80 & .jumpc(error)
  'f' over - 0x80 & .jumpc(error) ${ord('a')-10} - .return(0)
  :error .return(0xFF)

.ENDIF ; C__INCLUDED__CHAR_S__
