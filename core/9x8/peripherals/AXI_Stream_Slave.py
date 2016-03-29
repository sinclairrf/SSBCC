################################################################################
#
# Copyright 2016, Sinclair R.F., Inc.
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class AXI_Stream_Slave(SSBCCperipheral):
  """
  Implement an AXI-Stream slave port with an optional TLast signal.\n
  Usage:
    PERIPHERAL AXI_Stream_Slave         basePortName=<name>             \\
                                        instatus=<I_status>             \\
                                        outlatch=<O_latch>              \\
                                        indata=<I_data>                 \\
                                        data_width=<N>                  \\
                                        [noTLast|hasTLast]\n
  where:
    basePortName=<name>
      specifies the name used to construct the multiple AXI-Stream signals
    instatus=<I_status>
      specifies the symbol used to read the status as to whether or not data is
      available on the port
      Note:  Data is available is bit 0x01 is set.  If data is not available
             the byte will be 0x00.
      Note:  If "hasTLast" is specified, bit 0x02 of the status will be the
             value of the TLast signal coincident with the data that will be
             latched by the outlatch strobe.
    outlatch=<O_latch>
      specifies the symbol used for the outport strobe that latches the
      AXI-Stream data so that it can be read by the indata inport symbol
      Note:  This also generates the acknowledgement signal that allows the
             data on the AXI-Stream to advance (which is why the TLast value
             cannot be sampled after this strobe is generated).
    indata=<I_data>
      specifies the symbol used to read the data portion of the AXI-Stream
      latched by the outlatch symbol
      Note:  Data is read LSB first.
    data_width=<N>
      specifies the width of the data portion of the AXI-Stream
      Note:  N must be a power of 2 and it must be at least 8.
    noTLast
      specifies that the incoming AXI-Stream does not have a TLast signal
    hasTLast
      specifies that the incoming AXI-Stream does have a TLast signal\n
  Example:  Receive data from a 32-bit wide AXI-Stream and preserve the value
            of the TLast signal.\n
    PERIPHERAL AXI_Stream_Slave         basePortName=incoming           \\
                                        instatus=I_incoming_status      \\
                                        outlatch=O_latch_incoming       \\
                                        indata=I_incoming_data          \\
                                        data_width=32                   \\
                                        hasTLast\n
    ; Wait for data to arrive on the AXI-Stream.
    ; ( - )
    :loop_wait .inport(I_incoming_status) 0= .jumpc(loop_wait)
    ; Push the status of the TLast signal onto the data stack.
    ; ( - f_tlast )
    .inport(I_incoming_status) 0x02 and 0<>
    ; Latch and read the AXI-Stream data.
    ; ( f_tlast - f_tlast u_LSB ... u_MSB )
    .outstrobe(O_latch_incoming)
    ${4-1} :loop_read >r .inport(I_incoming_data) r> .jumpc(loop_read,1-) drop
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'basePortName', r'\w+$',                None,           ),
      ( 'data_width',   r'\w+$',                lambda v : self.IntPow2Method(config,v,lowLimit=8), ),
      ( 'hasTLast',     None,                   None,           ),
      ( 'indata',       r'I_\w+$',              None,           ),
      ( 'instatus',     r'I_\w+$',              None,           ),
      ( 'noTLast',      None,                   None,           ),
      ( 'outlatch',     r'O_\w+$',              None,           ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the required parameters are provided.
    for paramname in (
        'basePortName',
        'data_width',
        'indata',
        'instatus',
        'outlatch',
      ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
      ( 'noTLast', 'hasTLast', 'noTLast', None, ),
    ):
      if hasattr(self,exclusivepair[0]) and hasattr(self,exclusivepair[1]):
        raise SSBCCException('Only one of "%s" and "%s" can be specified at %s' % (exclusivepair[0],exclusivepair[1],loc,))
      if not hasattr(self,exclusivepair[0]) and not hasattr(self,exclusivepair[1]):
        if exclusivepair[2]:
          setattr(self,exclusivepair[2],exclusivepair[3])
        else:
          raise SSBCCException('One of "%s" or "%s" must be set at %s' % (exclusivepair[0],exclusivepair[1],loc,))
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    for signal in (
      ( '%s_aclk',      1,                      'input',  ),
      ( '%s_aresetn',   1,                      'input',  ),
      ( '%s_tvalid',    1,                      'input',  ),
      ( '%s_tready',    1,                      'output', ),
      ( '%s_tlast',     1,                      'input',  ) if hasattr(self,'hasTLast') else None,
      ( '%s_tdata',     self.data_width,        'input',  ),
    ):
      if not signal:
        continue
      thisName = signal[0] % self.basePortName
      config.AddIO(thisName,signal[1],signal[2],loc)
    config.AddSignal('s__%s__data' % self.basePortName, self.data_width, loc)
    config.AddInport((self.instatus,
                     ( '%s_tlast' % self.basePortName, 1, 'data', ) if hasattr(self,'hasTLast') else None,
                     ( '%s_tvalid' % self.basePortName, 1, 'data', ),
                     ), loc)
    self.ix_latch = config.NOutports()
    config.AddOutport((self.outlatch,True,
                      ), loc)
    self.ix_indata = config.NInports()
    config.AddInport((self.indata,
                     ( 's__%s__data' % self.basePortName, self.data_width, 'data', ),
                     ), loc)

  def GenVerilog(self,fp,config):
    body = """
//
// PERIPHERAL AXI_Stream_Slave:  @NAME@
//
initial @NAME@_tready = 1'b0;
always @ (posedge @NAME@_aclk)
  if (~@NAME@_aresetn)
    @NAME@_tready <= 1'b0;
  else if (s_outport && (s_T == @IX_LATCH@))
    @NAME@_tready <= 1'b1;
  else  if (@NAME@_tvalid && @NAME@_tready)
    @NAME@_tready <= 1'b0;
  else
    @NAME@_tready <= @NAME@_tready;
always @ (posedge @NAME@_aclk)
  if (~@NAME@_aresetn)
    s__@NAME@__data <= @WIDTH@'d0;
  else if (s_outport && (s_T == @IX_LATCH@))
    s__@NAME@__data <= @NAME@_tdata;
  else if (s_inport && (s_T == @IX_INDATA@))
    s__@NAME@__data <= @SHIFT_DATA@;
  else
    s__@NAME@__data <= s__@NAME@__data;
"""[1:]
    for subpair in (
      ( '@NAME@',       self.basePortName, ),
      ( '@WIDTH@',      str(self.data_width), ),
      ( '@IX_LATCH@',   "8'd%d" % self.ix_latch, ),
      ( '@IX_INDATA@',  "8'd%d" % self.ix_indata, ),
      ( '@SHIFT_DATA@', "8'd0" if self.data_width == 8 else "{ 8'd0, s__%s__data[8+:%d] }" % (self.basePortName,self.data_width-8,), ),
    ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
