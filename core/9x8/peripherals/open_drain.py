################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

class open_drain:
  """Implement an open-drain IOB suitable for direct connection to a pin.  This can,
for example, be used as an I/O port for an I2C device.

Usage:
  PERIPHERAL open_drain inport=I_name \\
                        outport=O_name \\
                        iosignal=io_name \\
                        [width=n]

Where:
  inport=I_name
    is the inport symbol to read the pin
  outport=O_name
    is the outport symbol to write to the pin
    Note:  A "0" value activates the open drain while a "1" value releases the
    open drain.
  iosignal=io_name
    is the tri-state pin for the open-drain I/O buffer
    Note:  The initial value of the pin is "open."
  width=n
    is the optional width of the port
    Note:  The default is one bit

Example:  Configure two 1-bit ports implementing an I2C bus:

  PORTCOMMENT I2C bus
  PERIPHERAL open_drain inport=I_SCL outport=O_SCL iosignal=io_scl
  PERIPHERAL open_drain inport=I_SDA outport=O_SDA iosignal=io_sda

  Transmit the start condition for an I2C bus by setting SDA low and then
  setting SCL low.

  ; Set SDA low
  0 .outport(O_SDA)
  ; delay one fourth of a 400 kHz cycle (based on a 100 MHz clock)
  ${int(100.e6/400.e3/3)-1} :delay .jumpc(delay,1-) drop
  ; Set SCL low
  0 .outport(O_SCL)

  See the I2C examples for a complete demonstration of using the open_drain
  peripheral.
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
        if self.inport != None:
          raise SSBCCException('inport can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('inport assignment missing at line %d' % ixLine);
        if not re.match('I_\w+$',param_arg):
          raise SSBCCException('Bad inport symbol at line %d:  "%s"' % (ixLine,param_arg,));
        self.inport = param_arg;
      elif param == 'iosignal':
        if self.iosignal != None:
          raise SSBCCException('iosignal can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('iosignal assignment missing at line %d' % ixLine);
        if not re.match('io_\w+$',param_arg):
          raise SSBCCException('Bad io signal name at line %d:  "%s"' % (ixLine,param_arg,));
        self.iosignal = param_arg;
      elif param == 'outport':
        if self.outport != None:
          raise SSBCCException('outport can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('outport assignment missing at line %d' % ixLine);
        if not re.match('O_\w+$',param_arg):
          raise SSBCCException('Bad outport symbol at line %d:  "%s"' % (ixLine,param_arg,));
        self.outport = param_arg;
      elif param == 'width':
        if self.width != None:
          raise SSBCCException('width can only be specified once at line %d' % ixLine);
        if param_arg == None:
          raise SSBCCException('width assignment missing at line %d' % ixLine);
        if not re.match('[1-9][0-9]*$',param_arg):
          raise SSBCCException('Bad signal width at line %d:  "%s"' % (ixLine,param_arg,));
        self.width = int(param_arg);
      else:
        raise SSBCCException('Unrecognized parameter at line %d:  "%s"' % (ixLine,param,));
    # Set defaults for non-specified values.
    if self.inport == None:
      raise SSBCCException('Missing "inport=I_name" at line %d' % ixLine);
    if self.iosignal == None:
      raise SSBCCException('Missing "iosignal=io_name" at line %d' % ixLine);
    if self.outport == None:
      raise SSBCCException('Missing "outport=O_name" at line %d' % ixLine);
    if self.width == None:
      self.width = 1;
    # Ensure the speicified values are reasonable.
    if (self.width < 1) or (8 < self.width):
      raise SSBCCException('pull-down peripheral width must be between 1 and 8 inclusive');
    # Add the I/O port and OUTPORT and INPORT signals for this peripheral.
    self.sname = 's__' + self.iosignal;
    sname_init = '%d\'b%s' % (self.width, '1'*self.width, );
    config.AddIO(self.iosignal,self.width,'inout');
    config.AddSignalWithInit(self.sname,self.width,None);
    config.AddInport((self.inport,
                     (self.iosignal,self.width,'data',),
                    ));
    config.AddOutport((self.outport,
                      (self.sname,self.width,'data',sname_init,),
                     ));

  def GenHDL(self,fp,config):
    if config.Get('hdl') == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config.Get('hdl'));

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
