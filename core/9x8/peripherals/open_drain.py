################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

class open_drain:
  """Implement an open-drain IOB suitable for direct connection to a pin.  This can
be used as an I/O port for an I2C device.

Usage:
  PERIPHERAL open_drain name \\
             [width=n]

Where:
  name
    is the base name to be used for the peripheral.
  width=n
    is the optional width of the port
    Note:  The default is one bit

The following OUTPORTs are provided by this module:
  O_name
    write the specified bit(s) to the open-drain I/O port
    Note:  A "0" value activates the open drain while a "1" value releases the
    open drain.

The following INPORTs are provided by this module:
  I_name
    read the value of the tri-state I/O port

The following I/Os are provided for the processor:
  io_name
    this is the tri-state signal implementing the open-drain I/O buffer

Example:  Configure two ports for running I2C peripherals:

  PORTCOMMENT I2C bus
  PERIPHERAL open_drain SCL
  PERIPHERAL open_drain SDA

Example:  Transmit a device address to an I2C peripheral and wait for the
          acknowlegement.  The function "i2c_quarter_cycle" should cause a
          quarter-I2C-clock cycle delay.

  ; set the start condition
  0 .outport(O_SDA) .call(i2c_quarter_cycle) 0 .outport(O_SCL) .call(i2c_quarter_cycle)
  ; transmit the byte, msb first
  $(8-1) :loop
    ; send the next bit of the address
    swap <<msb O_SDA outport swap
    ; send the four quarter phases of the clock, i.e., the sequence 0110
    0x7 $(4-1) :scl swap O_SCL outport 0>> swap .call(i2c_quarter_cycle) .jumpc(scl,1-) drop
  .jumpc(loop,1-) drop
  ; Get the acknowledge status and leave it on the stack
  1 .outport(O_SDA) .call(i2c_quarter_cycle)
  1 .outport(O_SCL) .call(i2c_quarter_cycle)
  .inport(I_SDA)
  .call(i2c_quarter_cycle)
  0 .outport(O_SCL) .call(i2c_quarter_cycle)
"""

  def __init__(self,config,param_list):
    # Extract the required parameters.
    if len(param_list) < 1:
      print __doc__;
      raise SSBCCException('Peripheral name missing');
    self.name = param_list[0][0];
    # Get the optional parameters.
    self.width = None;
    for param_tuple in param_list[1:]:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      if param == 'width':
        self.width = int(param_arg);
      else:
        raise SSBCCException('Unrecognized optional parameter:  "%s"' % param);
    # Set defaults for non-specified values.
    if type(self.width) == type(None):
      self.width = 1;
    # Ensure the speicified values are reasonable.
    if (self.width < 1) or (8 < self.width):
      raise SSBCCException('pull-down peripheral width must be between 1 and 8 inclusive');
    # Add the I/O port and OUTPORT and INPORT signals for this peripheral.
    config['ios'].append(('io_'+self.name,self.width,'inout'));
    config['signals'].append(('s_'+self.name,self.width,));
    config['inports'].append(('I_'+self.name,
                             ('io_'+self.name,1,'data',),
                            ));
    config['outports'].append(('O_'+self.name,
                              ('s_'+self.name,1,'data','1\'b1'),
                             ));

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    body_1 = """//
// open_drain "@NAME@" peripheral
//
assign io_@NAME@ = (s_@NAME@ == 1'b0) ? 1'b0 : 1'bz;
"""
    body_big = """//
// open_drain "@NAME@" peripheral
//
generate
genvar ix__open_drain__@NAME@;
for (ix__open_drain__@NAME@=0; ix__open_drain__@NAME@<@WIDTH@; ix__open_drain__@NAME@ = ix__open_drain__@NAME@+1) begin : gen_@NAME@
  assign io_@NAME@[ix__open_drain__@NAME@] = (s_@NAME@[ix__open_drain__@NAME@] == 1'b0) ? 1'b0 : 1'bz;
end
endgenerate
"""
    if self.width == 1:
      body = body_1;
    else:
      body = body_big;
    for subs in (
                  ('@NAME@',    self.name),
                  ('@WIDTH@',   str(self.width)),
                ):
      body = re.sub(subs[0],subs[1],body);
    fp.write(body);
