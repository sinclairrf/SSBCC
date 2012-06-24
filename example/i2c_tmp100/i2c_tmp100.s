; Copyright 2012, Sinclair R.F., Inc.
;
; TMP100:
;   run in 400 kHz mode

.constant C_TMP100 0x94 ; u14

.include lib_i2c.s

.main

  :infinite
    .call(get_i2c_temp) .jumpc(error)
      .call(print_2bytes)
    :error
    .call(wait_1_sec)
  .jump(infinite)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Wait one second with a 97 MHz clock.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function wait_1_sec

  ; 97 iterations
  ${97-1} :outer
    ; 1000 iterations
    ${4-1} :mid_outer
      ${250-1} :mid_inner
        ; 1000 clock cycles (250 iterations of 4 clock loop)
        250 :inner 1- .jumpc(inner,nop) drop
      .jumpc(mid_inner,1-) drop
    .jumpc(mid_outer,1-) drop
  .jumpc(outer,1-) drop

.return


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Read the I2C temperature sensor
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

; ( - T_lsb T_msb 0 ) or ( - f )
.function get_i2c_temp
  .call(i2c_send_start)
  ; ( - f )
  .call(i2c_send_byte,${C_TMP100|0x01}) .jumpc(error,nop)
  ; ( 0<> - u_LSB u_MSB 0 )
  drop .call(i2c_read_byte) >r .call(i2c_read_byte) r> 0
  :error
  .call(i2c_send_stop)
.return


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Print the 2-byte temperature as a hex value.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function print_2bytes

  ; construct the message as a null-terminated string:
  ;   put the two bytes to send onto the stack (MSB first, LSB second)
  ;   end each line with a carriage-return, line-feed pair
  ;   convert the LSB from a single-byte to two hex bytes
  ;   convert the MSB from a single-byte to two hex bytes
  ;   add the length of the message
  ; ( u_LSB u_MSB - '\0' '\n' '\r' p0 p1 p2 p3 )
  >r >r
  N"\r\n"
  r> .call(byte_to_hex)
  r> .call(byte_to_hex)

  ; transmit the message
  :loop .outport(O_UART_TX)
    :wait .inport(I_UART_TX) .jumpc(wait)
  .jumpc(loop,nop) drop

.return


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Convert a byte to a two digit hex value.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.memory RAM ram
.variable nibble_to_ascii "0123456789ABCDEF"

; ( u - ascii(lower_nibble(u)) ascii(upper_nibble(u)) )
.function byte_to_hex

  dup 0x0F & .fetchindexed(nibble_to_ascii)
  swap 0xF0 & 0>> 0>> 0>> 0>> .fetchindexed(nibble_to_ascii)

.return
