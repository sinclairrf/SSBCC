; propagate.s
; Copyright 2012-2013, Sinclair R.F., Inc.
;
; Propagate state for Conway's Game of Life, SSBCC.9x8 implementation

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Propagate the state.
; ( - )
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate

  ; Fill the middle line buffer with zeros or the last line of the image (if in
  ; wrap mode).
  .fetch(cmd_wrap)
    .callc(propagate__read_line,line_curr)
    0= .callc(propagate__zero_buffer,line_curr)
    drop

  ; Fill the last line buffer with the first line of the image
  0x00 .outport(O_ADDR_HIGH)
  .call(propagate__read_line,line_next)

  ;
  ; Compute the new image.
  ;

  0x00 :loop_outer

    ; Copy the middle and last line buffers to the first and middle line
    ; buffers respectively.
    line_prev .call(propagate__copy_line,line_curr)
    line_curr .call(propagate__copy_line,line_next)

    ; If this is is not the last line (incremented value is zero) or if
    ; wrapping is commanded, then read the next line, otherwise fill the buffer
    ; with zeros.
    dup 1+ O_ADDR_HIGH .outport .fetchvalue(cmd_wrap) or
      .callc(propagate__read_line,line_next)
      0= .callc(propagate__zero_buffer,line_next)
      drop

    ; write the line number as the upper portion of the write address
    O_ADDR_HIGH .outport

    ; Compute and store the new state of the current line.
    .call(propagate__line)

    1+ .jumpc(loop_outer,nop) drop

  .return

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Copy the current line buffer to the previous line buffer.
; ( u_prev u_curr - )
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate__copy_line
  ${34-1} :loop_copy
    >r
    .fetch+(ram) >r swap .store+(ram) r>
    r> .jumpc(loop_copy,1-) drop
  drop .return(drop)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Compute and store the new state of the current line.
; ( - )
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate__line

  ; Initialize the processing state.
  ; ( - 0 u_left u_here ) r: ( - u_index u_mask )
  0 >r
  0x80 >r
  0
  .call(propagate__fetch_triple)
  .call(propagate__fetch_triple)
  r> drop r>

  :loop_outer >r
    r@ 1- .outport(O_ADDR_LOW)
    ; Push the next 8-bit candidate value onto the return stack.
    ; r: ( - u_8bit )
    0 >r
    0x01 :loop_inner
      ; Drop the oldest triple and bring in the triple from the right.
      ; ( u_left_old u_curr_old u_next_old - u_left_new=u_curr_old u_curr_new=u_next_old u_next_new )
      >r swap drop r> .call(propagate__fetch_triple)
      ; Compute the new bit based on these surrounding bits
      ; ( u_left u_curr u_next - u_left u_curr u_next u_new_bit )
      .call(propagate__new_bit)
      ; Shift the bitmask left 1 bit and finish the loop if the ones bit has rolled off the left.
      r> <<0 .jumpc(loop_inner,nop) drop
      r> .outport(O_BUFFER)
    r> 1+ dup ${34-1} - 0<> .jumpc(loop_outer) drop

  .return

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Compute the new state of a pixel based on the 3x3 grid of pixels centered at
; the candidate pixel.
; ( u_prev u_curr u_next - u_prev u_curr u_next u_new )
;
; Rules:
;   1.  Live pixels with fewer than 2 live neighbors die.
;   2.  Live pixels with 2 or 3 live neighbors stay alive.
;   3.  Live pixels with more than 3 live neighbors die.
;   4.  Dead pixels with exactly 3 live neighbors come to life.
;
; Method used here:
;   1.  Count all live pixels in the 3x3 grid, including the candidate pixel.
;   2.  Get the alive/dead status of the candidate pixel.
;   3.  If 3 pixels are alive or if 4 pixels are alive and the candidate pixel
;       is alive, then propagate a live pixel.
;
; Note:
;   1.  If exactly 3 pixels are alive, then either (1) the cell is alive and
;       exactly two neighbors are alive or (2) the cell is dead and exactly 3
;       neighbors are alive.  In either case, the cell will either stay alive
;       or become alive.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate__new_bit

  ; Put the candidate pixels status on the return stack
  over 0x02 & 0<> >r

  ; ( u_next - ) r: ( - u_next )
  >r

  ; ( u_prev u_curr - u_prev u_curr n_prev )
  over .fetch(nBitsSet)

  ; ( u_curr n_prev - u_curr n_prev+n_curr )
  over .fetch(nBitsSet) +

  ; ( n_prev+n_curr - u_next n_total=n_prev+n_curr+n_next ) r: ( u_next - )
  r> swap over .fetch(nBitsSet) +

  ; ( n_total - u_bit ) r: ( u_new - )
  dup 3 - 0= swap 4 - 0= r> & or 0x01

  .return(&)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Read a line into the specified buffer.
; ( u_line_buffer - )
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate__read_line

  ; ( u_line_buffer - u_line_buffer u_addr_low ) r: ( - u_line )
  0x1E ${34-1} :loop >r

    ; ( u_addr_low - u_addr_low+1 )
    1+ O_ADDR_LOW .outport

    ; ( u_line u_addr_low - u_addr_low u_line )
    swap

    ; ( - u_from_memory )
    .inport(I_BUFFER)

    ; If this is not the first or last iteration or if wrapping is commanded,
    ; then use the value read from memory.  Otherwise replace it with zero
    ; ( u_from_memory - u_use )
    r@ ${34-1} - 0<> r@ 0<> and .fetchvalue(cmd_wrap) 0<> or &

    ; ( u_addr_low u_line u_use - u_line+1 u_addr_low )
    swap .store+(ram) swap

    r> .jumpc(loop,1-) drop

  ; ( u_line u_addr_low - )
  drop .return(drop)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Fill the specified line buffer with all zeros.
; ( u_line - )
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function propagate__zero_buffer
  ${34-1} :loop_curr_fill_zero >r 0 swap .store+(ram) r> .jumpc(loop_curr_fill_zero,1-) drop
  .return(drop)
