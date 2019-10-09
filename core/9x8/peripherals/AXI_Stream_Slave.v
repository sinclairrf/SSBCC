//
// PERIPHERAL AXI_Stream_Slave:  @NAME@
// Copyright 2016, Sinclair R.F., Inc.
// Copyright 2019, Rodney Sinclair
//

initial @NAME@_tready = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    @NAME@_tready <= 1'b0;
  else if (s_outport && (s_T == @IX_LATCH@))
    @NAME@_tready <= 1'b1;
  else  if (@NAME@_tvalid && @NAME@_tready)
    @NAME@_tready <= 1'b0;
  else
    @NAME@_tready <= @NAME@_tready;

always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__@NAME@__data <= @WIDTH@'d0;
  else if (s_outport && (s_T == @IX_LATCH@))
    s__@NAME@__data <= @NAME@_tdata;
  else if (s_inport && (s_T == @IX_INDATA@))
    s__@NAME@__data <= @SHIFT_DATA@;
  else
    s__@NAME@__data <= s__@NAME@__data;
