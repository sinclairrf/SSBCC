################################################################################
#
# Copyright 2013-2014, 2018, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

import math
import re

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class AXI4_Lite_Slave_DualPortRAM(SSBCCperipheral):
  """
  The documentation is recorded in the file AXI4_Lite_Slave_DualPortRAM.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'address',              r'O_\w+$',      None,           ),
      ( 'basePortName',         r'\w+$',        None,           ),
      ( 'ram8',                 None,           None,           ),
      ( 'ram32',                None,           None,           ),
      ( 'read',                 r'I_\w+$',      None,           ),
      ( 'address_width',        r'\S+$',        lambda v : self.IntMethod(config,v,lowLimit=4), ),
      ( 'write',                r'O_\w+$',      None,           ),
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
      'address',
      'basePortName',
      'read',
      'write',
    ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Set optional parameters.
    for optionalpair in (
        ('address_width',       8,    ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1])
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
        ('ram8','ram32','ram8',True,),
      ):
      if hasattr(self,exclusivepair[0]) and hasattr(self,exclusivepair[1]):
        raise SSBCCException('Only one of "%s" and "%s" can be specified at %s' % (exclusivepair[0],exclusivepair[1],loc,))
      if not hasattr(self,exclusivepair[0]) and not hasattr(self,exclusivepair[1]):
        setattr(self,exclusivepair[2],exclusivepair[3])
    # Set the string used to identify signals associated with this peripheral.
    self.namestring = self.basePortName
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    for signal in (
        ( '%s_aresetn',         1,                      'input',        ),
        ( '%s_aclk',            1,                      'input',        ),
        ( '%s_awvalid',         1,                      'input',        ),
        ( '%s_awready',         1,                      'output',       ),
        ( '%s_awaddr',          self.address_width,     'input',        ),
        ( '%s_wvalid',          1,                      'input',        ),
        ( '%s_wready',          1,                      'output',       ),
        ( '%s_wdata',           32,                     'input',        ),
        ( '%s_wstrb',           4,                      'input',        ),
        ( '%s_bvalid',          1,                      'output',       ),
        ( '%s_bready',          1,                      'input',        ),
        ( '%s_bresp',           2,                      'output',       ),
        ( '%s_arvalid',         1,                      'input',        ),
        ( '%s_arready',         1,                      'output',       ),
        ( '%s_araddr',          self.address_width,     'input',        ),
        ( '%s_rvalid',          1,                      'output',       ),
        ( '%s_rready',          1,                      'input',        ),
        ( '%s_rdata',           32,                     'output',       ),
        ( '%s_rresp',           2,                      'output',       ),
      ):
      thisName = signal[0] % self.basePortName
      config.AddIO(thisName,signal[1],signal[2],loc)
    config.AddSignal('s__%s__mc_rdata' % self.namestring, 8, loc)
    self.ix_address = config.NOutports();
    config.AddOutport((self.address,False,
                      # empty list
                      ),loc)
    config.AddInport((self.read,
                      ('s__%s__mc_rdata' % self.namestring, 8, 'data', ),
                      ),loc)
    self.ix_write = config.NOutports()
    config.AddOutport((self.write,False,
                      # empty list
                      ),loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if self.address_width <= 8:
      body = re.sub(r' *@ADDR_NARROW_BEGIN@','',body)
      body = re.sub(r' *@ADDR_NARROW_ELSE@.*?@ADDR_NARROW_END@','',body,flags=re.DOTALL)
    else:
      body = re.sub(r' *@ADDR_NARROW_BEGIN@.*@ADDR_NARROW_ELSE@','',body,flags=re.DOTALL)
      body = re.sub(r' *@ADDR_NARROW_END@','',body)
    if hasattr(self,'ram8'):
      body = re.sub(r'@RAM8_BEGIN@','',body)
      body = re.sub(r'@RAM8_END@','',body)
      body = re.sub(r'@RAM32_BEGIN@.*?@RAM32_END@','',body,flags=re.DOTALL)
    if hasattr(self,'ram32'):
      body = re.sub(r'@RAM8_BEGIN@.*?@RAM8_END@','',body,flags=re.DOTALL)
      body = re.sub(r'@RAM32_BEGIN@','',body)
      body = re.sub(r'@RAM32_END@','',body)
    for subpair in (
        ( r'\bL__',             'L__@NAME@__',                          ),
        ( r'\bgen__',           'gen__@NAME@__',                        ),
        ( r'\bi_',              '@NAME@_',                              ),
        ( r'\bix__',            'ix__@NAME@__',                         ),
        ( r'\bo_',              '@NAME@_',                              ),
        ( r'\bs__',             's__@NAME@__',                          ),
        ( r'@ADDRESS_WIDTH@',   str(self.address_width),                ),
        ( r'@IX_ADDRESS@',      "8'h%02x" % self.ix_address,            ),
        ( r'@IX_WRITE@',        "8'h%02x" % self.ix_write,              ),
        ( r'@NAME@',            self.namestring,                        ),
        ( r'@SIZE@',            str(2**self.address_width),             ),
        ( r'@UC_CLK@',          'i_clk',                                ),
        ( r'@UC_RST@',          'i_rst',                                ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
