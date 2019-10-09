/*******************************************************************************
 *
 * Copyright 2016, Sinclair R.F., Inc.
 *
 * Test bench for AXI_Stream_Slave peripheral.
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

// 100 MHz clock
reg s_clk = 1'b1;
always @ (s_clk)
  s_clk <= #5 ~s_clk;

// synchronous reset signal
reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst = 1'b0;
end

reg             s_axis_tvalid = 1'b0;
wire            s_axis_tready;
reg             s_axis_tlast = 1'b0;
reg      [15:0] s_axis_tdata = 16'd0;
integer         ix = 10;
integer         ix2;
initial begin
  while (s_rst)
    @ (posedge s_clk);
  repeat (5)
    @ (posedge s_clk);
  while (ix > 0) begin
    ix = ix - 1;
    s_axis_tvalid <= 1'b1;
    s_axis_tlast <= (ix == 0) ? 1'b1 : 1'b0;
    ix2 = ix*ix;
    s_axis_tdata <= ix2[0+:16];
    @ (posedge s_clk)
    while (~s_axis_tready)
      @ (posedge s_clk);
    s_axis_tvalid <= 1'b0;
    repeat (ix+1)
      @ (posedge s_clk);
  end
end

wire      [7:0] s_diag;
wire            s_diag_wr;
wire            s_done;
tb_AXI_Stream_Slave uut(
  // synchronous reset and processor clock
  .i_rst                (s_rst),
  .i_clk                (s_clk),
  // Incoming AXI Stream
  .s_axis_tvalid        (s_axis_tvalid),
  .s_axis_tready        (s_axis_tready),
  .s_axis_tlast         (s_axis_tlast),
  .s_axis_tdata         (s_axis_tdata),
  // diagnostic output
  .o_diag               (s_diag),
  .o_diag_wr            (s_diag_wr),
  // termination signal
  .o_done               (s_done)
);

always @ (posedge s_clk)
  if (s_diag_wr)
    $display("%12d : %h", $time, s_diag);

always @ (posedge s_clk)
  if (s_done)
    $finish;

endmodule
