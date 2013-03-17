################################################################################
#
# Copyright 2012-2013, Sinclair R.F., Inc.
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class open_drain(SSBCCperipheral):
  """
  Implement an open-drain I/O suitable for direct connection to a pin.  This
  can, for example, be used as an I/O port for an I2C device.

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

  The following OUTPORTs are provided by this peripheral:
    O_name
      this is the new output for the open drain I/O

  The following INPORTs are provided by this peripheral:
    I_name
      this reads the current value of the open drain I/O

  Example:  Configure two 1-bit ports implementing an I2C bus:

    Add the following to the architecture file:

    PORTCOMMENT I2C bus
    PERIPHERAL open_drain inport=I_SCL outport=O_SCL iosignal=io_scl
    PERIPHERAL open_drain inport=I_SDA outport=O_SDA iosignal=io_sda

    The following assembly will transmit the start condition for an I2C bus by
    pulling SDA low and then pulling SCL low.

    ; Set SDA low
    0 .outport(O_SDA)
    ; delay one fourth of a 400 kHz cycle (based on a 100 MHz clock)
    ${int(100.e6/400.e3/3)-1} :delay .jumpc(delay,1-) drop
    ; Set SCL low
    0 .outport(O_SCL)

    See the I2C examples for a complete demonstration of using the open_drain
    peripheral.
  """

  def __init__(self,peripheralFile,config,param_list,ixLine):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Parse the parameters.
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      if param == 'inport':
        self.AddAttr(config,param,param_arg,r'I_\w+$',ixLine);
      elif param == 'iosignal':
        self.AddAttr(config,param,param_arg,r'io_\w+$',ixLine);
      elif param == 'outport':
        self.AddAttr(config,param,param_arg,r'O_\w+$',ixLine);
      elif param == 'width':
        self.AddAttr(config,param,param_arg,r'[1-9]\d*$',ixLine);
        self.width = int(self.width);
      else:
        raise SSBCCException('Unrecognized parameter at line %d:  "%s"' % (ixLine,param,));
    # Ensure the required parameters are set.
    if not hasattr(self,'inport'):
      raise SSBCCException('Missing "inport=I_name" at line %d' % ixLine);
    if not hasattr(self,'iosignal'):
      raise SSBCCException('Missing "iosignal=io_name" at line %d' % ixLine);
    if not hasattr(self,'outport'):
      raise SSBCCException('Missing "outport=O_name" at line %d' % ixLine);
    # Set defaults for non-specified values.
    if not hasattr(self,'width'):
      self.width = 1;
    # Ensure the specified values are reasonable.
    maxWidth = config.Get('data_width');
    if (self.width < 1) or (maxWidth < self.width):
      raise SSBCCException('width must be between 1 and %d inclusive at line %d' % (maxWidth,ixLine,));
    # Create the internal signal name and initialization.
    self.sname = 's__%s' % self.iosignal;
    sname_init = '%d\'b%s' % (self.width, '1'*self.width, );
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.iosignal,self.width,'inout',ixLine);
    config.AddSignalWithInit(self.sname,self.width,None,ixLine);
    config.AddInport((self.inport,
                     (self.iosignal,self.width,'data',),
                    ),
                    ixLine);
    config.AddOutport((self.outport,
                      (self.sname,self.width,'data',sname_init,),
                     ),
                     ixLine);

  def GenVerilog(self,fp,config):
    body_1 = """//
// PERIPHERAL open_drain:  @NAME@
//
assign @IO_NAME@ = (@S_NAME@ == 1'b0) ? 1'b0 : 1'bz;
"""
    body_big = """//
// PERIPHERAL open_drain:  @NAME@
//
generate
genvar ix;
for (ix=0; ix<@WIDTH@; ix = ix+1) begin : gen_@NAME@
  assign @IO_NAME@[ix] = (@S_NAME@[ix] == 1'b0) ? 1'b0 : 1'bz;
end
endgenerate
"""
    if self.width == 1:
      body = body_1;
    else:
      body = body_big;
    for subs in (
                  (r'\bix\b',           'ix__@NAME@',),
                  (r'@IO_NAME@',        self.iosignal,),
                  (r'@NAME@',           self.iosignal,),
                  (r'@S_NAME@',         self.sname,),
                  (r'@WIDTH@',          str(self.width),),
                ):
      body = re.sub(subs[0],subs[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
