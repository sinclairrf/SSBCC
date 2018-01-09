; Copyright 2013, 2018, Sinclair R.F., Inc.
; Test bench for AXI4-Lite master peripheral.

.main

  ; Write 4 bytes.
  0x0F 0x01 0x02 0x03 0x04 0x00 0x00 0x00 0x00 .call(alm_write_u64,0x78)

  ; Read 8 bytes.
  .call(alm_read_u64,0x78)

  ; Write 8 bytes.
  0xFF 0x01 0x02 0x03 0x04 0x05 0x06 0x07 0x08 .call(alm_write_u64,0x60)

  ; Read 8 bytes.
  .call(alm_read_u64,0x60)

  ; Write the gray code of the address to all of memory
  0x80 :loop_write_all
    8 - >r
    0xFF r@ ${8-1} :loop_8 >r
      dup dup 0>> ^ swap 1+
    r> .jumpc(loop_8,1-) drop drop
    r@ .call(alm_write_u64)
  r> .jumpc(loop_write_all,nop) drop

  ; Issue several reads.
  0x40 :loop_read >r
    r@ .call(alm_read_u64)
    ${8-1} :loop_diag >r .outport(O_DIAG_DATA) r> .jumpc(loop_diag,1-) drop
  r> .jumpc(loop_read,0>>) drop

  ; Send termination strobe to the test bench and then wait forever.
  .outstrobe(O_DONE)
  :infinite .jump(infinite)

; Read a 32-bit value at a 32-bit aligned address.
; ( u_addr - u_LSB u u u_MSB )
.function alm_read_u64
  ; Output the 7-bit address.
  .outport(O_ALM_ADDRESS)
  ; Issue the strobe that starts the read process.
  .outstrobe(O_ALM_CMD_READ)
  ; Wait for the read process to finish.
  :wait .inport(I_ALM_BUSY) .jumpc(wait)
  ; Read the 4 bytes
  ${8-1} :loop_read .inport(I_ALM_READ_BYTE) swap .jumpc(loop_read,1-) drop
  .return

; Issue a write
; ( u_we u_LSB u u u_MSB u_addr - )
.function alm_write_u64
  ; Output the 7-bit address.
  .outport(O_ALM_ADDRESS)
  ; Output the 4 data bytes, MSB first.
  ${8-1} :loop_data swap .outport(O_ALM_DATA) .jumpc(loop_data,1-) drop
  ; Ensure all 8 bytes are written.
  .outport(O_ALM_WE)
  ; Issue the strobe that starts the write.
  .outstrobe(O_ALM_CMD_WRITE)
  ; Wait for the write process to finish.
  :wait .inport(I_ALM_BUSY) .jumpc(wait)
  .return
