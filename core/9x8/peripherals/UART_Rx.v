//
// PERIPHERAL UART_Rx:  @NAME@
//
// Technique:
// - optionally synchronize the incoming signal
// - optionally deglitch the incoming signal
// - identify edges, align with value before the edge
// - generate missing edges, error if non-aligned edges, align values
// - assemble received bit sequence
// - run state machine counting number of received bits and waiting for delayed start bits
// - validate bit sequence and output bit sequence at end of last stop bit
// - optional FIFO
//
localparam L__BAUDMETHOD = @BAUDMETHOD@;
localparam L__BAUDMETHOD_NBITS = $clog2(L__BAUDMETHOD);
// Either copy the input, register it, or put it through a synchronizer.
localparam L__SYNC_LENGTH = @SYNC@;
localparam L__DEGLITCH_LENGTH = @DEGLITCH@;
localparam L__IDLE_LENGTH = (1+8+@NSTOP@)*L__BAUDMETHOD-1;
localparam L__IDLE_LENGTH_NBITS = $clog2(L__IDLE_LENGTH+1);
localparam L__EDGE_TOL          = @EDGETOL@;
localparam L__EDGE_TIMER_SIZE   = ((1000+9*25)*L__BAUDMETHOD+500)/1000-1;
localparam L__EDGE_TIMER_NBITS  = $clog2(L__EDGE_TIMER_SIZE+1);
localparam L__EDGE_TIMER_START  = ((1000+L__EDGE_TOL)*L__BAUDMETHOD+500)/1000-1;
localparam L__EDGE_TIMER_TOL    = (2*L__EDGE_TOL*L__BAUDMETHOD+500)/1000;
localparam L__NRX = 1+8+@NSTOP@;
localparam L__INFIFO = @INFIFO@;
localparam L__INFIFO_NBITS = $clog2((L__INFIFO==0)?1:L__INFIFO);
generate
wire s__Rx_sync;
if (L__SYNC_LENGTH == 0) begin : gen__no_sync
  assign s__Rx_sync = @INPORT@;
end else if (L__SYNC_LENGTH == 1) begin : gen__short_sync
  reg s__Rx_inport_s = 1'b1;
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_inport_s <= 1'b1;
    else
      s__Rx_inport_s <= @INPORT@;
  assign s__Rx_sync = s__Rx_inport_s;
