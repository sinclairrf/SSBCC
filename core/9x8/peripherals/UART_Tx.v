//
// PERIPHERAL UART_Tx:  @NAME@
//
generate
reg  [7:0] s__Tx_data;
reg        s__go;
reg        s__uart_busy;
if (@FIFO@ == 0) begin : gen_@NAME@_nofifo
  always @ (s__uart_busy)
    s__busy = s__uart_busy;
  always @ (s__Tx)
    s__Tx_data = s__Tx;
  always @ (s__wr)
    s__go = s__wr;
end else begin : gen_@NAME@_fifo
  localparam L__FIFO_NBITS = $clog2(@FIFO@);
  reg [7:0] s__fifo_mem[@FIFO@-1:0];
  reg [L__FIFO_NBITS:0] s__fifo_addr_in = {(L__FIFO_NBITS+1){1'b0}};
  always @ (posedge i_clk)
    if (i_rst)
      s__fifo_addr_in <= {(L__FIFO_NBITS+1){1'b0}};
    else if (s__wr) begin
      s__fifo_addr_in <= s__fifo_addr_in + { {(L__FIFO_NBITS){1'b0}}, 1'b1 };
      s__fifo_mem[s__fifo_addr_in[0+:L__FIFO_NBITS]] <= s__Tx;
    end
  reg [L__FIFO_NBITS:0] s__fifo_addr_out;
  reg s__fifo_has_data = 1'b0;
  reg s__fifo_full = 1'b0;
  always @ (posedge i_clk)
    if (i_rst) begin
      s__fifo_has_data <= 1'b0;
      s__fifo_full <= 1'b0;
    end else begin
      s__fifo_has_data <= (s__fifo_addr_out != s__fifo_addr_in);
      s__fifo_full <= (s__fifo_addr_out == (s__fifo_addr_in ^ { 1'b1, {(L__FIFO_NBITS){1'b0}} }));
    end
  initial s__fifo_addr_out = {(L__FIFO_NBITS+1){1'b0}};
  always @ (posedge i_clk)
    if (i_rst)
      s__fifo_addr_out <= {(L__FIFO_NBITS+1){1'b0}};
    else if (s__go)
      s__fifo_addr_out <= s__fifo_addr_out + { {(L__FIFO_NBITS){1'b0}}, 1'b1 };
  initial s__go = 1'b0;
  always @ (posedge i_clk)
    if (i_rst)
      s__go <= 1'b0;
    else if (s__fifo_has_data && !s__uart_busy && !s__go)
      s__go <= 1'b1;
    else
      s__go <= 1'b0;
  initial s__Tx_data = 8'd0;
  always @ (posedge i_clk)
    if (i_rst)
      s__Tx_data <= 8'd0;
    else
      s__Tx_data <= s__fifo_mem[s__fifo_addr_out[0+:L__FIFO_NBITS]];
  always @ (s__fifo_full)
    s__busy = s__fifo_full;
end
// Count the clock cycles to decimate to the desired baud rate.
localparam L__COUNT       = @BAUDMETHOD@-1;
localparam L__COUNT_NBITS = $clog2(L__COUNT+1);
reg [L__COUNT_NBITS-1:0] s__count = {(L__COUNT_NBITS){1'b0}};
reg s__count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__count <= {(L__COUNT_NBITS){1'b0}};
    s__count_is_zero <= 1'b0;
  end else if (s__go || s__count_is_zero) begin
    s__count <= L__COUNT[0+:L__COUNT_NBITS];
    s__count_is_zero <= 1'b0;
  end else begin
    s__count <= s__count - { {(L__COUNT_NBITS-1){1'b0}}, 1'b1 };
    s__count_is_zero <= (s__count == { {(L__COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s__out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s__out_stream <= 8'hFF;
  else if (s__go)
    s__out_stream <= s__Tx_data;
  else if (s__count_is_zero)
    s__out_stream <= { 1'b1, s__out_stream[1+:7] };
  else
    s__out_stream <= s__out_stream;
// Generate the output bit stream.
initial @NAME@ = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    @NAME@ <= 1'b1;
  else if (s__go)
    @NAME@ <= 1'b0;
  else if (s__count_is_zero)
    @NAME@ <= s__out_stream[0];
  else
    @NAME@ <= @NAME@;
// Count down the number of bits.
localparam L__NTX       = 1+8+@NSTOP@-1;
localparam L__NTX_NBITS = $clog2(L__NTX);
reg [L__NTX_NBITS-1:0] s__ntx = {(L__NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__ntx <= {(L__NTX_NBITS){1'b0}};
  else if (s__go)
    s__ntx <= L__NTX[0+:L__NTX_NBITS];
  else if (s__count_is_zero)
    s__ntx <= s__ntx - { {(L__NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s__ntx <= s__ntx;
// The status bit is 1 if the core is busy and 0 otherwise.
initial s__uart_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__uart_busy <= 1'b0;
  else if (s__go)
    s__uart_busy <= 1'b1;
  else if (s__count_is_zero && (s__ntx == {(L__NTX_NBITS){1'b0}}))
    s__uart_busy <= 1'b0;
  else
    s__uart_busy <= s__uart_busy;
endgenerate
