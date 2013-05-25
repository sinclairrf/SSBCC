//
// PERIPHERAL:  AXI4-Lite slave dual-port-RAM interface
//
// Note:  While the AXI4-Lite protocol allows simultaneous read and write
// operations, only one side of the dual-port RAM is available to the AXI4-lite
// interface.  This requires internal arbitration between the two operations
// with either the first or the write operation being preferred.
//
// Note:  The dual-port-ram is implemented as write-through memory.
//
generate
localparam L__SIZE = @SIZE@;
localparam L__NBITS_SIZE = $clog2(L__SIZE);
localparam L__RESP_OKAY = 2'b00;
localparam L__RESP_EXOKAY = 2'b01;
localparam L__RESP_SLVERR = 2'b10;
localparam L__RESP_DECERR = 2'b11;
// Declare the dual-port memory.
reg [7:0] s__mem[L__SIZE-1:0];
// AXI4-Lite side of the dual-port memory;
initial o_bresp = L__RESP_OKAY;
initial o_rresp = L__RESP_OKAY;
reg                     s__axi_idle             = 1'b1;
reg                     s__axi_got_waddr        = 1'b0;
reg                     s__axi_got_wdata        = 1'b0;
reg                     s__axi_got_raddr        = 1'b0;
reg [L__NBITS_SIZE-1:2] s__axi_addr             = {(L__NBITS_SIZE-2){1'b0}};
always @ (posedge i_aclk)
  if (~i_aresetn) begin
    s__axi_idle         <= 1'b1;
    s__axi_got_waddr    <= 1'b0;
    s__axi_got_wdata    <= 1'b0;
    s__axi_got_raddr    <= 1'b0;
    s__axi_addr         <= {(L__NBITS_SIZE-2){1'b0}};
  end else begin
    s__axi_idle         <= s__axi_idle;
    s__axi_got_waddr    <= s__axi_got_waddr;
    s__axi_got_wdata    <= s__axi_got_wdata;
    s__axi_got_raddr    <= s__axi_got_raddr;
    s__axi_addr         <= s__axi_addr;
    o_awready           <= 1'b0;
    o_wready            <= 1'b0;
    o_arready           <= 1'b0;
    if (s__axi_idle) begin
      if (i_awvalid) begin
        s__axi_idle <= 1'b0;
        s__axi_got_waddr <= 1'b1;
        s__axi_addr <= i_awaddr[L__NBITS_SIZE-1:2];
        o_awready <= 1'b1;
      end else if (i_arvalid) begin
        s__axi_idle <= 1'b0;
        s__axi_got_raddr <= 1'b1;
        s__axi_addr <= i_araddr[L__NBITS_SIZE-1:2];
        o_arready <= 1'b1;
      end
    end else if (s__axi_got_waddr) begin
      if (i_wvalid) begin
        s__axi_got_waddr <= 1'b0;
        s__axi_got_wdata <= 1'b1;
        o_wready <= 1'b1;
      end
    end else if (s__axi_got_wdata) begin
      if (i_bready) begin
        s__axi_got_wdata <= 1'b0;
        s__axi_idle <= 1'b1;
      end
    end else if (s__axi_got_raddr) begin
      if (i_rready) begin
        s__axi_got_raddr <= 1'b0;
        s__axi_idle <= 1'b1;
      end
    end
  end
initial o_bvalid = 1'b0;
always @ (s__axi_got_wdata)
  o_bvalid <= s__axi_got_wdata;
initial o_rvalid = 1'b0;
always @ (s__axi_got_raddr)
  o_rvalid <= s__axi_got_raddr;
wire [3:0] s__wstrb;
genvar ix__wstrb;
for (ix__wstrb=0; ix__wstrb<4; ix__wstrb=ix__wstrb+1) begin : gen__wstrb
  assign s__wstrb[ix__wstrb] = s__axi_got_waddr && i_wvalid && i_wstrb[ix__wstrb];
end
genvar ix__mem;
for (ix__mem=0; ix__mem<4; ix__mem=ix__mem+1) begin : gen__wr
  localparam [1:0] L__ix_mem = ix__mem;
  always @ (posedge i_aclk) begin
    if (s__wstrb[ix__mem])
      s__mem[{ s__axi_addr, L__ix_mem }] = i_wdata[8*ix__mem+:8];
    o_rdata[8*ix__mem+:8] <= s__mem[{ s__axi_addr, L__ix_mem }];
  end
end
// Micro controller side of the dual-port memory.
always @ (posedge i_clk) begin
  if (s__mc_wr)
    s__mem[s__mc_addr] = s__mc_wdata;
end
always @ (*)
  s__mc_rdata <= s__mem[s__mc_addr];
endgenerate
