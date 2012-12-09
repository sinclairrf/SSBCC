; Conway's Game of Life, SSBCC.9x8 implementation
; Copyright 2012, Sinclair R.F., Inc.

.include ram.s
.include propagate.s

.main

  ; On initial program start-up or on a reset, do the following:
  .call(clear_ping_pong_buffers)

  ; Run the program.
  :infinite

    .call(process_user_commands)

    ; Don't propagate the state if the the machine is stopped.
    .fetch(cmd_stop) .jumpc(infinite)

    ; See if enough frames have elapsed to start updating the next frame.
    .fetch(cnt_frame_waits) .jumpc(wait,1-)

      ; Restart the count for the number of frames between updates.
      .fetch(cmd_frame_waits) .store(cnt_frame_waits)

      ; Compute the new machine state
      .call(propagate)

      ; Swap the read and write ping pong buffer selection.
      .fetch(sel_rd) O_PING_PONG_SEL_WR .outport 1 ^ O_PING_PONG_SEL_RD .outport .store(sel_rd)

      .jump(no_wait)

    ; Otherwise, store the decremented wait count.
    :wait

      .store(cnt_frame_waits)

    :no_wait

    ; Wait until the current video frame ends.
    :wait_until_frame_ended .inport(I_FRAME_ENDED) 0= .jumpc(wait_until_frame_ended)

  .jump(infinite)

; Clear the two ping pong buffers.
.function clear_ping_pong_buffers
  1 :loop_sel
    O_PING_PONG_SEL_WR .outport
    0xFF :loop_high
      O_ADDR_HIGH .outport
      0x1F :loop_low
        O_ADDR_LOW .outport
        0 .outport(O_BUFFER)
        .jumpc(loop_low,1-) drop
      .jumpc(loop_high,1-) drop
    .jumpc(loop_sel,1-)
  .return(drop)
