//
// PERIPHERAL:  counter (@INSIGNAL@)
//

@NARROW_BEGIN@
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__counter <= @WIDTH@'d0;
  else if (@INSIGNAL@)
    s__counter <= s__counter + @WIDTH@'d1;
  else
    s__counter <= s__counter;
@NARROW_END@

@WIDE_BEGIN@
reg [@WIDTH-1@:0] s__count;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__count <= @WIDTH@'d0;
  else if (@INSIGNAL@)
    s__count <= s__count + @WIDTH@'d1;
  else
    s__count <= s__count;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__counter <= @WIDTH@'d0;
  else if (s_outport && (s_T == @IX_LATCH@))
    s__counter <= s__count;
  else if (s_inport && (s_T == @IX_INPORT@))
    s__counter <= { 8'd0, s__counter[8+:@WIDTH-8@] };
  else
    s__counter <= s__counter;
@WIDE_END@
