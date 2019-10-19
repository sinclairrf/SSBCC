//
// PERIPHERAL:  big_outport (@OUTSIGNAL@)
//

always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    @OUTSIGNAL@ <= @WIDTH@'d0;
  else if (s_outport && (s_T == @IX_OUTPORT@))
    @OUTSIGNAL@ <= { @OUTSIGNAL@[0+:@WIDTH-8@], s_N };
  else
    @OUTSIGNAL@ <= @OUTSIGNAL@;
