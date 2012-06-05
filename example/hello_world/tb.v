/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * Test bench for hello_world.v.
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

// 100 MHz clock (as per hello_world.9x8/baudmethod)
reg s_clk = 1'b1;
always @ (s_clk) s_clk <= #5 ~s_clk;

reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst <= 1'b0;
  repeat((13*10+3)*((100_000_000+115200/2)/115200)) @ (posedge s_clk);
  $finish;
end

hello_world uut(
  // synchronous reset and processor clock
  .i_rst        (s_rst),
  .i_clk        (s_clk),
  // outport ports
  .o_UART_Tx    ()
);

initial begin
  $dumpfile("tb.vcd");
  $dumpvars();
end

endmodule
