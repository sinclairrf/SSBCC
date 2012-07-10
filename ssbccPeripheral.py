################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import re

from ssbccUtil import SSBCCException

class SSBCCperipheral:
  """Base class for peripherals"""

  def __init__(self,config,param_list,ixLine):
    pass;

  def AddAttr(self,config,name,value,reformat,ixLine):
    if hasattr(self,name):
      raise SSBCCperipheral('%s repeated at line %d' % (name,ixLine,));
    if value == None:
      raise SSBCCperipheral('%s missing value at line %d' % (name,ixLine,));
    if not re.match(reformat,value):
      raise SSBCCException('Inport symbol at line %d does not match required format "%s":  "%s"' % (ixLine,reformat,value,));
    setattr(self,name,value);

  def GenAssembly(self,config):
    pass;

  def GenHDL(self,fp,config):
    if config.Get('hdl') == 'Verilog':
      self.GenVerilog(fp,config);
    elif config.Get('hdl') == 'VHDL':
      self.GenVHDL(fp,config);
    else:
      raise SSBCCException('HDL "%s" not implemented' % config.Get('hdl'));

  def GenVerilog(self,fp,config):
    raise Exception('Verilog is not implemented for this peripheral');

  def GenVHDL(self,fp,config):
    raise Exception('VHDL is not implemented for this peripheral');
