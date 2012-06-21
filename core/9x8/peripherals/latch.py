################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import math;
import re;

class latch:
  """Latch a large input port for piecewise input to the core.

This peripheral is used to input large counters and such so that the pieces of
the counter input to the processor are all valid at the same time.

The external signal is registered when the processor does an outport to
O_name_LATCH and is broken into 8-bit chunks that can be read by the processor.
These chunks are number from 0 at the far right to ceil(n/8)-1 on the far left.
The chunk is specified by an outport to O_name_ADDR and is then read by an
inport from I_name_READ.

Usage:
  PERIPHERAL latch O_LATCH O_ADDR I_READ width=n signal=i_name

Where:
  O_LATCH
    is the symbol used by the processor to register the input signal
    Note:  The name must start with "O_".
  O_ADDR
    is the symbol used by the processor to indicate which byte of the registered
    input signal is to input by the next inport from I_name_READ
    Note:  The name must start with "O_".
  I_READ
    is the symbol used by the processor to read the byte specified by the last
    outport to O_name_ADDR
    Note:  The name must start with "I_".
  width=n
    specified with width of the input signal
    Note:  The signal is broken into ceil(n/8) 8-bit words
  signal=i_name
    specifies the name of the input signal
    Note:  The name must start with "i_".

The following outports are provided by this peripheral:
  O_LATCH
  O_ADDR

The following inports are provided by this peripheral:
  I_READ

The following processor inputs are provided by this peripheral:
  i_name

Example:  Capture an external 24-bit counter:

  Within the processor architecture file include the configuration command:

    PERIPHERAL latch O_COUNT_LATCH O_COUNT_ADDR I_COUNT_READ width=24 signal=i_count

  To read the counter and put it on the stack with the MSB at the top of the
  stack:

    O_LATCH outport             ; strobe doesn't need a value to output
    0 .outport(O_ADDR) .inport(I_READ)
    1 .outport(O_ADDR) .inport(I_READ)
    2 .outport(O_ADDR) .inport(I_READ)

  or

    O_LATCH outport             ; strobe doesn't need a value to output
    0 :loop O_ADDR outport .inport(I_READ) swap 1+ dup 3 - .jumpc(loop) drop

"""

  def __init__(self,config,param_list,ixLine):
    # Ensure the right number of arguments was provided.
    if len(param_list) != 5:
      print __doc__;
      raise SSBCCException('Wrong number of arguments to peripheral "latch" at line %d' % ixLine);
    # parse the required positional parameters
    if param_list[0][0][0:2] != 'O_':
      print __doc__;
      raise SSBCCException('First positional argument must start with "O_" at line %d' % ixLine);
    if param_list[1][0][0:2] != 'O_':
      print __doc__;
      raise SSBCCException('Second positional argument must start with "O_" at line %d' % ixLine);
    if param_list[2][0][0:2] != 'I_':
      print __doc__;
      raise SSBCCException('Third positional argument must start with "I_" at line %d' % ixLine);
    self.o_latch = param_list[0][0];
    self.o_addr  = param_list[1][0];
    self.i_read  = param_list[2][0];
    # parse the non-positional parameters
    self.i_width = None;
    self.i_signal = None;
    for param_tuple in param_list[3:]:
      param = param_tuple[0];
      param_arg = param_tuple[1:];
      # processor input signal name
      if param == 'signal':
        if type(self.i_signal) != type(None):
          raise SSBCCException('"signal=i_name" can only be specified once at line %d' % ixLine);
        if param_arg[0][0:2] != 'i_':
          raise SSBCCException('signal name must start with "i_" at line %d' % ixLine);
        self.i_signal = param_arg[0];
      elif param == 'width':
        if type(self.i_width) != type(None):
          raise SSBCCException('"width=n" can only be specified once at line %d' % ixLine);
        self.i_width = int(param_arg[0]);
      else:
        raise SSBCCException('Unrecognized option at line %d: "%s"' % (ixLine,param,));
    # Ensure the required parameters are set.
    if type(self.i_signal) == type(None):
      raise SSBCCException('signal name not set at line %d' % ixLine);
    if type(self.i_width) == type(None):
      raise SSBCCException('signal width not set at line %d' % ixLine);
    # Derived parameters
    self.addr_width = int(math.ceil(math.log(self.i_width/8,2)));
    self.latch_width = 8*((self.i_width+7)/8);
    # Configure the processor I/Os, etc.
    config['ios'].append((self.i_signal,self.i_width,'input',));
    self.s_addr = 's_internal_%03X' % len(config['signals']);
    config['signals'].append((self.s_addr,self.addr_width,));
    self.s_signal = 's_internal_%03X' % len(config['signals']);
    config['signals'].append((self.s_signal,8,));
    config['inports'].append((self.i_read,
                             (self.s_signal,8,'data',),
                            ));
    self.ix__o_latch = len(config['outports']);
    config['outports'].append((self.o_latch,
                             ));
    self.ix__o_addr = len(config['outports']);
    config['outports'].append((self.o_addr,
                             ));

  def GenAssembly(self,config):
    pass;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    body = """
//
// latch peripheral for @I_SIGNAL@
//
generate
// Register the input signal when  commanded.
reg [@LATCH_WIDTH@-1:0] s_latch = {(@LATCH_WIDTH@){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s_latch <= {(@LATCH_WIDTH@){1'b0}};
  else if (s_outport && (s_T == 8'd@IX__O_LATCH@))
    s_latch[0+:@WIDTH@] <= @I_SIGNAL@;
  else
    s_latch <= s_latch;
// Latch the mux address when commanded.
reg [@ADDR_WIDTH@-1:0] s_addr = {(@ADDR_WIDTH@){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s_addr <= {(@ADDR_WIDTH@){1'b0}};
  else if (s_outport && (s_T == 8'd@IX__O_ADDR@))
    s_addr <= s_N[0+:@ADDR_WIDTH@];
  else
    s_addr <= s_addr;
// Run the mux.
integer ix;
initial @S_SIGNAL@ = 8'h00;
always @ (posedge i_clk)
  if (i_rst)
    @S_SIGNAL@ <= 8'h00;
  else begin
    @S_SIGNAL@ <= 8'h00;
    for (ix=0; ix<@LATCH_WIDTH@/8; ix=ix+1)
      if (ix[0+:@ADDR_WIDTH@] == s_addr)
        @S_SIGNAL@ <= s_latch[8*ix+:8];
  end
endgenerate
""";
    for subs in (
                  ('@ADDR_WIDTH@',      str(self.addr_width),),
                  ('@IX__O_ADDR@',      str(self.ix__o_addr),),
                  ('@IX__O_LATCH@',     str(self.ix__o_latch),),
                  ('@LATCH_WIDTH@',     str(self.latch_width),),
                  ('@S_SIGNAL@',        self.s_signal,),
                  ('@I_SIGNAL@',        self.i_signal,),
                  ('@WIDTH@',           str(self.i_width),),
                ):
      body = re.sub(subs[0],subs[1],body);
    fp.write(body);
