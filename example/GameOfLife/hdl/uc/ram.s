; ram.s
; Copyright 2012, Sinclair R.F., Inc.
;
; RAM definition for Conway's Game of Life, SSBCC.9x8 implementation

.memory RAM ram
; these bit counts must be the first 8 entries in the ram
.variable       bit_counts              0 1 1 2 1 2 2 3
; commanded mode
.variable       cmd_frame_waits         0       ; number of frames between updates
.variable       cmd_stop                0       ; don't propagate the state
.variable       cmd_wrap                0       ; wrap at the top/bottom and left/right boundaries
; internal status
.variable       cnt_frame_waits         0       ; current count against cmd_frame_waits
.variable       sel_rd                  0       ; index for ping pong buffer being displayed
; buffered game state for computing each line of output
.variable       line_prev               0*34    ; values from previous line
.variable       line_curr               0*34    ; values from current line
.variable       line_next               0*34    ; values from next line

