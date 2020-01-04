// Copyright 2020, Rodney Sinclair
// Open-Drain I/O (@IOSIGNAL@)

@NARROW_BEGIN@
assign @IOSIGNAL@ = (s__@IOSIGNAL@ == 1'b0) ? 1'b0 : 1'bz;
@NARROW_END@

@WIDE_BEGIN@
generate
genvar ix;
for (ix=0; ix<@WIDTH@; ix = ix+1) begin : gen_@IOSIGNAL@
  assign @IOSIGNAL@[ix] = (s__@IOSIGNAL@[ix] == 1'b0) ? 1'b0 : 1'bz;
end
endgenerate
@WIDE_END@
