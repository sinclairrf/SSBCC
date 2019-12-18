################################################################################
#
# Copyright 2013-2014, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import CeilLog2, \
                      SSBCCException

class inFIFO_async(SSBCCperipheral):
  """
  The documentation is recorded in the file inFIFO_async.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'inclk',        r'i_\w+$',      None,   ),
      ( 'data',         r'i_\w+$',      None,   ),
      ( 'data_wr',      r'i_\w+$',      None,   ),
      ( 'data_full',    r'o_\w+$',      None,   ),
      ( 'inport',       r'I_\w+$',      None,   ),
      ( 'inempty',      r'I_\w+$',      None,   ),
      ( 'depth',        r'[1-9]\d*$',   lambda v : self.IntPow2Method(config,v,lowLimit=16), ),
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
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.inclk,1,'input',loc)
    config.AddIO(self.data,8,'input',loc)
    config.AddIO(self.data_wr,1,'input',loc)
    config.AddIO(self.data_full,1,'output',loc)
    config.AddSignal('s__%s__data' % self.data,8,loc)
    config.AddSignal('s__%s__empty' % self.data,1,loc)
    self.ix_data = config.NInports()
    config.AddInport((self.inport,
                     ('s__%s__data' % self.data,8,'data',),
                    ),loc)
    config.AddInport((self.inempty,
                     ('s__%s__empty' % self.data,1,'data',),
                    ),loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
      ( r'\bgen__',           'gen__@NAME@__' ),
      ( r'\bix__',            'ix__@NAME@__' ),
      ( r'\bs__',             's__@NAME@__' ),
      ( r'@DATA@',            self.data, ),
      ( r'@DATA_FULL@',       self.data_full, ),
      ( r'@DATA_WR@',         self.data_wr, ),
      ( r'@DEPTH-1@',         str(self.depth-1), ),
      ( r'@DEPTH_NBITS@',     str(CeilLog2(self.depth)), ),
      ( r'@DEPTH_NBITS-1@',   str(CeilLog2(self.depth)-1), ),
      ( r'@INCLK@',           self.inclk, ),
      ( r'@IX_DATA@',         str(self.ix_data), ),
      ( r'@NAME@',            self.data, ),
      ( r'@UC_CLK@',          'i_clk', ),
      ( r'@UC_RST@',          'i_rst', ),
    ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
