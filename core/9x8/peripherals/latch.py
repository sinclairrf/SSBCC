################################################################################
#
# Copyright 2012-2013, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

import math
import re

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class latch(SSBCCperipheral):
  """
  The documentation is recorded in the file latch.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    parameters = {
      'inport':         ( r'I_\w+$',      None, ),
      'insignal':       ( r'i_\w+$',      None, ),
      'outport_addr':   ( r'O_\w+$',      None, ),
      'outport_latch':  ( r'O_\w+$',      None, ),
      'width':          ( r'[1-9]\d*$',   lambda v : self.IntMethod(config,v,lowLimit=9), ),
    }
    for param_tuple in param_list:
      param_name, param_value = param_tuple
      try:
        name_test, value_test = parameters[param_name]
      except KeyError:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param_name,loc,))
      self.AddAttr(config,param_name,param_value,name_test,loc,value_test)
    # Ensure the required parameters are set.
    for param_name in parameters:
      if not hasattr(self,param_name):
        raise SSBCCException('Required parameter "%s" not provided at %s', (param_name,loc,))
    # Derived parameters
    self.latch_width = 8*((self.width+7)/8)
    self.addr_width = int(math.ceil(math.log(self.latch_width/8,2)))
    # Configure the processor I/Os, etc.
    config.AddIO(self.insignal,self.width,'input',loc)
    config.AddSignal('s__%s__select' % self.insignal,8,loc)
    config.AddInport((self.inport,
                     ('s__%s__select' % self.insignal,8,'data',),
                    ),loc)
    self.ix__o_latch = config.NOutports()
    config.AddOutport((self.outport_latch,True,),loc)
    self.ix__o_addr = config.NOutports()
    config.AddOutport((self.outport_addr,False,),loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
        ( r'\bix\b',           'ix__@INSIGNAL@', ),
        ( r'\bs__',            's__@INSIGNAL@__', ),
        ( r'@ADDR_WIDTH@',      str(self.addr_width), ),
        ( r'@ADDR_WIDTH-1@',    str(self.addr_width-1), ),
        ( r'@IX_O_ADDR@',       "8'h%02x" % self.ix__o_addr, ),
        ( r'@IX_O_LATCH@',      "8'h%02x" % self.ix__o_latch, ),
        ( r'@LATCH_WIDTH@',     str(self.latch_width), ),
        ( r'@LATCH_WIDTH-1@',   str(self.latch_width-1), ),
        ( r'@LATCH_WIDTH/8@',   str(self.latch_width/8), ),
        ( r'@INSIGNAL@',        self.insignal, ),
        ( r'@WIDTH@',           str(self.width), ),
        ( r'@UC_CLK@',          'i_clk', ),
        ( r'@UC_RST@',          'i_rst', ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
