/*******************************************************************************
 *
 * Copyright 2015, Sinclair R.F., Inc.
 *
 * Test bench for two-interrupt peripheral.
 *
 ******************************************************************************/

`timescale 1ns/1ps

module tb;

// 10 MHz clock
reg s_clk = 1'b1;
always @ (s_clk) s_clk <= #50 ~s_clk;

reg s_rst = 1'b1;
initial begin
  repeat (5) @ (posedge s_clk);
  s_rst <= 1'b0;
end

reg s_interrupt = 1'b0;
initial begin
  repeat (50) @ (posedge s_clk);
  s_interrupt = 1'b1;
  @ (posedge s_clk)
  s_interrupt = 1'b0;
end

wire s_UART_Tx;
dual_interrupt uut(
  // synchronous reset and processor clock
  .i_rst        (s_rst),
  .i_clk        (s_clk),
  // transmit-only UART
  .o_uart_tx    (s_UART_Tx),
  // interrupts
  .i_interrupt  (s_interrupt)
);

localparam baud = 115200;
localparam dt_baud = 1.0e9/baud;
reg [8:0] deser = 9'h1FF;
initial forever begin
  @ (negedge s_UART_Tx);
  #(dt_baud/2.0);
  repeat (9) begin
    #dt_baud;
    deser = { s_UART_Tx, deser[1+:8] };
  end
  if (deser[8] != 1'b1)
    $display("%13d : Malformed UART transmition", $time);
  else if ((8'h20 <= deser[0+:8]) && (deser[0+:8]<=8'h80))
    $display("%13d : Sent 0x%02H : %c", $time, deser[0+:8], deser[0+:8]);
  else
    $display("%13d : Sent 0x%02H", $time, deser[0+:8]);
  if (deser[0+:8] == 8'h0A) begin
    @ (negedge s_clk)
    $finish;
  end
end

initial begin
  $dumpfile("tb.vcd");
  $dumpvars();
end

endmodule
