################################################################################
#
# Copyright 2012-2014, Sinclair R.F., Inc.
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class PWM_8bit(SSBCCperipheral):
  """
  Pulse Width Modulator (PWM) with 8-bit control.\n
  This peripheral creates one or more PWMs.  The PWM is designed so that it is
  allways off when the control is 0 and it is always on when the control is
  0xFF.\n
  Usage:
    PERIPHERAL PWM_8bit   outport=O_name \\
                          outsignal=o_name \\
                          ratemethod={clk/rate|count} \\
                          [invert|noinvert] \\
                          [instances=n] \\
                          [norunt]\n
  Where:
    outport=O_name
      specifies the symbol used by the outport instruction to write a byte to
      the peripheral
      Note:  The name must start with "O_".
    outsignal=o_name
      specifies the name of the output signal
      Note:  The name must start with "o_".
    ratemethod={clk/rate|count}
      specifies the number of clock cycles per PWM count increment
      Note:  "clk," "rate," and "count" can be integers or can be declared by
             CONSTANT, LOCALPARARM, or PARAMETER configuration commands.
      Example:  ratemethod=count means to increment the PWM counter once every
                "count" clock cycles.
      Example:  ratemethod=G_CLK_HZ/1_000 means to use the parameter G_CLK_HZ
                (set elsewhere) and a 1,000 Hz update rate to determine the
                number of clock cycles between updates.
    invert|noinvert
      optional configuration command to invert or to not invert the PWM output
      Default:  don't invert the output (i.e., a command of 0 means the output is
                always low)
      Note:  "invert" should be used when pulling the external signal to ground
             means the device is "on"
    instances=n
      specifies the number of PWMs for the peripheral
      Default:  The default is one PWM control and output.
    norunt
      optionally add logic to ensure "runt" pulses are not generated by
      incorporating new PWM commands at the start of the counting cycle
      Default:  "runt" pulses are allowed.\n
  The following OUTPORT is provided by this peripheral when instances=1:
    O_name
      output the next 8-bit value to transmit or to queue for transmission\n
  The following OUTPORT is provided by this peripheral when instances=n is larger
  than 1:
    O_name_0, O_name_1, ..., O_name_{n-1}
      output the next 8-bit value to transmit on the specified PWM
      Note:  O_name_i = ${O_name_0+i) where 0<=i<n.
      Note:  The PWM for o_name[i] is controlled by the outport O_name_i
      Example:  If "instances=3" is specified, then the following outports are
                provided:  O_name_0, O_name_1, and O_name_2.  The assembly
                sequence "5 .outport(O_name_1)" will change the PWM control for
                the second of these three PWMs to 5.\n
  Note:  The PWM counter is an 8-bit count that ranges from 1 to 255.  Each PWM
         output is '1' when this count is less than or equal to the commanded
         count.  The signal for a commanded count of 0 will never be on while
         the signal for a commanded count of 255 will always be on.\n
  Example:  Control the intensity of an LED through a PWM.  The LED must flicker
            at a frequency greater than about 30 Hz in order for the flickering
            to not be visible by human eyes.  The LED is turned on when the
            signal to the LED is at ground.  The processor clock frequency is
            provided by the parameter G_CLK_FREQ_HZ.\n
    Within the processor architecture file include the configuration command:\n
    CONSTANT   C_PWM_LED_HZ 30*255
    PERIPHERAL PWM_8bit   outport=O_PWM_LED                     \\
                          outsignal=o_led                       \\
                          ratemethod=G_CLK_FREQ_HZ/C_PWM_LED_HZ \\
                          invert\n
    Use the following assembly to set the LED to about 1/4 intensity:\n
    0x40 .outport(O_PWM_LED)\n
  Example:  Similarly to obove, but for the three controls of a tri-color LED:\n
    Within the processor architecture file include the configuration command:\n
    CONSTANT   C_PWM_LED_HZ 30*255
    PERIPHERAL PWM_8bit   outport=O_PWM_LED                     \\
                          outsignal=o_led                       \\
                          ratemethod=G_CLK_FREQ_HZ/C_PWM_LED_HZ \\
                          invert                                \\
                          instances=3\n
    Use the following assembly to set the LED intensities to 0x10 0x20 and 0x55:\n
    0x10 .outport(O_PWM_LED_0)
    0x20 .outport(O_PWM_LED_1)
    0x55 .outport(O_PWM_LED_2)\n
    or use the following function to send the three values on the stack where
    the top of the stack is 0x55 0x20 0x10 (this isn't less code, but it
    illustrates how to increment the outport index):\n
    ; ( u_pwm_led_2 u_pwm_led_1 u_pwm_led_0 - )
    .function set_pwm_led
      O_PWM_LED_0 ${3-1} :loop r> swap over outport drop 1+ r> .jumpc(loop,1-) drop
    .return(drop)
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Get the parameters.
    allowables = (
      ( 'outport',      r'O_\w+$',      None,   ),
      ( 'outsignal',    r'o_\w+$',      None,   ),
      ( 'ratemethod',   r'\S+$',        lambda v : self.RateMethod(config,v), ),
      ( 'invert',       None,           True,   ),
      ( 'noinvert',     None,           True,   ),
      ( 'instances',    r'[1-9]\d*$',   int,    ),
      ( 'norunt',       None,           True,   ),
    );
    names = [a[0] for a in allowables];
    for param_tuple in param_list:
      param = param_tuple[0];
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,));
      param_test = allowables[names.index(param)];
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2]);
    # Ensure the required parameters are provided.
    for paramname in (
        'outport',
        'outsignal',
        'ratemethod',
      ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,));
    # Set optional parameters.
    for optionalpair in (
        ( 'instances',  1,      ),
        ( 'norunt',     False,  ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1]);
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
        ( 'invert',     'noinvert',     'noinvert',     True,   ),
      ):
      if hasattr(self,exclusivepair[0]) and hasattr(self,exclusivepair[1]):
        raise SSBCCException('Only one of "%s" and "%s" can be specified at %s' % (exclusivepair[0],exclusivepair[1],loc,));
      if not hasattr(self,exclusivepair[0]) and not hasattr(self,exclusivepair[1]) and exclusivepair[2]:
        setattr(self,exclusivepair[2],exclusivepair[3]);
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.outsignal,self.instances,'output',loc);
    self.ix_outport_0 = config.NOutports();
    if self.instances == 1:
      tmpOutport = self.outport;
      config.AddOutport((tmpOutport,False,),loc);
    else:
      for ixOutPort in range(self.instances):
        tmpOutport = '%s_%d' % (self.outport,ixOutPort,);
        config.AddOutport((tmpOutport,False,),loc);
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True;

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v');
    output_on = "1'b1";
    output_off = "1'b0";
    if hasattr(self,'invert'):
      output_on = "1'b0";
      output_off = "1'b1";
    for subpair in (
        ( r'\bL__',             'L__@NAME@__',          ),
        ( r'\bgen__',           'gen__@NAME@__',        ),
        ( r'\bs__',             's__@NAME@__',          ),
        ( r'\bix\b',            'ix__@NAME@',           ),
        ( r'@COUNT@',           self.ratemethod,        ),
        ( r'@INSTANCES@',       str(self.instances),    ),
        ( r'@IX_OUTPORT_0@',    str(self.ix_outport_0), ),
        ( r'@OFF@',             output_off,             ),
        ( r'@ON@',              output_on,              ),
        ( r'@NAME@',            self.outsignal,         ),
        ( r'@NORUNT@',          '1\'b1' if self.norunt else '1\'b0', ),
      ):
      body = re.sub(subpair[0],subpair[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
