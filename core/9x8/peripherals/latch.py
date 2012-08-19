################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import math;
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class latch(SSBCCperipheral):
  """Latch a large input port for piecewise input to the core.

This peripheral is used to input large counters and such so that the pieces of
the counter input to the processor are all valid at the same time.

The external signal is registered when the processor does an outport to
O_name_LATCH and is broken into 8-bit chunks that can be read by the processor.
These chunks are number from 0 at the far right to ceil(n/8)-1 on the far left.
The chunk is specified by an outport to O_name_ADDR and is then read by an
inport from I_name_READ.

Usage:
  PERIPHERAL latch outport_latch=O_LATCH \\
                   outport_addr=O_ADDR \\
                   inport=I_READ \\
                   insignal=i_name \\
                   width=n

Where:
  outport_latch=O_LATCH
    is the symbol used by the processor to register the input signal
    Note:  The name must start with "O_".
  outport_addr=O_ADDR
    is the symbol used by the processor to indicate which byte of the registered
    input signal is to input by the next inport from I_name_READ
    Note:  The name must start with "O_".
  inport=I_READ
    is the symbol used by the processor to read the byte specified by the last
    outport to O_name_ADDR
    Note:  The name must start with "I_".
  insignal=i_name
    specifies the name of the input signal
    Note:  The name must start with "i_".
  width=n
    specified with width of the input signal
    Note:  The signal is broken into ceil(n/8) 8-bit words
    Note:  This peripheral doesn't make sense when width < 8.  It will issue an
           error when this condition is encountered.

The following outports are provided by this peripheral:
  O_LATCH
    this outport instructs the peripheral to latch the specified signal
    Note:  No argument is required for this outport.  I.e., it is equivalent to
           a "strobe" outport.
  O_ADDR
    this outport specifies which 8-bit chunk of the latched signal will be read
    by I_READ

The following inport is provided by this peripheral:
  I_READ
    this inport is used to read the 8-bit segment of the latched signal as
    specified by O_ADDR

The following processor inputs are provided by this peripheral:
  i_name
    this is a "width" wide signal connected to the FPGA fabric

Example:  Capture an external 24-bit counter:

  Within the processor architecture file include the configuration command:

    PERIPHERAL latch outport_latch=O_COUNT_LATCH \\
                     outport_addr=O_COUNT_ADDR \\
                     inport=I_COUNT_READ \\
                     insignal=i_count \\
                     width=24

  To read the counter and put it on the stack with the MSB at the top of the
  stack:

    O_COUNT_LATCH outport       ; doesn't need a value to output
    0 .outport(O_COUNT_ADDR) .inport(I_COUNT_READ)
    1 .outport(O_COUNT_ADDR) .inport(I_COUNT_READ)
    2 .outport(O_COUNT_ADDR) .inport(I_COUNT_READ)

  or

    O_COUNT_LATCH outport
    0 :loop O_COUNT_ADDR outport .inport(I_COUNT_READ) swap 1+ dup 3 - .jumpc(loop) drop

"""

  def __init__(self,config,param_list,ixLine):
    # Parse the parameters.
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      if param == 'outport_latch':
        self.AddAttr(config,param,param_arg,r'O_\w+$',ixLine);
      elif param == 'outport_addr':
        self.AddAttr(config,param,param_arg,r'O_\w+$',ixLine);
      elif param == 'inport':
        self.AddAttr(config,param,param_arg,r'I_\w+$',ixLine);
      elif param == 'insignal':
        self.AddAttr(config,param,param_arg,r'i_\w+$',ixLine);
      elif param == 'width':
        self.AddAttr(config,param,param_arg,r'[1-9]\d*$',ixLine);
        self.width = int(self.width);
      else:
        raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are set.
    for param in ('outport_latch', 'outport_addr', 'inport', 'insignal', 'width', ):
      if not hasattr(self,param):
        raise SSBCCException('Required parameter "%s" not provided at line %d', (param,ixLine,));
    # Ensure parameters are reasonable.
    if self.width <= 8:
      raise SSBCCException('The "latch" peripheral doesn\'t make sense when width <= 8 on line %d' % ixLine);
    # Derived parameters
    self.latch_width = 8*((self.width+7)/8);
    self.addr_width = int(math.ceil(math.log(self.latch_width/8,2)));
    # Configure the processor I/Os, etc.
    config.AddIO(self.insignal,self.width,'input');
    config.AddSignal('s__%s__select' % self.insignal,8);
    config.AddInport((self.inport,
                     ('s__%s__select' % self.insignal,8,'data',),
                    ));
    self.ix__o_latch = config.NOutports();
    config.AddOutport((self.outport_latch,));
    self.ix__o_addr = config.NOutports();
    config.AddOutport((self.outport_addr,));

  def GenVerilog(self,fp,config):
    body = """
//
// latch peripheral for @INSIGNAL@
//
generate
// Register the input signal when  commanded.
reg [@LATCH_WIDTH@-1:0] s__latch = {(@LATCH_WIDTH@){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__latch <= {(@LATCH_WIDTH@){1'b0}};
  else if (s_outport && (s_T == 8'd@IX_O_LATCH@))
    s__latch[0+:@WIDTH@] <= @INSIGNAL@;
  else
    s__latch <= s__latch;
// Latch the mux address when commanded.
reg [@ADDR_WIDTH@-1:0] s__addr = {(@ADDR_WIDTH@){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__addr <= {(@ADDR_WIDTH@){1'b0}};
  else if (s_outport && (s_T == 8'd@IX_O_ADDR@))
    s__addr <= s_N[0+:@ADDR_WIDTH@];
  else
    s__addr <= s__addr;
// Run the mux.
integer ix;
initial s__select = 8'h00;
always @ (posedge i_clk)
  if (i_rst)
    s__select <= 8'h00;
  else begin
    s__select <= 8'h00;
    for (ix=0; ix<@LATCH_WIDTH@/8; ix=ix+1)
      if (ix[0+:@ADDR_WIDTH@] == s__addr)
        s__select <= s__latch[8*ix+:8];
  end
endgenerate
""";
    for subs in (
                  (r'\bix\b',           'ix__@INSIGNAL@',),
                  (r'\bs__',            's__@INSIGNAL@__',),
                  ('@ADDR_WIDTH@',      str(self.addr_width),),
                  ('@IX_O_ADDR@',       str(self.ix__o_addr),),
                  ('@IX_O_LATCH@',      str(self.ix__o_latch),),
                  ('@LATCH_WIDTH@',     str(self.latch_width),),
                  ('@INSIGNAL@',        self.insignal,),
                  ('@WIDTH@',           str(self.width),),
                ):
      body = re.sub(subs[0],subs[1],body);
    fp.write(body);
