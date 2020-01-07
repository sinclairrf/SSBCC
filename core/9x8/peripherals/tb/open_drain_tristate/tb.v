/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * Test bench for the open_drain peripheral.
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

//
// 100 MHz clock and synchronous reset.
//

reg s_clk = 1'b1;
always @ (s_clk)
  s_clk <= #5 ~s_clk;

reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst = 1'b0;
end

wire s_env;
tri1 s_od;
wire o_od_o;
wire o_od_t;
tb_open_drain_tristate uut(
  // synchronous reset and processor clock
  .i_rst        (s_rst),
  .i_clk        (s_clk),
  .o_env        (s_env),
  .i_od_i       (s_od),
  .o_od_o       (o_od_o),
  .o_od_t       (o_od_t)
);

assign s_od = (o_od_t) ? 1'bz : o_od_o;

initial begin
  repeat (60) @ (posedge s_clk);
  $finish;
end

always @ (posedge s_clk)
  $display("%12d : %b %b", $time, s_env, s_od);

//initial begin
//  $dumpfile("tb.vcd");
//  $dumpvars();
//end

endmodule
