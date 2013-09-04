################################################################################
#
# Copyright 2013, Sinclair R.F., Inc.
#
################################################################################

import math
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class AXI4_Lite_Master(SSBCCperipheral):
  """
  AXI-Lite master for 32-bit reads and 8, 16, and 32-bit writes.\n
  256 bytes addressable by a single 8-bit value.  The data is stored in little
  endian format (i.e., the LSB of the 32-bit word is stored in the lowest
  numbered address).\n
  Usage:
    PERIPHERAL AXI4_Lite_Master                                 \\
                                basePortName=<name>             \\
                                address=<O_address>             \\
                                data=<O_data>                   \\
                                write_enable=<O_write_enable>   \\
                                command_read=<O_command_read>   \\
                                command_write=<O_command_write> \\
                                busy=<I_busy>                   \\
                                read=<I_read>                   \\
                                address_width=<N>               \\
                                synchronous={True|False}
  Where:
    basePortName=<name>
      specifies the name used to construct the multiple AXI4-Lite signals
    address=<O_address>
      specifies the symbol used to set the address used for read and write
      operations from and to the dual-port memory
      Note:  If the address is 8 bits or less, a single write to this port will
             set the address.  If the address is 9 bits or longer, then multiple
             writes to this address, starting with the MSB of the address, are
             required to set all of the address bits.  See the examples for
             illustrations of how this works.
      Note:  The 2 lsb of the address are ignored.  I.e., all addresses will be
             treated as 32-bit aligned.
    data=<O_data>
      specifies the symbol used to set the 32-bit data for write operations
      Note:  Four outputs to this address are required, starting with the MSB of
             the 32-bit value,  See the examples for illustrations of how this
             works.
    write_enable=<O_write_enable>
      specifies the symbol used to set the 4 write enable bits
    command_read=<O_command_read>
      specifies the symbol used to start the AXI4-Lite master core to issue a
      read and store the received data
    command_write=<O_command_write>
      specifies the symbol used to start the AXI4-Lite master core to issue a
      write
    busy=<I_busy>
      specifies the symbol used to read the busy/not-busy status of the core
      Note:  A non-zero value means the core is busy.
    read=<I_read>
      specifies the symbol used to read successive bytes of the received 32-bit
      value starting with the LSB
    address_width=<N>
      specifies the width of the 8-bit aligned address\n
    synchronous={True|False}
      indicates whether or not he micro controller clock and the AXI4-Lite bus
      are synchronous
  Example:  Xilinx' AXI_DMA core has a 7-bit address range for its register
    address map.  The PERIPHERAL configuration statement to interface to this
    core would be:\n
      PERIPHERAL AXI4_Lite_Master                                       \
                        basePortName=myAxiDmaDevice                     \
                        address=O_myAxiDmaDevice_address                \
                        data=O_myAxiDmaDevice_data                      \
                        write_enable=O_myAxiDmaDevice_wen               \
                        command_read=O_myAxiDmaDevice_cmd_read          \
                        command_write=O_myAxiDmaDevice_cmd_write        \
                        busy=I_myAxiDmaDevice_busy                      \
                        read=I_myAxiDmaDevice_read                      \
                        address_width=7                                 \
                        synchronous=True\n
    To write to the memory master to slave start address, use the
    following, where "start_address" is a 4-byte variable set elsewhere in the
    program:\n
      ; Set the 7-bit register address.
      0x18 .outport(O_myAxiDmaDevice_address)
      ; Read the 4-byte start address from memory.
      .fetchvector(start_address,4)
      ; write the address to the AXI4-Lite master
      ${4-1} :loop_data
        swap .outport(O_myAxiDmaDevice_data)
      .jumpc(loop_data,1-) drop
      ; Ensure all 4 bytes will be written.
      0x0F .outport(O_myAxiDmaDevice_wen)
      ; Issue the write strobe.
      .outstrobe(O_myAxiDmaDevice_cmd_write)
      ; Wait for the write operation to finish.
      :loop_write_wait
        .inport(I_myAxiDmaDevice_busy)
      .jumpc(loop_write_wait)\n
    Alternatively, a function could be defined as follows:\n
      ; Write the specified 32-bit value to the specified 7-bit address.
      ; ( u_LSB u u u_MSB u_addr - )
      .function myAxiDmaDevice_write
        ; Write the 7-bit register address.
        .outport(O_myAxiDmaDevice_address)
        ; Write the 32-bit value, starting with the MSB.
        ${4-1} :loop_data
          swap .outport(O_myAxiDmaDevice_data)
        .jumpc(loop_data,1-) drop
        ; Ensure all 4 bytes will be written.
        0x0F .outport(O_myAxiDmaDevice_wen)
        ; Issue the write strobe.
        .outstrobe(O_myAxiDmaDevice_cmd_write)
        ; Wait for the write operation to finish.
        :loop_write_wait
          .inport(I_myAxiDmaDevice_busy)
        .jumpc(loop_write_wait)
        ; That's all
        .return\n
    And the write could then be performed using the following code:\n
      .constant AXI_DMA_MM2S_Start_Address 0x18
      ...
      ; Write the start address to the AXI DMA.
      .fetchvector(start_address,4)
      .call(myAxiDmaDevice_write,AXI_DMA_MM2S_Start_Address)\n
  Example:  Suppose the AXI4-Lite Master peripheral is connected to a memory
    with a 22-bit address width, i.e., a 4 MB address range.  The PERIPHERAL
    configuration command would be similar to the above except the string
    "myAxiDmaDevice" would need to be changed to the new hardware peripheral and
    the address width would be set using "address_width=22".\n
    The 22-bit address would be set using 3 bytes.  For example, the address
    0x020100 would be set by:\n
      0x00 .outport(O_myAxiMaster_address)
      0x01 .outport(O_myAxiMaster_address)
      0x02 .outport(O_myAxiMaster_address)\n
    The 2 msb of the first, most-significant, address byte will be dropped by
    the shift register receiving the address and the 2 lsb of the last, least
    significant, address byte will be written as zeros to the AXI Lite
    peripheral.\n
  LEGAL NOTICE:  ARM has restrictions on what kinds of applications can use
  interfaces based on their AXI protocol.  Ensure your application is in
  compliance with their restrictions before using this peripheral for an AXI
  interface.
  """

  def __init__(self,peripheralFile,config,param_list,ixLine):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Get the parameters.
    allowables = (
      ('address',       r'O_\w+$',              None,           ),
      ('address_width', r'[1-9]\d*$',           int,            ),
      ('basePortName',  r'\w+$',                None,           ),
      ('command_read',  r'O_\w+$',              None,           ),
      ('command_write', r'O_\w+$',              None,           ),
      ('data',          r'O_\w+$',              None,           ),
      ('read',          r'I_\w+$',              None,           ),
      ('busy',          r'I_\w+$',              None,           ),
      ('synchronous',   r'(True|False)$',       bool,           ),
      ('write_enable',  r'O_\w+$',              None,           ),
    );
    names = [a[0] for a in allowables];
    for param_tuple in param_list:
      param = param_tuple[0];
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at line %d' % (param,ixLine,));
      param_test = allowables[names.index(param)];
      self.AddAttr(config,param,param_tuple[1],param_test[1],ixLine,param_test[2]);
    # Ensure the required parameters are provided (all parameters are required).
    for paramname in names:
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at line %d' % (paramname,ixLine,));
    # There are no optional parameters.
    # Temporary:  Warning message
    if not self.synchronous:
      raise SSBCCException('synchronous=False has not been validated yet');
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    for signal in (
      ( 'i_%s_aresetn',         1,                      'input',        ),
      ( 'i_%s_aclk',            1,                      'input',        ),
      ( 'o_%s_awvalid',         1,                      'output',       ),
      ( 'i_%s_awready',         1,                      'input',        ),
      ( 'o_%s_awaddr',          self.address_width,     'output',       ),
      ( 'o_%s_wvalid',          1,                      'output',       ),
      ( 'i_%s_wready',          1,                      'input',        ),
      ( 'o_%s_wdata',           32,                     'output',       ),
      ( 'o_%s_wstrb',           4,                      'output',       ),
      ( 'i_%s_bresp',           2,                      'input',        ),
      ( 'i_%s_bvalid',          1,                      'input',        ),
      ( 'o_%s_bready',          1,                      'output',       ),
      ( 'o_%s_arvalid',         1,                      'output',       ),
      ( 'i_%s_arready',         1,                      'input',        ),
      ( 'o_%s_araddr',          self.address_width,     'output',       ),
      ( 'i_%s_rvalid',          1,                      'input',        ),
      ( 'o_%s_rready',          1,                      'output',       ),
      ( 'i_%s_rdata',           32,                     'input',        ),
      ( 'i_%s_rresp',           2,                      'input',        ),
    ):
      thisName = signal[0] % self.basePortName;
      config.AddIO(thisName,signal[1],signal[2],ixLine);
    config.AddSignal('s__%s__address' % self.basePortName, self.address_width, ixLine);
    config.AddSignal('s__%s__rd' % self.basePortName, 1, ixLine);
    config.AddSignal('s__%s__wr' % self.basePortName, 1, ixLine);
    config.AddSignal('s__%s__busy' % self.basePortName, 5, ixLine);
    config.AddSignal('s__%s__read' % self.basePortName, 32, ixLine);
    self.ix_address = config.NOutports();
    config.AddOutport((self.address,
                      # empty list -- disable normal output port signal generation
                      ),ixLine);
    self.ix_data = config.NOutports();
    config.AddOutport((self.data,
                      # empty list -- disable normal output port signal generation
                      ),ixLine);
    config.AddOutport((self.write_enable,
                      ('o_%s_wstrb' % self.basePortName, 4, 'data', ),
                      ),ixLine);
    config.AddOutport((self.command_read,
                      ('s__%s__rd' % self.basePortName, 1, 'strobe', ),
                      ),ixLine);
    config.AddOutport((self.command_write,
                      ('s__%s__wr' % self.basePortName, 1, 'strobe', ),
                      ),ixLine);
    config.AddInport((self.busy,
                     ('s__%s__busy' % self.basePortName, 5, 'data', ),
                     ),ixLine);
    self.ix_read = config.NInports();
    config.AddInport((self.read,
                     ('s__%s__read' % self.basePortName, 32, 'data', ),
                     ),ixLine);

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v');
    # avoid i_clk and i_rst
    for subpair in (
      (r'\bgen__',              'gen__@NAME@__',                        ),
      (r'\bL__',                'L__@NAME@__',                          ),
      (r'\bs__',                's__@NAME@__',                          ),
      (r'\bi_a',                'i_@NAME@_a',                           ),
      (r'\bi_b',                'i_@NAME@_b',                           ),
      (r'\bi_rd',               'i_@NAME@_rd',                          ),
      (r'\bi_rr',               'i_@NAME@_rr',                          ),
      (r'\bi_rv',               'i_@NAME@_rv',                          ),
      (r'\bi_w',                'i_@NAME@_w',                           ),
      (r'\bo_',                 'o_@NAME@_',                            ),
      (r'@ADDRESS_WIDTH@',      str(self.address_width),                ),
      (r'@ISSYNC@',             "1'b1" if self.synchronous else "1'b0", ),
      (r'@IX_ADDRESS@',         str(self.ix_address),                   ),
      (r'@IX_DATA@',            str(self.ix_data),                      ),
      (r'@IX_READ@',            str(self.ix_read),                      ),
      (r'@NAME@',               self.basePortName,                      ),
    ):
      body = re.sub(subpair[0],subpair[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
