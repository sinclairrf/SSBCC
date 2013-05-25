################################################################################
#
# Copyright 2013, Sinclair R.F., Inc.
#
################################################################################

import math
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class AXI4_Lite_Slave_DualPortRAM(SSBCCperipheral):
  """
  AXI-Lite slave implemented as a dual-port RAM.  The dual-port RAM has at most
  256 bytes addressable by a single 8-bit value.  The data is stored in little
  endian format (i.e., the LSB of the 32-bit word is stored in the lowest
  numbered address).\n
  Usage:
    PERIPHERAL AXI4_Lite_Slave_DualPortRAM              \\
                                basePortName=<name>     \\
                                address=<O_address>     \\
                                read=<I_read>           \\
                                write=<O_write>         \\
                                [size=<N>]\n
  Where:
    basePortName=<name>
      specifies the name used to construct the multiple AXI4-Lite signals
    address=<O_address>
      specifies the symbol used to set the address used for read and write
      operations from and to the dual-port memory
    read=<I_read>
      specifies the symbol used to read from the dual-port memory
    write=<O_write>
      specifies the symbol used to write to the dual-port memory
    size=<N>
      optionally specify the size of the dual-port memory.
      Note:  N must be either a power of 2 in the range from 16 to 256 inclusive
             or it must be a local param with the same restrictions on its
             value.
      Note:  N=256, i.e., the largest memory possible, is the default.
      Note:  Using a localparam for the memory size provides a convenient way
             to use the size of the dual port RAM in the micro controller code.\n
  LEGAL NOTICE:  ARM has restrictions on what kinds of applications can use
  interfaces based on the AXI protocol.  Ensure your application is in
  compliance with their legal restrictions before using this peripheral.
  """

  def __init__(self,peripheralFile,config,param_list,ixLine):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Get the parameters.
    def validateSize(x):
      if re.match(r'L_\w+$',x):
        if not config.IsParameter(x):
          raise SSBCCException('"size=%s" is not a parameter at line %d' % (x,ixLine,));
        ix = [param[0] for param in config.parameters].index(x);
        y = config.parameters[ix][1];
        if not re.match(r'[1-]\d*$', y):
          raise SSBCCException('localparam must be a numeric constant, not "%s", to be used in "size=%s" at line %d' % (y,x,ixLine,));
        y = int(y);
      elif re.match(r'[1-9]\d*$',x):
        y = int(x);
      else:
        raise SSBCCException('Malformed entry for "size=%s" at line %d' % (x,ixLine,));
      if math.modf(math.log(y,2))[0] != 0:
        raise SSBCCException('size=%d must be a power of 2 at line %d' % (y,ixLine,));
      if not (16 <= y <= 256):
        raise SSBCCException('size=%d must be between 16 and 256 inclusive at line %d' % (y,ixLine,));
      return y;
    allowables = (
      ('address',       r'O_\w+$',      None,           ),
      ('basePortName',  r'\w+$',        None,           ),
      ('read',          r'I_\w+$',      None,           ),
      ('size',          r'\S+$',        validateSize,   ),
      ('write',         r'O_\w+$',      None,           ),
    );
    names = [a[0] for a in allowables];
    for param_tuple in param_list:
      param = param_tuple[0];
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at line %d' % (param,ixLine,));
      param_test = allowables[names.index(param)];
      self.AddAttr(config,param,param_tuple[1],param_test[1],ixLine,param_test[2]);
    # Ensure the required parameters are provided.
    for paramname in (
      'address',
      'basePortName',
      'read',
      'write',
    ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at line %d' % (paramname,ixLine,));
    # Set optional parameters.
    for optionalpair in (
        ('size',        256,    ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1]);
    # Set the string used to identify signals associated with this peripheral.
    self.namestring = self.basePortName;
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    for signal in (
      ( 'i_%s_aresetn',         1,                      'input',        ),
      ( 'i_%s_aclk',            1,                      'input',        ),
      ( 'i_%s_awvalid',         1,                      'input',        ),
      ( 'o_%s_awready',         1,                      'output',       ),
      ( 'i_%s_awaddr',          math.log(self.size,2),  'input',        ),
      ( 'i_%s_wvalid',          1,                      'input',        ),
      ( 'o_%s_wready',          1,                      'output',       ),
      ( 'i_%s_wdata',           32,                     'input',        ),
      ( 'i_%s_wstrb',           4,                      'input',        ),
      ( 'o_%s_bresp',           2,                      'output',       ),
      ( 'o_%s_bvalid',          1,                      'output',       ),
      ( 'i_%s_bready',          1,                      'input',        ),
      ( 'i_%s_arvalid',         1,                      'input',        ),
      ( 'o_%s_arready',         1,                      'output',       ),
      ( 'i_%s_araddr',          math.log(self.size,2),  'input',        ),
      ( 'o_%s_rvalid',          1,                      'output',       ),
      ( 'i_%s_rready',          1,                      'input',        ),
      ( 'o_%s_rdata',           32,                     'output',       ),
      ( 'o_%s_rresp',           2,                      'output',       ),
    ):
      thisName = signal[0] % self.basePortName;
      config.AddIO(thisName,signal[1],signal[2],ixLine);
    config.AddSignal('s__%s__mc_addr'  % self.namestring, int(math.log(self.size,2)), ixLine);
    config.AddSignal('s__%s__mc_rdata' % self.namestring, 8, ixLine);
    config.AddSignal('s__%s__mc_wdata' % self.namestring, 8, ixLine);
    config.AddSignal('s__%s__mc_wr'    % self.namestring, 1, ixLine);
    config.AddOutport((self.address,
                      ('s__%s__mc_addr' % self.namestring, int(math.log(self.size,2)), 'data', ),
                      ),ixLine);
    config.AddInport((self.read,
                      ('s__%s__mc_rdata' % self.namestring, 8, 'data', ),
                      ),ixLine);
    config.AddOutport((self.write,
                      ('s__%s__mc_wdata' % self.namestring, 8, 'data', ),
                      ('s__%s__mc_wr'    % self.namestring, 1, 'strobe', ),
                      ),ixLine);
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True;

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v');
    for subpair in (
      (r'\bL__',        'L__@NAME@__',          ),
      (r'\bgen__',      'gen__@NAME@__',        ),
      (r'\bi_a',        'i_@NAME@_a',           ),
      (r'\bi_b',        'i_@NAME@_b',           ),
      (r'\bi_r',        'i_@NAME@_r',           ),
      (r'\bi_w',        'i_@NAME@_w',           ),
      (r'\bix__',       'ix__@NAME@__',         ),
      (r'\bo_',         'o_@NAME@_',            ),
      (r'\bs__',        's__@NAME@__',          ),
      (r'@NAME@',       self.namestring,        ),
      (r'@SIZE@',       str(self.size)          ),
    ):
      body = re.sub(subpair[0],subpair[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