end else begin : gen__long_sync
  reg [L__SYNC_LENGTH-1:0] s__Rx_inport_s = {(L__SYNC_LENGTH){1'b1}};
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_inport_s <= {(L__SYNC_LENGTH){1'b1}};
    else
      s__Rx_inport_s <= { s__Rx_inport_s[0+:L__SYNC_LENGTH-1], @INPORT@ };
  assign s__Rx_sync = s__Rx_inport_s[L__SYNC_LENGTH-1];
end
// Either pass the received signal with no deglitching or apply deglitch
// hysteresis that consists of not changing the reported state unless all of
// the queued bits have changed state.
reg s__Rx_deglitched;
if (L__DEGLITCH_LENGTH == 0) begin : gen__nodeglitch
  always @ (*)
    s__Rx_deglitched <= s__Rx_sync;
end else begin : gen__deglitch
  initial s__Rx_deglitched = 1'b1;
  reg [L__DEGLITCH_LENGTH-1:0] s__Rx_deglitch = {(L__DEGLITCH_LENGTH){1'b1}};
  always @ (posedge i_clk) begin
    s__Rx_deglitched <= (&(s__Rx_deglitch != {(L__DEGLITCH_LENGTH){s__Rx_deglitched}})) ? ~s__Rx_deglitched : s__Rx_deglitched;
    s__Rx_deglitch <= { s__Rx_deglitch[0+:L__DEGLITCH_LENGTH-1], @INPORT@ };
  end
end
// Identify idle state for error recovery.  This consists of 1+8+nStop bits of
// all ones.
reg [L__IDLE_LENGTH_NBITS-1:0] s__Rx_input_idle_count = L__IDLE_LENGTH[L__IDLE_LENGTH_NBITS-1:0];
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_input_idle_count <= L__IDLE_LENGTH[L__IDLE_LENGTH_NBITS-1:0];
  else if (s__Rx_deglitched == 1'b0)
    s__Rx_input_idle_count <= L__IDLE_LENGTH[L__IDLE_LENGTH_NBITS-1:0];
  else
    s__Rx_input_idle_count <= s__Rx_input_idle_count - { {(L__IDLE_LENGTH_NBITS-1){1'b0}}, 1'b1 };
reg s__Rx_input_idle = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_input_idle <= 1'b1;
  else if (s__Rx_deglitched == 1'b0)
    s__Rx_input_idle <= 1'b0;
  else if (s__Rx_input_idle_count == {(L__IDLE_LENGTH_NBITS){1'b0}})
    s__Rx_input_idle <= 1'b1;
  else
    s__Rx_input_idle <= s__Rx_input_idle;
// Identify edges
reg s__Rx_last = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_last <= 1'b1;
  else
    s__Rx_last <= s__Rx_deglitched;
reg s__Rx_edge = 1'b0;
reg s__Rx_edge_value = 1'b1;
always @ (posedge i_clk)
  if (i_rst) begin
    s__Rx_edge <= 1'b0;
    s__Rx_edge_value <= 1'b1;
  end else begin
    s__Rx_edge <= (s__Rx_deglitched != s__Rx_last);
    s__Rx_edge_value <= s__Rx_last;
  end
// State machine signal -- waiting for first edge of start bit.
reg s__Rx_waiting;
// Run a timer to (1) capture values at the center of bits and (2) ensure edges
// are consistently timed to a +/-2.5% tolerance.
reg [L__EDGE_TIMER_NBITS-1:0] s__Rx_edge_timer = {(L__EDGE_TIMER_NBITS){1'b0}};
reg [L__EDGE_TIMER_NBITS-1:0] s__Rx_edge_cumtol = L__EDGE_TIMER_TOL[0+:L__EDGE_TIMER_NBITS];
reg s__Rx_edge_timer_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__Rx_edge_timer <= {(L__EDGE_TIMER_NBITS){1'b0}};
    s__Rx_edge_cumtol <= L__EDGE_TIMER_TOL[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_timer_zero <= 1'b0;
  end else if (s__Rx_input_idle || (s__Rx_waiting && !s__Rx_edge)) begin
    s__Rx_edge_timer <= {(L__EDGE_TIMER_NBITS){1'b0}};
    s__Rx_edge_cumtol <= L__EDGE_TIMER_TOL[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_timer_zero <= 1'b0;
  end else if (s__Rx_edge) begin
    s__Rx_edge_timer <= L__EDGE_TIMER_START[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_cumtol <= L__EDGE_TIMER_TOL[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_timer_zero <= 1'b0;
  end else if (s__Rx_edge_timer_zero) begin
    s__Rx_edge_timer <= L__EDGE_TIMER_START[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_cumtol <= s__Rx_edge_cumtol + L__EDGE_TIMER_TOL[0+:L__EDGE_TIMER_NBITS];
    s__Rx_edge_timer_zero <= 1'b0;
  end else begin
    s__Rx_edge_timer <= s__Rx_edge_timer - { {(L__EDGE_TIMER_NBITS-1){1'b0}}, 1'b1 };
    s__Rx_edge_cumtol <= s__Rx_edge_cumtol;
    s__Rx_edge_timer_zero <= (s__Rx_edge_timer == { {(L__EDGE_TIMER_NBITS-1){1'b0}}, 1'b1 });
  end
reg s__Rx_edge_error = 1'b0;
// Edge detector is a composite of incoming edges and fabricated edges.
assign s__Rx_edge_out = s__Rx_edge || s__Rx_edge_timer_zero;
// Detect poorly timed edges.  Clear the detection when the input has been idle
// long enough for there to have been no transmitted data.
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_edge_error <= 1'b0;
  else if (s__Rx_input_idle)
    s__Rx_edge_error <= 1'b0;
  else if (s__Rx_edge && (s__Rx_edge_timer > s__Rx_edge_cumtol))
    s__Rx_edge_error <= 1'b1;
  else
    s__Rx_edge_error <= s__Rx_edge_error;
// Record the received bit stream after edges occur.
// Note:  L__NRX is always 4 bits long since NSTOP is either 1 or 2.
reg [L__NRX-1:0] s__Rx_s = {(L__NRX){1'b1}};
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_s <= {(L__NRX){1'b1}};
  else if (s__Rx_edge_out)
    s__Rx_s <= { s__Rx_edge_value, s__Rx_s[1+:L__NRX-1] };
// State machine:  s__Rx_count == 0 (s__Rx_waiting == 1) means no edges have
// been encountered.  Otherwise s__Rx_count is the number of edges encountered
// (at the leading edges of the bits being recorded).  Wait until the first
// real or fake edge following the last stop bit to record the data (to ensure
// it isn't glitched in the middle).
reg s__Rx_error_p;
initial s__Rx_waiting = 1'b1;
reg [3:0] s__Rx_count = 4'd0;
reg s__Rx_wr = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__Rx_waiting <= 1'b1;
    s__Rx_count <= 4'd0;
    s__Rx_wr <= 1'b0;
  end else begin
    s__Rx_waiting <= s__Rx_waiting;
    s__Rx_wr <= 1'b0;
    if (s__Rx_edge_out)
      if (s__Rx_count < L__NRX[0+:4]) begin
        s__Rx_waiting <= 1'b0;
        s__Rx_count <= s__Rx_count + 4'd1;
      end else begin
        if (s__Rx_deglitched == 1'b0) // immediate start bit
          s__Rx_count <= 4'd1;
        else begin
          s__Rx_waiting <= 1'b1;
          s__Rx_count <= 4'd0;
        end
        s__Rx_wr <= !s__Rx_error_p && !s__Rx_error;
      end
    else
      s__Rx_count <= s__Rx_count;
  end
// Check for bad bit sequence.
initial s__Rx_error_p = 1'b0;
wire [L__NRX-1:0] s__Rx_p = { s__Rx_edge_value, s__Rx_s[1+:L__NRX-1] };
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_error_p <= 1'b0;
  else if (s__Rx_input_idle)
    s__Rx_error_p <= 1'b0;
  else if ((s__Rx_count == L__NRX[0+:4]) && ((s__Rx_p[0] != 1'b0) || ~&s__Rx_p[L__NRX-1:9]))
    s__Rx_error_p <= 1'b1;
  else
    s__Rx_error_p <= s__Rx_error_p;
// Optional FIFO
reg s__Rx_inbuf_error = 1'b0;
if (L__INFIFO == 0) begin : gen__nofifo
  initial s__Rx_empty = 1'b1;
  always @ (posedge i_clk)
    if (i_rst) begin
      s__Rx_empty <= 1'b1;
      s__Rx <= 8'h00;
    end else begin
      if (s__Rx_wr)
        s__Rx <= s__Rx_s[1+:8];
      else
        s__Rx <= s__Rx;
      if (s__Rx_wr) begin
        if (s__Rx_rd)
          s__Rx_empty <= s__Rx_empty;
        else
          s__Rx_empty <= 1'b0;
      end else begin
        if (s__Rx_rd)
          s__Rx_empty <= 1'b1;
        else
          s__Rx_empty <= s__Rx_empty;
      end
    end
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_inbuf_error <= 1'b0;
    else
      s__Rx_inbuf_error <= (s__Rx_empty && s__Rx_rd) || (!s__Rx_empty && s__Rx_wr&& !s__Rx_rd );
end else begin : gen__fifo
  reg [L__INFIFO_NBITS:0] s__Rx_fifo_addr_in;
  reg [L__INFIFO_NBITS:0] s__Rx_fifo_addr_out;
  wire s__Rx_shift;
  reg s__Rx_fifo_has_data = 1'b0;
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_fifo_has_data <= 1'b0;
    else
      s__Rx_fifo_has_data <= (s__Rx_fifo_addr_out != s__Rx_fifo_addr_in) && !s__Rx_shift;
  initial s__Rx_empty = 1'b1;
  always @ (posedge i_clk)
    if (i_rst) begin
      s__Rx_empty <= 1'b1;
    end else begin
      case ({ s__Rx_fifo_has_data, s__Rx_empty, s__Rx_rd })
        3'b000 :  s__Rx_empty <= 1'b0;
        3'b001 :  s__Rx_empty <= 1'b1; // good read
        3'b010 :  s__Rx_empty <= 1'b1;
        3'b011 :  s__Rx_empty <= 1'b1; // bad read
        3'b100 :  s__Rx_empty <= 1'b0;
        3'b101 :  s__Rx_empty <= 1'b0; // shift, good read
        3'b110 :  s__Rx_empty <= 1'b0; // shift
        3'b111 :  s__Rx_empty <= 1'b1; // shift, bad read
      endcase
    end
  assign s__Rx_shift = s__Rx_fifo_has_data && (s__Rx_empty || s__Rx_rd);
  reg s__Rx_full = 1'b0;
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_full <= 1'b0;
    else
      s__Rx_full <= (s__Rx_fifo_addr_in == (s__Rx_fifo_addr_out ^ { 1'b1, {(L__INFIFO_NBITS){1'b0}} }));
  reg [7:0] s__Rx_fifo_mem[@INFIFO@-1:0];
  initial s__Rx_fifo_addr_in = {(L__INFIFO_NBITS+1){1'b0}};
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_fifo_addr_in <= {(L__INFIFO_NBITS+1){1'b0}};
    else if (s__Rx_wr && (!s__Rx_full || s__Rx_shift)) begin
      s__Rx_fifo_addr_in <= s__Rx_fifo_addr_in + { {(L__INFIFO_NBITS){1'b0}}, 1'b1 };
      s__Rx_fifo_mem[s__Rx_fifo_addr_in[0+:L__INFIFO_NBITS]] <= s__Rx_s[1+:8];
    end else
      s__Rx_fifo_addr_in <= s__Rx_fifo_addr_in;
  initial s__Rx_fifo_addr_out = {(L__INFIFO_NBITS+1){1'b0}};
  always @ (posedge i_clk)
    if (i_rst) begin
      s__Rx_fifo_addr_out <= {(L__INFIFO_NBITS+1){1'b0}};
      s__Rx <= 8'h00;
    end else if (s__Rx_shift) begin
      s__Rx_fifo_addr_out <= s__Rx_fifo_addr_out + { {(L__INFIFO_NBITS){1'b0}}, 1'b1 };
      s__Rx <= s__Rx_fifo_mem[s__Rx_fifo_addr_out[0+:L__INFIFO_NBITS]];
    end else begin
      s__Rx_fifo_addr_out <= s__Rx_fifo_addr_out;
    end
  always @ (posedge i_clk)
    if (i_rst)
      s__Rx_inbuf_error <= 1'b0;
    else
      s__Rx_inbuf_error <= (s__Rx_empty && s__Rx_rd) || (s__Rx_full && s__Rx_wr && !s__Rx_shift);
end
// Global error state.
always @ (posedge i_clk)
  if (i_rst)
    s__Rx_error <= 3'h0;
  else begin
    // read error
    if (s__Rx_inbuf_error)
      s__Rx_error[0] <= 1'b1;
    else if (s__Rx_error_rd)
      s__Rx_error[0] <= 1'b0;
    else
      s__Rx_error[0] <= s__Rx_error[0];
    // edge rate error
    if (s__Rx_edge_error)
      s__Rx_error[1] <= 1'b1;
    else if (s__Rx_error_rd)
      s__Rx_error[1] <= 1'b0;
    else
      s__Rx_error[1] <= s__Rx_error[1];
    // missing start or stop bit(s)
    if (s__Rx_edge_out && (s__Rx_count == L__NRX[0+:4]) && s__Rx_error_p)
      s__Rx_error[2] <= 1'b1;
    else if (s__Rx_error_rd)
      s__Rx_error[2] <= 1'b0;
    else
      s__Rx_error[2] <= s__Rx_error[2];
  end
endgenerate
