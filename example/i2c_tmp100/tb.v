/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * Test bench for examples/i2c_tmp100
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

// 97 MHz clock
reg s_clk = 1'b1;
always @ (s_clk) s_clk <= #5.155 ~s_clk;

reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst <= 1'b0;
end

tri1 s_SCL;
tri1 s_SDA;
i2c_tmp100 it_inst(
  // synchronous reset and processor clock
  .i_rst        (s_rst),
  .i_clk        (s_clk),
  // I2C ports
  .io_scl       (s_SCL),
  .io_sda       (s_SDA),
  // UART_Tx ports
  .o_UART_Tx    ()
);

// run for 2+ msec
initial begin
  while ($realtime < 2.1e6) @ (posedge s_clk);
  $finish;
end

initial begin
  $dumpfile("tb.vcd");
  $dumpvars();
end

endmodule
