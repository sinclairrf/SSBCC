################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class UART_Tx(SSBCCperipheral):
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
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      if param == 'baudmethod':
        baudformat = r'([1-9]\d*|(([1-9]\d*|G_\w+)/([1-9]\d*|G_\w+)))$';
        self.AddAttr(config,'baudmethod',param_arg,baudformat,ixLine);
        self.ProcessBaudMethod(config);
      elif param == 'FIFO':
        self.AddAttr(config,'FIFO',param_arg,r'[1-9]\d*$',ixLine);
        self.FIFO = int(self.FIFO);
      elif param == 'inport':
        self.AddAttr(config,'inport',param_arg,'I_\w+$',ixLine);
      elif param == 'noFIFO':
        self.AddAttr(config,'noFIFO','True','True',ixLine);
      elif param == 'nStop':
        self.AddAttr(config,'nStop',param_arg,r'[12]$',ixLine);
        self.nStop = int(self.nStop);
      elif param == 'outport':
        self.AddAttr(config,'outport',param_arg,r'O_\w+$',ixLine);
      elif param == 'outsignal':
        self.AddAttr(config,'outsignal',param_arg,r'o_\w+$',ixLine);
      # no match
      else:
        raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are provided.
    if not hasattr(self,'baudmethod'):
      raise SSBCCException('Required parameter "baudmethod" is missing at line %d' % ixLine);
    if not hasattr(self,'inport'):
      raise SSBCCException('Required parameter "inport" is missing at line %d' % ixLine);
    if not hasattr(self,'outport'):
      raise SSBCCException('Required parameter "outport" is missing at line %d' % ixLine);
    # Set optional parameters.
    if not hasattr(self,'nStop'):
      self.nStop = 1;
    if not hasattr(self,'outsignal'):
      self.outsignal = 'o_UART_Tx';
    if not hasattr(self,'FIFO') and not hasattr(self,'noFIFO'):
      self.noFIFO = True;
    # Ensure parameters do not conflict.
    if hasattr(self,'FIFO') and hasattr(self,'noFIFO'):
      raise SSBCCException('Only one of "FIFO" and "noFIFO" can be specified at line %d' % ixLine);
    # List the I/Os and global signals required by this peripheral.
    config.AddIO(self.outsignal,1,'output');
    config.AddSignal('s__%s__Tx' % self.outsignal,8);
    config.AddSignal('s__%s__busy' % self.outsignal,1);
    config.AddSignal('s__%s__wr' % self.outsignal,1);
    config.AddInport((self.inport,
                    ('s__%s__busy' % self.outsignal,1,'data',),
                   ));
    config.AddOutport((self.outport,
                      ('s__%s__Tx' % self.outsignal,8,'data',),
                      ('s__%s__wr' % self.outsignal,1,'strobe',),
                     ));
    # Add the 'clog2' function to the core.
    config.functions['clog2'] = True;

  def ProcessBaudMethod(self,config):
    if self.baudmethod.find('/') > 0:
      baudarg = re.findall('([^/]+)',self.baudmethod);
      if len(baudarg) != 2:
        raise Exception('Program Bug:  Should not get here with two "/"s in baudmethod');
      if not (re.match(r'^\d+$',baudarg[0]) and re.match(r'^\d+$',baudarg[1])):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet at line %d' % ixLine);
      self.baudmethod = (int(baudarg[0])+int(baudarg[1])/2)/int(baudarg[1]);
    else:
      if not re.match(r'^\d+$',self.baudmethod):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet at line %d' % ixLine);
      self.baudmethod = int(self.baudmethod);

  def GenVerilog(self,fp,config):
    body = """//
// PERIPHERAL UART_Tx:  @NAME@
//
generate
reg s__@NAME@__uart_busy;
@FIFOBODY@
// Count the clock cycles to decimate to the desired baud rate.
localparam L__@NAME@__COUNT       = @BAUDMETHOD@;
localparam L__@NAME@__COUNT_NBITS = @clog2@(L__@NAME@__COUNT);
reg [L__@NAME@__COUNT_NBITS-1:0] s__@NAME@__count = {(L__@NAME@__COUNT_NBITS){1\'b0}};
reg s__@NAME@__count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__@NAME@__count <= {(L__@NAME@__COUNT_NBITS){1\'b0}};
    s__@NAME@__count_is_zero <= 1'b0;
  end else if (s__@NAME@__go || s__@NAME@__count_is_zero) begin
    s__@NAME@__count <= L__@NAME@__COUNT[0+:L__@NAME@__COUNT_NBITS];
    s__@NAME@__count_is_zero <= 1'b0;
  end else begin
    s__@NAME@__count <= s__@NAME@__count - { {(L__@NAME@__COUNT_NBITS-1){1'b0}}, 1'b1 };
    s__@NAME@__count_is_zero <= (s__@NAME@__count == { {(L__@NAME@__COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s__@NAME@__out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__out_stream <= 8'hFF;
  else if (s__@NAME@__go)
    s__@NAME@__out_stream <= s__@NAME@__Tx_data;
  else if (s__@NAME@__count_is_zero)
    s__@NAME@__out_stream <= { 1'b1, s__@NAME@__out_stream[1+:7] };
  else
    s__@NAME@__out_stream <= s__@NAME@__out_stream;
// Generate the output bit stream.
initial @NAME@ = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    @NAME@ <= 1'b1;
  else if (s__@NAME@__go)
    @NAME@ <= 1'b0;
  else if (s__@NAME@__count_is_zero)
    @NAME@ <= s__@NAME@__out_stream[0];
  else
    @NAME@ <= @NAME@;
// Count down the number of bits.
localparam L__@NAME@__NTX       = 1+8+@NSTOP@-1;
localparam L__@NAME@__NTX_NBITS = @clog2@(L__@NAME@__NTX);
reg [L__@NAME@__NTX_NBITS-1:0] s__@NAME@__ntx = {(L__@NAME@__NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__ntx <= {(L__@NAME@__NTX_NBITS){1'b0}};
  else if (s__@NAME@__go)
    s__@NAME@__ntx <= L__@NAME@__NTX[0+:L__@NAME@__NTX_NBITS];
  else if (s__@NAME@__count_is_zero)
    s__@NAME@__ntx <= s__@NAME@__ntx - { {(L__@NAME@__NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s__@NAME@__ntx <= s__@NAME@__ntx;
// The status bit is 1 if the core is done and 0 otherwise.
initial s__@NAME@__uart_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__uart_busy <= 1'b0;
  else if (s__@NAME@__go)
    s__@NAME@__uart_busy <= 1'b1;
  else if (s__@NAME@__count_is_zero && (s__@NAME@__ntx == {(L__@NAME@__NTX_NBITS){1'b0}}))
    s__@NAME@__uart_busy <= 1'b0;
  else
    s__@NAME@__uart_busy <= s__@NAME@__uart_busy;
@UARTBUSY@
endgenerate
""";
    nofifobody = """// noFIFO
wire s__@NAME@__go = s__@NAME@__wr;
wire [7:0] s__@NAME@__Tx_data = s__@NAME@__Tx;""";
    fifobody = """// FIFO=@FIFO@
localparam L__@NAME@__FIFO_LENGTH = @FIFO@;
localparam L__@NAME@__FIFO_NBITS = @clog2@(L__@NAME@__FIFO_LENGTH);
reg [7:0] s__@NAME@__fifo_mem[@FIFO@-1:0];
reg [L__@NAME@__FIFO_NBITS:0] s__@NAME@__fifo_addr_in = {(L__@NAME@__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__fifo_addr_in <= {(L__@NAME@__FIFO_NBITS+1){1'b0}};
  else if (s__@NAME@__wr) begin
    s__@NAME@__fifo_addr_in <= s__@NAME@__fifo_addr_in + { {(L__@NAME@__FIFO_NBITS){1'b0}}, 1'b1 };
    s__@NAME@__fifo_mem[s__@NAME@__fifo_addr_in[0+:L__@NAME@__FIFO_NBITS]] <= s__@NAME@__Tx;
  end
reg [L__@NAME@__FIFO_NBITS:0] s__@NAME@__fifo_addr_out;
reg s__@NAME@__fifo_has_data = 1'b0;
reg s__@NAME@__fifo_full = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__@NAME@__fifo_has_data <= 1'b0;
    s__@NAME@__fifo_full <= 1'b0;
  end else begin
    s__@NAME@__fifo_has_data <= (s__@NAME@__fifo_addr_out != s__@NAME@__fifo_addr_in);
    s__@NAME@__fifo_full <= (s__@NAME@__fifo_addr_out == (s__@NAME@__fifo_addr_in ^ { 1'b1, {(L__@NAME@__FIFO_NBITS){1'b0}} }));
  end
initial s__@NAME@__fifo_addr_out = {(L__@NAME@__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__fifo_addr_out <= {(L__@NAME@__FIFO_NBITS+1){1'b0}};
  else if (s__@NAME@__go)
    s__@NAME@__fifo_addr_out <= s__@NAME@__fifo_addr_out + { {(L__@NAME@__FIFO_NBITS){1'b0}}, 1'b1 };
reg s__@NAME@__go = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__go <= 1'b0;
  else if (s__@NAME@__fifo_has_data && !s__@NAME@__uart_busy && !s__@NAME@__go)
    s__@NAME@__go <= 1'b1;
  else
    s__@NAME@__go <= 1'b0;
reg [7:0] s__@NAME@__Tx_data = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__@NAME@__Tx_data <= 8'd0;
  else
    s__@NAME@__Tx_data <= s__@NAME@__fifo_mem[s__@NAME@__fifo_addr_out[0+:L__@NAME@__FIFO_NBITS]];""";
    if hasattr(self,'noFIFO'):
      body = re.sub('@FIFOBODY@',nofifobody,body);
      body = re.sub('@UARTBUSY@','always @ (*) s__@NAME@__busy = s__@NAME@__uart_busy;',body);
    else:
      body = re.sub('@FIFOBODY@',fifobody,body);
      body = re.sub('@UARTBUSY@','always @ (*) s__@NAME@__busy = s__@NAME@__fifo_full;',body);
      body = re.sub('@FIFO@',str(self.FIFO),body);
    for subs in (
                  ('@BAUDMETHOD@', str(self.baudmethod),),
                  ('@NAME@',       self.outsignal,),
                  ('@NSTOP@',      str(self.nStop), ),
                ):
      body = re.sub(subs[0],subs[1],body);
    if config.Get('define_clog2'):
      body = re.sub('@clog2@','clog2',body);
    else:
      body = re.sub('@clog2@','$clog2',body);
    fp.write(body);
