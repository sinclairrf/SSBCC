; Copyright 2012, Sinclair R.F., Inc.
;
; TMP100:
;   run in 3.4 MHz high speed mode

.constant C_TMP100 0x94 ; u14

.main

  :infinite
    .call(get_i2c_temp)
    .call(print_2bytes)
    .call(wait_1_sec)
  .jump(infinite)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Wait one second with a 97 MHz clock.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function wait_1_sec

  ; 97 iterations
  $(97-1) :outer
    ; 1000 iterations
    $(4-1) :mid_outer
      $(250-1) :mid_inner
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

; ( - T_lsb T_msb )
.function get_i2c_temp
  .call(i2c_send_start)
  $(C_TMP100|0x01) .call(i2c_send_byte)
  .call(i2c_read_byte) >r .call(i2c_read_byte) r>
  .call(i2c_send_stop)
.return

; ( - )
.function i2c_send_start
  0 .outport(O_SDA) .call(i2c_quarter_cycle)
  0 .outport(O_SCL) .call(i2c_quarter_cycle)
.return

; Send the transmitted byte and indicate true if the acknowledge bit was
; received.
; ( u - f )
.function i2c_send_byte
  ; send the byte, msb first
  $(8-1) :outer
    ; send the next bit
    swap <<msb O_SDA outport swap
    ; send the clock as a "0110" pattern
    0x06 $(4-1) :inner
      swap O_SCL outport 0>> swap .call(i2c_quarter_cycle)
    .jumpc(inner,1-) drop drop
  .jumpc(outer,1-) drop drop
  ; get the acknowledge bit at the middle of the high portion of SCL
  1 .outport(O_SDA) .call(i2c_quarter_cycle)
  1 .outport(O_SCL) .call(i2c_quarter_cycle)
  .inport(I_SDA) 0= .call(i2c_quarter_cycle)
  0 .outport(O_SCL) .call(i2c_quarter_cycle)
.return

; read the next byte from the device
; ( - u )
.function i2c_read_byte
  ; ( - u count )
  0 $(8-1) :loop
    0 .outport(O_SCL) .call(i2c_quarter_cycle)
    1 .outport(O_SCL) .call(i2c_quarter_cycle)
    swap <<0 .inport(I_SDA) or swap .call(i2c_quarter_cycle)
    0 .outport(O_SCL) .call(i2c_quarter_cycle)
  .jumpc(loop,1-)
; ( u count - u )
.return(drop)

; ( - )
.function i2c_send_stop
  1 .outport(O_SCL) .call(i2c_quarter_cycle)
  1 .outport(O_SDA) .call(i2c_quarter_cycle)
.return

; 97 MHz / 400 kHz / 4 ==> 61
; subtract the 3 clock cycles to call this function and the 2 clock cycles to
;   return from it ==> consume 56 clock cycles
;   for a loop with 3 clock cycles per iteration, this is about 18 iterations
.function i2c_quarter_cycle
  $(18-1) :loop .jumpc(loop,1-)
.return(drop)


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
