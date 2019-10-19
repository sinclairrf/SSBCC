################################################################################
#
# Copyright 2013-2014, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

import re

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class big_outport(SSBCCperipheral):
  """
  The documentation is recorded in the file big_outport.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'outport',      r'O_\w+$',              None,   ),
      ( 'outsignal',    r'o_\w+$',              None,   ),
      ( 'width',        r'(9|[1-9]\d+)$',       int,    ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the required parameters are provided (all parameters are required).
    for paramname in names:
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # There are no optional parameters.
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.outsignal,self.width,'output',loc)
    self.ix_outport = config.NOutports()
    config.AddOutport((self.outport,False,
                      # empty list
                      ),
                      loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
        ( r'@IX_OUTPORT@',      "8'h%02x" % self.ix_outport, ),
        ( r'@WIDTH@',           str(self.width), ),
        ( r'@WIDTH-8@',         str(self.width-8), ),
        ( r'@OUTSIGNAL@',       self.outsignal, ),
        ( r'@UC_CLK@',          'i_clk', ),
        ( r'@UC_RST@',          'i_rst', ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
