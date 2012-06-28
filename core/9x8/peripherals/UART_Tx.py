################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import re;

from ssbccUtil import *;

class UART_Tx:
  """Transmit side of a UART:
  1 start bit
  8 data bits
  n stop bits

Usage:
  PERIPHERAL UART_Tx outport=O_name \\
                     inport=I_name \\
                     baudmethod={clk/rate,count} \\
                     [noFIFO|FIFO=n] \\
                     [nStop=n] \\
                     [outsignal=o_name]
Where:
  outport=O_name
    specifies the symbol used by the outport instruction to write a byte to the
    peripheral
    Note:  The name must start with "O_".
  inport=I_name
    specifies the symbol used by the inport instruction to get the status of the
    peripheral
    Note:  The name must start with "I_".
  baudmethod
    specifies the method to generate the desired bit rate:
    1st method:  clk/rate
      clk is the frequency of "i_clk" in Hz
        a number will be interpreted as the clock frequency in Hz
        a symbol will be interpreted as a parameter
          Note:  this parameter must have been declared with a "PARAMETER"
          command
      rate is the desired baud rate
        this is specified as per "clk"
  noFIFO
    the peripheral will not have a FIFO
    this is the default
  FIFO=n
    adds a FIFO of depth n
  nStop=n
    configures the peripheral for n stop bits
    default:  1 stop bit
    Note:  n must be at least 1
    Note:  normal values are 1 and 2
    2nd method:
      specify the number of "i_clk" clock cycles between bit edges
  outsignal=o_name
    optionally specifies the name of the module's output signal
    Default:  o_UART_Tx

The following OUTPORTs are provided by this peripheral:
  O_name_TX
    this is the next 8-bit value to transmit or to queue for transmission

The following INPORTs are provided by this peripheral:
  I_name_TX
    bit 0:  busy status
      this bit will be high when the core cannot accept more data
      Note:  If there is no FIFO this means that the core is still
        transmitting the last byte.  If there is a FIFO it means that the FIFO
        cannot accept any more data.

Example:  Configure for 115200 baud using a 100 MHz clock and transmit the
          message "Hello World!"

  Within the processor architecture file include the configuration command:

    PERIPHERAL UART_Tx O_UART_TX I_UART_TX baudmethod=100000000/115200

  Within the processor assembly, include the code:

    C"Hello World!\\r\\n"
    :loop 1- swap .outport(O_UART_TX) :wait .inport(I_UART_TX_BUSY) .jumpc(wait) .jumpc(loop,nop) drop

"""

  def __init__(self,config,param_list,ixLine):
    # Get the parameters.
    self.baudmethod = None;
    self.FIFO = None;
    self.inport = None;
    self.nStop = None;
    self.outport = None;
    self.outsignal = None;
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      # baudmethod=rate/baudrate or baudmethod=decimate_count
      if param == 'baudmethod':
        if self.baudmethod != None:
          raise SSBCCException('baudmethod can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('baudmethod argument missing at line %d' % ixLine);
        self.ProcessBaudMethod(config,param_arg);
      # FIFO
      elif param == 'FIFO':
        if self.FIFO != None:
          if type(self.FIFO) == int:
            raise SSBCCException('FIFO can only be specified once at line %d' % ixLine);
          else
            raise SSBCCException('FIFO cannot be specified after noFIFO line %d' % ixLine);
        self.FIFO = int(param_arg);
        if self.FIFO <= 0:
          raise SSBCCException('FIFO length must be positive at line %d' % ixLine);
      # inport
      elif param == 'inport':
        if self.inport != None:
          raise SSBCCException('inport can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('inport symbol name missing at line %d' % ixLine);
        if not re.match(r'^I_\w+$',param_arg):
          raise SSBCCException('Malformed inport symbol name at line %d' % ixLine);
        self.inport = param_arg;
      # noFIFO
      elif param == 'noFIFO':
        if self.FIFO != None:
          if type(self.FIFO) == int:
            raise SSBCCException('noFIFO cannot be specified after "FIFO" at line %d' % ixLine);
          else
            raise SSBCCException('noFIFO can only be specified once at line %d' % ixLine);
        if param_arg != None:
          raise SSBCCException('noFIFO cannot have an argument at line %d' % ixLine);
        self.FIFO = False;
      # nStop=
      elif param == 'nStop':
        if self.nStop != None:
          raise SSBCCException('nStop can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('nStop must have an argument at line %d' % ixLine);
        try:
          self.nStop = int(param_arg);
        except:
          raise SSBCCException('Malformed value for nStop at line %d' % ixLine);
        if self.nStop <= 0:
          raise SSBCCException('nStop must be 1 or more at line %d' % ixLine);
      # outport
      elif param == 'outport':
        if self.outport != None:
          raise SSBCCException('outport can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('outport symbol name missing at line %d' % ixLine);
        if not re.match(r'^O_\w+$',param_arg):
          raise SSBCCException('Malformed outport symbol name at line %d' % ixLine);
        self.outport = param_arg;
      # outsignal
      elif param == 'outsignal':
        if self.outsignal != None:
          raise SSBCCException('outsignal can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('outsignal output port name missing at line %d' % ixLine);
        if not re.match(r'o_\w+$',param_arg):
          raise SSBCCException('Malformed outsignal output port name at line %d' % ixLine);
        self.outsignal = param_arg;
      # no match
      else:
        raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are provided and set non-specified optional parameters.
    if self.outport == None:
      raise SSBCCException('Required parameter "outport" is missing at line %d' % ixLine);
    if self.inport == None:
      raise SSBCCException('Required parameter "inport" is missing at line %d' % ixLine);
    if self.baudmethod == None:
      raise SSBCCException('Required parameter "baudmethod" is missing at line %d' % ixLine);
    if self.FIFO == None:
      self.FIFO = False;
    if self.outsignal == None:
      self.outsignal = 'o_UART_Tx';
    if self.nStop == None:
      self.nStop = 1;
    # List the I/Os and global signals required by this peripheral.
    config['ios'].append((self.outsignal,1,'output',));
    config['signals'].append(('s_%s_Tx' % self.outsignal,8,));
    config['signals'].append(('s_%s_busy' % self.outsignal,1,));
    config['signals'].append(('s_%s_wr' % self.outsignal,1,));
    config['inports'].append((self.inport,
                             ('s_%s_busy' % self.outsignal,1,'data',),
                            ));
    config['outports'].append((self.outport,
                              ('s_%s_Tx' % self.outsignal,8,'data',),
                              ('s_%s_wr' % self.outsignal,1,'strobe',),
                             ));
    # Add the 'clog2' function to the core.
    config['functions']['clog2'] = True;

  def ProcessBaudMethod(self,config,param_arg):
    if param_arg.find('/') > 0:
      baudarg = re.findall('([^/]+)',param_arg);
      if len(baudarg) != 2:
        raise SSBCCException('baudmethod cannot have more than one "/" at line %d' % ixLine);
      if not (re.match(r'^\d+$',baudarg[0]) and re.match(r'^\d+$',baudarg[1])):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet at line %d' % ixLine);
      self.baudmethod = (int(baudarg[0])+int(baudarg[1])/2)/int(baudarg[1]);
    else:
      baudarg = param_arg;
      if not re.match(r'^\d+$',baudarg):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet at line %d' % ixLine);
      self.baudmethod = int(baudarg);

  def GenAssembly(self,config):
    pass;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    body = """//
// UART_Tx "@NAME@" peripheral
//
generate
// Count the clock cycles to decimate to the desired baud rate.
localparam L_@NAME@_COUNT       = @BAUDMETHOD@;
localparam L_@NAME@_COUNT_NBITS = @clog2@(L_@NAME@_COUNT);
reg [L_@NAME@_COUNT_NBITS-1:0] s_count = {(L_@NAME@_COUNT_NBITS){1\'b0}};
reg s_count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s_count <= {(L_@NAME@_COUNT_NBITS){1\'b0}};
    s_count_is_zero <= 1'b0;
  end else if (s_@NAME@_wr || s_count_is_zero) begin
    s_count <= L_@NAME@_COUNT[0+:L_@NAME@_COUNT_NBITS];
    s_count_is_zero <= 1'b0;
  end else begin
    s_count <= s_count - { {(L_@NAME@_COUNT_NBITS-1){1'b0}}, 1'b1 };
    s_count_is_zero <= (s_count == { {(L_@NAME@_COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s_out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s_out_stream <= 8'hFF;
  else if (s_@NAME@_wr)
    s_out_stream <= s_@NAME@_Tx;
  else if (s_count_is_zero)
    s_out_stream <= { 1'b1, s_out_stream[1+:7] };
  else
    s_out_stream <= s_out_stream;
// Generate the output bit stream.
initial @NAME@ = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    @NAME@ <= 1'b1;
  else if (s_@NAME@_wr)
    @NAME@ <= 1'b0;
  else if (s_count_is_zero)
    @NAME@ <= s_out_stream[0];
  else
    @NAME@ <= @NAME@;
// Count down the number of bits.
localparam L_@NAME@_NTX       = 1+8+@NSTOP@-1;
localparam L_@NAME@_NTX_NBITS = @clog2@(L_@NAME@_NTX);
reg [L_@NAME@_NTX_NBITS-1:0] s_ntx = {(L_@NAME@_NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s_ntx <= {(L_@NAME@_NTX_NBITS){1'b0}};
  else if (s_@NAME@_wr)
    s_ntx <= L_@NAME@_NTX[0+:L_@NAME@_NTX_NBITS];
  else if (s_count_is_zero)
    s_ntx <= s_ntx - { {(L_@NAME@_NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s_ntx <= s_ntx;
// The status bit is 1 if the core is done and 0 otherwise.
initial s_@NAME@_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s_@NAME@_busy <= 1'b0;
  else if (s_@NAME@_wr)
    s_@NAME@_busy <= 1'b1;
  else if (s_count_is_zero && (s_ntx == {(L_@NAME@_NTX_NBITS){1'b0}}))
    s_@NAME@_busy <= 1'b0;
  else
    s_@NAME@_busy <= s_@NAME@_busy;
endgenerate
""";
    for subs in (
                  ('@BAUDMETHOD@', str(self.baudmethod), ),
                  ('@NAME@',       self.outsignal, ),
                  ('@NSTOP@',      str(self.nStop) ),
                ):
      body = re.sub(subs[0],subs[1],body);
    if config['define_clog2']:
      body = re.sub('@clog2@','clog2',body);
    else:
      body = re.sub('@clog2@','$clog2',body);
    fp.write(body);
