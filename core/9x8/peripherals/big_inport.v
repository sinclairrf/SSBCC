//
// PERIPHERAL:  big_inport (@INSIGNAL@)
//

always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__biginport__@INSIGNAL@ <= @WIDTH@'d0;
  else if (s_outport && (s_T == @IX_LATCH@))
    s__biginport__@INSIGNAL@ <= @INSIGNAL@;
  else if (s_inport && (s_T == @IX_INPORT@))
    s__biginport__@INSIGNAL@ <= { 8'd0, s__biginport__@INSIGNAL@[8+:@WIDTH-8@] };
  else
    s__biginport__@INSIGNAL@ <= s__biginport__@INSIGNAL@;
