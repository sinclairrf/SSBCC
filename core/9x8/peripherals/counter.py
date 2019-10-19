################################################################################
#
# Copyright 2013-2014, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

import re

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class counter(SSBCCperipheral):
  """
  The documentation is recorded in the file big_inport.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'outlatch',     r'O_\w+$',              None,   ),
      ( 'inport',       r'I_\w+$',              None,   ),
      ( 'insignal',     r'i_\w+$',              None,   ),
      ( 'width',        r'(9|[1-9]\d*)$',       int,    ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the optional width is set.
    if not hasattr(self,'width'):
      self.width=8
    # Ensure the required parameters are provided.
    required = ['inport','insignal',]
    if self.width > 8:
      required.append('outlatch')
    for paramname in required:
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # There are no optional parameters.
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.insignal,1,'input',loc)
    config.AddSignal('s__%s__counter' % self.insignal, self.width, loc)
    self.ix_inport = config.NInports()
    config.AddInport((self.inport,
                      ('s__%s__counter' % self.insignal, self.width, 'data', ),
                      ),loc)
    self.ix_latch = config.NOutports()
    if hasattr(self,'outlatch'):
      config.AddOutport((self.outlatch,True,
                        # empty list
                        ),loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if self.width <= 8:
      body = re.sub(r'@NARROW_BEGIN@','',body)
      body = re.sub(r'@NARROW_END@','',body)
      body = re.sub(r'@WIDE_BEGIN@.*?@WIDE_END@','',body,flags=re.DOTALL)
    else:
      body = re.sub(r'@NARROW_BEGIN@.*?@NARROW_END@','',body,flags=re.DOTALL)
      body = re.sub(r'@WIDE_BEGIN@','',body)
      body = re.sub(r'@WIDE_END@','',body)
    for subpair in (
        ( r'\bs__',       's__@NAME@__', ),
        ( r'@IX_LATCH@',  "8'h%02x" % self.ix_latch, ),
        ( r'@IX_INPORT@', "8'h%02x" % self.ix_inport, ),
        ( r'@WIDTH@',     str(self.width), ),
        ( r'@WIDTH-1@',   str(self.width-1), ),
        ( r'@WIDTH-8@',   str(self.width-8), ),
        ( r'@NAME@',      '@INSIGNAL@', ),
        ( r'@INSIGNAL@',  self.insignal, ),
        ( r'@UC_CLK@',    'i_clk', ),
        ( r'@UC_RST@',    'i_rst', ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
