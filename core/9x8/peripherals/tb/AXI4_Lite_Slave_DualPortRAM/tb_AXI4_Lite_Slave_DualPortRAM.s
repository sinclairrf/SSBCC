; Copyright 2013, Sinclair R.F., Inc.
; Test bench for AXI4-Lite slave dual-port-ram peripheral.

.main

  ; Clear the dual-port-ram from the bottom to the top
  0 :clear O_DP_ADDRESS outport 0xAB .outport(O_DP_WRITE) 1+ dup L_DP_SIZE - .jumpc(clear) drop

;  :forever 0 :read O_DP_ADDRESS outport .inport(I_DP_READ) .outport(O_DIAG_DATA) 1+ dup L_DP_SIZE - .jumpc(read) drop .jump(forever)


  ; Wait for the AXI master to write a 4 to address 16.
  16 .outport(O_DP_ADDRESS)
  :wait_4 .inport(I_DP_READ) 4 - .jumpc(wait_4)


;  ; Clear the 32-bit word starting at address 4.
;  4 ${4-1} :clear_word >r O_DP_ADDRESS outport 0 .outport(O_DP_WRITE) 1+ r> .jumpc(clear_word,1-) drop drop

  ; Read and output the first 20 memory addresses starting with address 0.
  0 ${20-1} :read_16 >r
    O_DP_ADDRESS outport O_DIAG_ADDR outport .inport(I_DP_READ) .outport(O_DIAG_DATA)
    1+ r> .jumpc(read_16,1-) drop

  ; Terminate the program.
  O_DONE outport

  :infinite .jump(infinite)
