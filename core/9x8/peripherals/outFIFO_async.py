################################################################################
#
# Copyright 2013-2014, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import CeilLog2, \
                      SSBCCException

class outFIFO_async(SSBCCperipheral):
  """
  The documentation is recorded in the file outFIFO_async.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ('outclk',        r'i_\w+$',      None,   ),
      ('data',          r'o_\w+$',      None,   ),
      ('data_rd',       r'i_\w+$',      None,   ),
      ('data_empty',    r'o_\w+$',      None,   ),
      ('outport',       r'O_\w+$',      None,   ),
      ('infull',        r'I_\w+$',      None,   ),
      ('depth',         r'[1-9]\d*$',   lambda v : self.IntPow2Method(config,v,lowLimit=16),    ),
      ('outempty',      r'I_\w+$',      None,   ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the required parameters are provided.
    for paramname in names:
      if paramname in ('outempty',):
        continue
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.outclk,1,'input',loc)
    config.AddIO(self.data,8,'output',loc)
    config.AddIO(self.data_rd,1,'input',loc)
    config.AddIO(self.data_empty,1,'output',loc)
    config.AddSignal('s__%s__full' % self.data,1,loc)
    self.ix_outport = config.NOutports()
    config.AddOutport((self.outport,False,
                      # empty list
                      ),loc)
    config.AddInport((self.infull,
                     ('s__%s__full' % self.data,1,'data',),
                    ),loc)

    if hasattr(self,'outempty'):
      self.outempty_name = 's__%s__outempty_in' % self.data
      config.AddSignalWithInit(self.outempty_name,1,'1\'b1',loc)
      self.ix_outempty = config.NInports()
      config.AddInport((self.outempty,
                       (self.outempty_name,1,'data',),
                      ),loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if hasattr(self,'outempty'):
      body = re.sub(r'@OUTEMPTY_BEGIN@','',body)
      body = re.sub(r'@OUTEMPTY_END@','',body)
    else:
      body = re.sub(r'@OUTEMPTY_BEGIN@.*?@OUTEMPTY_END@','',body,flags=re.DOTALL)
    for subpair in (
      ( r'\bgen__',             'gen__@NAME@__' ),
      ( r'\bix__',              'ix__@NAME@__' ),
      ( r'\bs__',               's__@NAME@__' ),
      ( r'@DATA@',              self.data, ),
      ( r'@DATA_EMPTY@',        self.data_empty, ),
      ( r'@DATA_RD@',           self.data_rd, ),
      ( r'@DEPTH@',             str(self.depth), ),
      ( r'@DEPTH-1@',           str(self.depth-1), ),
      ( r'@DEPTH_NBITS@',       str(CeilLog2(self.depth)), ),
      ( r'@DEPTH_NBITS-1@',     str(CeilLog2(self.depth)-1), ),
      ( r'@IX_OUTPORT@',        str(self.ix_outport), ),
      ( r'@OUTCLK@',            self.outclk, ),
      ( r'@NAME@',              self.data, ),
      ( r'@UC_CLK@',            'i_clk', ),
      ( r'@UC_RST@',            'i_rst', ),
    ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
