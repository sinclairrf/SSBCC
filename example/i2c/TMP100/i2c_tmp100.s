; Copyright 2012, Sinclair R.F., Inc.
;
; TMP100:
;   run in 400 kHz mode

.constant C_TMP100 0x94 ; u14

.include ../lib_i2c.s

.main

  :infinite
    "\r\n\0"
    .call(get_i2c_temp) .jumpc(error)
      >r .call(byte_to_hex) r> .call(byte_to_hex)
      .jump(no_error)
    :error
      "N/A "
    :no_error
    :print_loop
      .outport(O_UART_TX)
      :print_wait .inport(I_UART_TX) .jumpc(print_wait)
      .jumpc(print_loop,nop) drop
    .call(wait_1_sec)
  .jump(infinite)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Wait one second with a 100 MHz clock.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function wait_1_sec

  ; 100 iterations
  ${100-1} :outer
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
