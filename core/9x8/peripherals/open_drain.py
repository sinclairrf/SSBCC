################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

class open_drain:
  """Implement an open-drain IOB suitable for direct connection to a pin.  This can
be used as an I/O port for an I2C device.

Usage:
  PERIPHERAL open_drain inport=I_name \\
                        outport=O_name \\
                        iosignal=io_name \\
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

Example:  Configure two ports for running an I2C bus:

  PORTCOMMENT I2C bus
  PERIPHERAL open_drain inport=I_SCL outport=O_SCL iosignal=io_scl
  PERIPHERAL open_drain inport=I_SDA outport=O_SDA iosignal=io_sda

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

  def __init__(self,config,param_list,ixLine):
    # Get the parameters.
    self.inport = None;
    self.iosignal = None;
    self.outport = None;
    self.width = None;
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      if param == 'inport':
        if type(self.inport) != type(None):
          raise SSBCCException('inport can only be specified once at line %d' % ixLine);
        if type(param_arg) == type(None):
          raise SSBCCException('inport assignment missing at line %d' % ixLine);
        if not re.match('I_\w+$',param_arg):
          raise SSBCCException('Bad inport symbol at line %d:  "%s"' % (ixLine,param_arg,));
        self.inport = param_arg;
      elif param == 'iosignal':
        if type(self.iosignal) != type(None):
          raise SSBCCException('iosignal can only be specified once at line %d' % ixLine);
        if type(param_arg) == type(None):
          raise SSBCCException('iosignal assignment missing at line %d' % ixLine);
        if not re.match('io_\w+$',param_arg):
          raise SSBCCException('Bad io signal name at line %d:  "%s"' % (ixLine,param_arg,));
        self.iosignal = param_arg;
      elif param == 'outport':
        if type(self.outport) != type(None):
          raise SSBCCException('outport can only be specified once at line %d' % ixLine);
        if type(param_arg) == type(None):
          raise SSBCCException('outport assignment missing at line %d' % ixLine);
        if not re.match('O_\w+$',param_arg):
          raise SSBCCException('Bad outport symbol at line %d:  "%s"' % (ixLine,param_arg,));
        self.outport = param_arg;
      elif param == 'width':
        if type(self.width) != type(None):
          raise SSBCCException('width can only be specified once at line %d' % ixLine);
        if type(param_arg) == type(None):
          raise SSBCCException('width assignment missing at line %d' % ixLine);
        if not re.match('[1-9][0-9]*$',param_arg):
          raise SSBCCException('Bad signal width at line %d:  "%s"' % (ixLine,param_arg,));
        self.width = int(param_arg);
      else:
        raise SSBCCException('Unrecognized parameter at line %d:  "%s"' % (ixLine,param,));
    # Set defaults for non-specified values.
    if type(self.inport) == type(None):
      raise SSBCCException('Missing "inport=I_name" at line %d' % ixLine);
    if type(self.iosignal) == type(None):
      raise SSBCCException('Missing "iosignal=io_name" at line %d' % ixLine);
    if type(self.outport) == type(None):
      raise SSBCCException('Missing "outport=O_name" at line %d' % ixLine);
    if type(self.width) == type(None):
      self.width = 1;
    # Ensure the speicified values are reasonable.
    if (self.width < 1) or (8 < self.width):
      raise SSBCCException('pull-down peripheral width must be between 1 and 8 inclusive');
    # Add the I/O port and OUTPORT and INPORT signals for this peripheral.
    self.sname = 's__' + self.iosignal;
    sname_init = '%d\'b%s' % (self.width, '1'*self.width, );
    config['ios'].append((self.iosignal,self.width,'inout'));
    config['signals'].append((self.sname,self.width,None,));
    config['inports'].append((self.inport,
                             (self.iosignal,self.width,'data',),
                            ));
    config['outports'].append((self.outport,
                              (self.sname,self.width,'data',sname_init,),
                             ));

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    body_1 = """//
// open_drain peripheral for "@NAME@"
//
assign @IO_NAME@ = (@S_NAME@ == 1'b0) ? 1'b0 : 1'bz;
"""
    body_big = """//
// open_drain peripheral for "@NAME@"
//
generate
genvar ix__open_drain__@NAME@;
for (ix__open_drain__@NAME@=0; ix__open_drain__@NAME@<@WIDTH@; ix__open_drain__@NAME@ = ix__open_drain__@NAME@+1) begin : gen_@NAME@
  assign @IO_NAME@[ix__open_drain__@NAME@] = (@S_NAME@[ix__open_drain__@NAME@] == 1'b0) ? 1'b0 : 1'bz;
end
endgenerate
"""
    if self.width == 1:
      body = body_1;
    else:
      body = body_big;
    for subs in (
                  ('@IO_NAME@', self.iosignal,),
                  ('@NAME@',    self.iosignal,),
                  ('@S_NAME@',  self.sname,),
                  ('@WIDTH@',   str(self.width),),
                ):
      body = re.sub(subs[0],subs[1],body);
    fp.write(body);
