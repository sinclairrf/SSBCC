; Copyright 2016, Sinclair R.F., Inc.
;
; Test bench for AXI_Stream_Slave peripheral.

.macro push16

.main

  ; Initialize the 16-bit sum to 0
  ; ( - u_LSB u_MSB)
  .push16(0)

  ; Read 16-bit values from the AXI-Stream until the TLast signal is received.
  :loop
    .inport(I_axis_status) 0= .jumpc(loop)

    ; Preserve the value of the TLast status
    ; ( u_LSB u_MSB - u_LSB u_MSB ) r:( - f_~tlast )
    .inport(I_axis_status) 0x02 & 0= >r

    ; Latch and advance the AXI-Stream and accumulate the sum.
    ; ( u_LSB u_MSB - u_LSB' u_MSB' ) r:( f_~tlast - f_~tlast )
    .outstrobe(O_axis_latch)
    >r .inport(I_axis_data) +c >r + .inport(I_axis_data) r> + r> +

    ; Continue looping if this wasn't the last sample.
    ; ( u_LSB u_MSB - u_LSB u_MSB ) r:( f_~tlast - )
    r> .jumpc(loop)

  ; Output the 2 bytes in the sum.
  .outport(O_DIAG)
  .outport(O_DIAG)

  ; Wait a few clock cycles.
  ${3-1} :wait .jumpc(wait,1-) drop

  ; Send the termination signal and then enter an infinite loop.
  1 .outport(O_DONE)
  :infinite .jump(infinite)
