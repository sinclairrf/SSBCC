################################################################################
#
# Copyright 2016, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class AXI_Stream_Slave(SSBCCperipheral):
  """
  The documentation is recorded in the file AXI_Stream_Slave.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'basePortName', r'\w+$',                None,           ),
      ( 'data_width',   r'\w+$',                lambda v : self.IntMethod(config,v,lowLimit=8,multipleof=8), ),
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
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
      ( '@NAME@',       self.basePortName, ),
      ( '@WIDTH@',      str(self.data_width), ),
      ( '@IX_LATCH@',   "8'd%d" % self.ix_latch, ),
      ( '@IX_INDATA@',  "8'd%d" % self.ix_indata, ),
      ( '@SHIFT_DATA@', "8'd0" if self.data_width == 8 else "{ 8'd0, s__%s__data[8+:%d] }" % (self.basePortName,self.data_width-8,), ),
      ( r'@UC_CLK@',    'i_clk', ),
      ( r'@UC_RST@',    'i_rst', ),
    ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
