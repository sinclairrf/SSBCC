################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class PWM_8bit(SSBCCperipheral):
   """Pulse Width Modulator (PWM) with 8-bit control.

This peripheral creates one or more PWMs.  The PWM is designed so that

Usage:
  PERIPHERAL PWM_8bit   outport=O_name \\
                        outsignal=o_name \\
                        ratemethod={clk/rate|count} \\
                        [invert|noinvert] \\
                        [instances=n]

Where:
  outport=O_name
    specifies the symbol used by the outport instruction to write a byte to the
    peripheral
    Note:  The name must start with "O_".
  outsignal=o_name
    specifies the name of the output signal
  ratemethod={clk/rate|count}
    specifies the frequency at which the PWM counter is incremented
    Example:  ratemethod=count means to increment the PWM counter once every
              "count" clock cycles.
  invert|noinvert
    optional configuration command to invert or to not invert the PWM output
    Default:  don't invert the output (i.e., a command of 0 means the output is
              always low)
    Note:  "invert" should be used when pulling the external signal to ground
           means the device is "on"
  instances=n
    specifies the number of PWMs for the peripheral
    Default:  The default is one PWM control and output.

The following OUTPORT is provided by this peripheral when instances=1:
  O_name
    output the next 8-bit value to transmit or to queue for transmission

The following OUTPORT is provided by this peripheral when instances=n is larger
than 1:
  O_name_0, O_name_1, ..., O_name_{n-1}
    If instances=n where n>1, then n outports are created
    Note:  O_name_i = ${O_name_0+i) where 0<=i<n.
    Note:  The PWM for o_name[i] is controlled by the outport O_name_i

Note:  The PWM counter is an 8-bit count that ranges from 1 to 255.  Each PWM
       output is '1' when this count is less than or equal to the commanded
       count.  The signal for a commanded count of 0 will never be on while the
       signal for a commanded count of 255 will always be on.

Example:  Control the intensity of an LED through a PWM.  The LED must flicker
          at a frequency greater than about 30 Hz in order for the flickering to
          not be visible by human eyes.  The LED is turned on when the signal to
          the LED is at ground.  The processor clock frequency is provided by
          the parameter G_CLK_FREQ_HZ.

  Within the processor architecture file include the configuration command:

  PERIPHERAL PWM_8bit   outport=O_PWM_LED \
                        outsignal=o_led \
                        ratemethod=G_CLK_FREQ_HZ/(30*255) \
                        invert

  Use the following assembly to set the LED to about 1/4 intensity:

  0x40 .outport(O_PWM_LED)

Example:  Similarly to obove, but for the three controls of a tri-color LED:

  Within the processor architecture file include the configuration command:

  PERIPHERAL PWM_8bit   outport=O_PWM_LED \
                        outsignal=o_led \
                        ratemethod=G_CLK_FREQ_HZ/(30*255) \
                        invert \
                        instances=3

  Use the following assembly to set the LEDs to 0x10 0x20 and 0x55:

  0x10 .outport(O_PWM_LED_0)
  0x20 .outport(O_PWM_LED_1)
  0x55 .outport(O_PWM_LED_2)

  or use the following function to send the three values on the stack where the
  top of the stack is 0x55 0x20 0x10 (this isn't less code, but it illustrates
  how to increment the outport index):

  ; ( u_pwm_led_2 u_pwm_led_1 u_pwm_led_0 - )
  .function set_led_pwms
  O_PWM_LED_0 ${3-1} :loop r> swap over outport drop 1+ r> .jumpc(loop,1-) drop
  .return(drop)
""";

  def __init__(self,config,param_list,ixLine):
    pass;

  def GenVerilog(self,fp,config):
    pass;
