; Copyright 2012, Sinclair R.F., Inc.
;
; TMP100:
;   run in 3.4 MHz high speed mode

.constant C_TMP100 0x94 ; u14

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

; ( - )
.function i2c_send_start
  0 .outport(O_SDA)
  .call(i2c_quarter_cycle,1)
  .call(i2c_quarter_cycle,0)
.return

; Send the transmitted byte and indicate false if the acknowledge bit was
; received.
; ( u - f )
.function i2c_send_byte
  ; send the byte, msb first
  ; ( u - )
  ${8-1} :outer
    ; send the next bit
    swap <<msb swap
    .call(i2c_clock_cycle,over) drop
  .jumpc(outer,1-) drop drop
  ; get the acknowledge bit at the middle of the high portion of SCL
  ; ( - f )
  .call(i2c_clock_cycle,1)
.return

; read the next byte from the device
; ( - u )
.function i2c_read_byte
  0 ${8-1} :loop
    swap <<0 .call(i2c_clock_cycle,1) or swap
  .jumpc(loop,1-) drop
  ; send the acknowledgement bit
  .call(i2c_clock_cycle,0)
.return(drop)
 
; Send a stop by brining SDA high while SCL is high
; ( - )
.function i2c_send_stop
  0 .outport(O_SDA) .call(i2c_quarter_cycle,1)
  1 .outport(O_SDA) .call(i2c_quarter_cycle,1)
.return

; send the clock as a "0110" pattern and samle SDA in the  middle of the high portion
; ( u_sda_out - u_sda_in )
.function i2c_clock_cycle
  .outport(O_SDA)
  .call(i2c_quarter_cycle,0)
  .call(i2c_quarter_cycle,1)
  .inport(I_SDA)
  .call(i2c_quarter_cycle,1)
  .call(i2c_quarter_cycle,0)
.return

; 97 MHz / 400 kHz / 4 ==> 61
; subtract the 3 clock cycles to call this function and the 2 clock cycles to
;   return from it ==> consume 56 clock cycles
;   for a loop with 3 clock cycles per iteration, this is about 18 iterations
.function i2c_quarter_cycle
  .outport(O_SCL)
  ${18-1} :loop .jumpc(loop,1-)
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
