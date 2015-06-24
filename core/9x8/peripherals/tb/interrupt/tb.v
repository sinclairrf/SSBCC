/*******************************************************************************
 *
 * Copyright 2015, Sinclair R.F., Inc.
 *
 * Test bench for the servo_motor peripheral.
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

// 10 MHz clock
reg s_clk = 1'b1;
always @ (s_clk)
  s_clk <= #50 ~s_clk;

reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst = 1'b0;
end

reg s_interrupt = 1'b0;
initial begin
  @ (negedge s_rst);
  repeat(`INT_DELAY) @ (posedge s_clk);
  s_interrupt = 1'b1;
  @ (posedge s_clk);
  s_interrupt = 1'b0;
end

tb_interrupt uut(
  // synchronous reset and processor clock
  .i_rst        (s_rst),
  .i_clk        (s_clk),
  // external interrupt
  .i_interrupt  (s_interrupt)
);

initial begin
//  $dumpfile("tb.vcd");
//  $dumpvars();
  repeat(50) @ (posedge s_clk);
  @ (negedge s_clk);
  $finish;
end

endmodule
