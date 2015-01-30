################################################################################
#
# Copyright 2015, Sinclair R.F., Inc.
#
################################################################################

import math

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import CeilLog2
from ssbccUtil import SSBCCException

class stepper_motor(SSBCCperipheral):
  """
  Stepper motor driver\n
  This peripheral creates pulses to driver a stepper motor driver such as TI's
  DRV8825.  It includes a buffer which can be used to store acceleration,
  motion, and deceleration profiles and returns a "completed" status to the
  micro controller.\n
  The core runs accumulators for the angle and the rate.  I.e. the rate is an
  accumulated sum of the initial rate and the commanded acceleration and the
  angle is an accumulation of this possibly changing rate.  The direction signal
  to the stepper motor is the sign bit from the accumulated rate.  The "step"
  signal to the stepper motor driver is strobed every time the accumulated angle
  overflows or underflows and the direction bit to the driver is set according
  to whether the accumulated angle overflowed or underflowed.\n
  The motor control word consists of the following signals:
    initial rate
    acceleration
    number of steps to be performed this control word
    optional mode specification
  These control words are individually packed into one or more 8-bit bytes.  The
  8-bit values from the micro controller are shifted into a buffer from which
  the control word is constructed.  This completed control word is then shifted
  into a FIFO.  The control words in the FIFO are then used to generate the
  timing for the step strobes to the stepper motor driver.  When the FIFO
  empties, the rate and the acceleration are set to zero and the mode retains
  its most recent value.  The user must ensure they do not overfill the FIFO --
  the only FIFO status is an "empty" or control words "done" status.\n
  Usage:
    PERIPHERAL stepper_motor    basename=name                           \\
                                outcontrol=O_name                       \\
                                outrecord=O_name                        \\
                                outrun=O_name                           \\
                                indone=I_name                           \\
                                inerror=I_name                          \\
                                ratemethod={CLK_FREQ_HZ/RATE_HZ|count}  \\
                                rateres=N_rate                          \\
                                accelscale=N_accel_scale                \\
                                accelres=N_accel                        \\
                                countwidth=N_count                      \\
                                [modewidth=N_mode]                      \\
                                [FIFO=N_fifo]\n
  Where:
    basename=name
      specifies the name used to contruct the I/O signals
      Note:  The name must start with an alphabetic character.
      Example:  "basename=stepper" results in the names "o_stepper_dir",
                "o_stepper_step", and "o_stepper_mode" for the output
                direction, step, and optional mode signals and
                "i_stepper_error" for the input error signal.
    outcontrol=O_name
      specifies the port used to assemble 8-bit control values into the stepper
      motor control word
      Note:  The name must start with "O_".
    outrecord=O_name
      specifies the port used to generate the strobe that pushes the assembled
      motor control word into the stepper motor FIFO
      Note:  The name must start with "O_".
    outrun=O_name
      specified the port used to begin the sequence of operations specified by
      the motor control words in the buffer
      Note:  The name must start with "O_".
    indone=I_name
      specifies the port used to determine whether or not the operations in the
      FIFO have finished
      Note:  The name must start with "I_".
    inerror=I_name
      specifies the port used to read the error status from the stepper motor
      controller
      Note:  The name must start with "I_".
    ratemethod
      specified the method to generate the internal clock rate from the
      processor clock
      1st method:  CLK_FREQ_HZ/RATE_HZ
        CLK_FREQ_HZ is the frequency of "i_clk" in Hz
          a number will be interpreted as the clock frequency in Hz
          a symbol will be interpreted as a constant or a parameter
            Note:  the symbol must be declared with the CONSTANT, LOCALPARARM,
                   or PARAMETER configuration command.
        RATE_HZ is the desired internal clock rate
          this is specified as per "CLK_FREQ_HZ"
      2nd method:  count
        specify the number of "i_clk" clock cycles per internal clock cycle
      Note:  CLK_FREQ_HZ, RATE_HZ, and count can be parameters or constants.  For example,
             the following uses the parameter C_CLK_FREQ_HZ for the clock
             frequency and an internal rate to 500 kHz:
             "ratemethod=C_CLK_FREQ_HZ/500_000".
      Note:  The minimum value of "ratemethod" is 2.
    rateres=N_rate
      specifies the resolution of the rate
      Note:  See the 'r' parameter in the "Theory of Operation" section.
    accelscale=N_accel_scale
      specifies the scaling for the most significant bit of the acceleration
      Note:  See the 'a' parameter in the "Theory of Operation" section.
    accelres=N_accel
      specifies the resolution for the acceleration
      Note:  See the 'b' parameter in the "Theory of Operation" section.
    countwidth=N_count
      specifies the width of the counter for the number of steps to be performed
      by the control word
    modewidth=N_mode
      - if not specified, there is no mode signal to the stepper motor
        controller
      - if specified then this specifies the width of the signal to the stepper
        motor controller
    FIFO=N_fifo
      optionally specify the depth of the control word FIFO
      Note:  This must be a power of 2 and must be at least 16.
      Note:  The default is 16.\n
  Theory of Operation:
    Define the following:
      n         is the number of internal clock cycles since the control word
                started being performed (i.e., these are counted after the dlock
                rate is reduced by ratemethod)
      F         is the internal clock cycle frequency (i.e., RATE_HZ in the
                second form for specifying the ratemethod
      R_0       is the initial rate command
      R_n       is the accumulated rate after n internal clock cycles
      A         is the commanded acceleration
      S_n       is the accumulated step after n internal clock cycles
    Then
      R_n = R_0 + A * n
      S_n = R_0 * n + A * n * (n-1) / 2
    The rate R_n can be thought of as a signed fraction with the format "s0.r"
    where 's' represents the sign bit, there are no bits to the left of the
    decimal, and there are 'r' bits to the right of the decimal.  Then the rate
    can be as high as F and as low as F/2^r.  Practically, the maximum rate
    cannot exceed half the internal clock frequency, otherwise the "step"
    signals will merge together and the stepper driver will not see distinct
    driver pulses.\n
    Similarly, the acceleration command A can be thought of as a signed fraction
    with the format "sa.b".  Here 's' again represents the sign bit and 'b'
    represents the number of bits to the right of the decimial, but 'a' is a
    negative number representing the first bit in A.  I.e., aside from the sign
    bit, A is b+a+1 bits wide.  For example, the specification s-4.8 means that
    A has a sign bit with 8-4+1 = 5 bits for the value of A with the leasts
    significant bit representing a rate of F^2/2^8.\n
    The bit widths are determined as follows: Let mR be the minimum non-zero
    magnitude of the rate, mA be the minimum non-zero mangitude of the
    acceleration, and MA be the mamximum magnitude of the acceleration, all in
    step/sec or step/sec^2.  Then\n
      r = ceil(-log_2(mR/F))\n
      a = floor(log_2(MA/F^2))\n
      b = ceil(-log_2(mA/f^2))\n
    Note:  r and b may be increased by a few bits if accurate representations of
    the minimum rates are needed.\n
  Example:
    A micro controller with an 8 MHz clock is used to operate a DRV8825 driving
    a stepper motor assembly.  The stepper motor has 200 steps per revolution,
    can be operated in full-step or a 16-step micro step mode, has a maximum
    rotation rate of 10 Hz, and has a maximum acceleration of 4 Hz/sec (i.e.,
    800 steps/sec^2).  The motor is attached to a 400mm theaded rod with a pitch
    of 4mm per revolution.\n
    The 1.9usec minimum high and low widths of the DRV8825 and the 8 MHz
    processor clock mean that the stepper motor controller can realistically be
    run at 500kHz.  The rate method to divide the micro controller clock to the
    internal processing rate is specified by "ratemethod" in the PERIPHERAL
    command.\n
    The bit widths are determine by choosing:\n
      mR = 10 step/sec
        ==> r = ceil(-log_2(mR/F))
              = ceil(-log_2((10 step/sec)/500kHz)
              = 16\n
      MA = 10 rev/sec^2 = 10*16*200 step/sec^2
        ==> a = floor(log_2(MA/F^2))
              = floor(log_2((32,000 step/sec^2)/500kHz^2))
              = -23\n
      mA = 20 step/sec^2 (in full step mode)
        ==> b = ceil(-log_2(mA/F^2))
              = 34\n
    The value r=16 means the rate would be stored in a 17-bit value.  Since 24
    is the next larger multiple of 8, a 24-bit width is specified for the rate
    with the resolution being F/2^(24-1) = 0.06 step/sec.\n
    The values a=-23 and b=34 mean the acceleration would be stored in a
    1+(34-23+1) = 13 bit value.  The next larger multiple of 8 is 16, which is 3
    bits more than the initial estimate, so the resolution is increased from 34
    to 37 bits to the right of the decimal and A is stored in a s-23.37
    fixed-point format.\n
    The number of full steps to move a nut from one of the of rod to the other
    is (400mm/(4mm/rev)*(200steps/rev)=20_000 steps.  In the micro-stepmode
    there are 16 micro steps per full step, so at most 320_000 micro steps can
    be performed before the full length of the rod is traversed.  I.e., a 19-bit
    counter will suffice for the worst-case unidirection motion.  This 19-bit
    count requires 3 8-bit writes to the control word.\n
    A "modewidth" of 1 is specifies so that the controller can be operated in
    either full step or a single hard-wired micro-step mode.  If all 3 of the
    DRV8825 mode pins were connected, then "modewidth=3" would need to
    specified.\n
    The peripheral is then specified as follows:\n
      CONSTANT          C_RATE_RES      23
      CONSTANT          C_ACCEL_SCALE   -23
      CONSTANT          C_ACCEL_RES     37
      CONSTANT          C_COUNT_WIDTH   19
      PERIPHERAL        stepper_motor   basename=stepper                \\
                                        outcontrol=O_stepper_control    \\
                                        outrecord=O_stepper_wr          \\
                                        outrun=O_stepper_go             \\
                                        indone=I_stepper_done           \\
                                        inerror=I_stepper_error         \\
                                        ratemethod=8_000_000/500_000    \\
                                        rateres=C_RATE_RES              \\
                                        accelscale=C_ACCEL_SCALE        \\
                                        accelres=C_ACCEL_RES            \\
                                        countwidth=C_COUNT_WIDTH        \\
                                        modewidth=1\n
    and the TBD byte control words are pushed into the peripheral as follows:
      R_0       24-bit initial rate stored in a 24-bit field (MSB first)
      A         16-bit acceleration stored in a 16-bit field (MSB first)
      COUNT     19-bit count stored in a 32-bit field (MSB first)
      MODE      1-bit mode stored as the lsb of an 8-bit field
    The control word is a total of 9 bytes wide.\n
    To command the peripheral to accelerate from stop to 200 steps/sec in one
    second in the forward direction using the full-step mode, the following
    seqeuence of bytes would be written to the control port:
      0x00 0x00 0x00    ; initial rate is zero
      0x00 0x6E         ; 200 step/sec^2 * 2^37 / 500kHz^2 = 109.95
      0x00 0x00 0x63    ; send 100 step commands (command 100-1=99)
      0x00              ; full-step mode\n
    To command the peripheral to decelerate from 200 step/sec to zero in one
    second, the following sequence of bytes would be written to the control
    port:
      0x00 0x01 0xDB    ; 200 step/sec * 2^23 / 500kHz
      0xFF 0x9C         ; negative of the above acceleration
      0x00 0x00 0x63    ; send 100 step commands (command 100-1=99)
      0x00              ; full-step mode\n
    The first of these two control words could be assembled and transmitted to
    the peripheral as follows:\n
      0x00                      ; mode
      .push24(${100-1})         ; send 100 step commands
      .push16(110)              ; 200 step/sec^2
      .push24(0)                ; initial rate is zero
      ${9-1} :loop swap .outport(O_stepper_control) .jumpc(loop,1-) drop
      .outstrobe(O_stepper_wr)  ; push the assembed control word into the FIFO
      ...
      .outstrobe(O_stepper_go)  ; perform the queued control words
    """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'FIFO',           r'\S+$',              lambda v : self.IntPow2Method(config,v,lowLimit=16),  ),
      ( 'accelres',       r'\S+$',              lambda v : self.IntMethod(config,v,lowLimit=1),       ),
      ( 'accelscale',     r'\S+$',              lambda v : self.IntMethod(config,v,highLimit=-1),     ),
      ( 'basename',       r'[A-Za-z]\w*$',      None,                                                 ),
      ( 'countwidth',     r'\S+$',              lambda v : self.IntMethod(config,v,lowLimit=1),       ),
      ( 'indone',         r'I_\w+$',            None,                                                 ),
      ( 'inerror',        r'I_\w+$',            None,                                                 ),
      ( 'modewidth',      r'\S+$',              lambda v : self.IntMethod(config,v,lowLimit=1),       ),
      ( 'outcontrol',     r'O_\w+$',            None,                                                 ),
      ( 'outrecord',      r'O_\w+$',            None,                                                 ),
      ( 'outrun',         r'O_\w+$',            None,                                                 ),
      ( 'ratemethod',     r'\S+$',              lambda v : self.RateMethod(config,v),                 ),
      ( 'rateres',        r'\S+$',              lambda v : self.IntMethod(config,v,lowLimit=1),       ),
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
      'accelres',
      'accelscale',
      'countwidth',
      'indone',
      'inerror',
      'outcontrol',
      'outrecord',
      'outrun',
      'ratemethod',
      'rateres',
    ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Set unspecified optional parameters.
    if not hasattr(self,'modewidth'):
      self.modewidth = 0;
    if not hasattr(self,'FIFO'):
      self.FIFO = 16
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO('o_%s_dir'    % self.basename, 1, 'output', loc)
    config.AddIO('o_%s_step'   % self.basename, 1, 'output', loc)
    if self.modewidth > 0:
      config.AddIO('o_%s_mode' % self.basename, 1, 'output', loc)
    config.AddIO('i_%s_error'  % self.basename, 1, 'input',  loc)
    config.AddSignal('s__%s__done' % self.basename, 1, loc);
    self.ix_outcontrol = config.NOutports()
    config.AddOutport((self.outcontrol,
                       False,
                       # empty list
                      ),loc)
    self.ix_outrecord = config.NOutports()
    config.AddOutport((self.outrecord,
                       True,
                       # empty list
                      ),loc)
    self.ix_outrun = config.NOutports()
    config.AddOutport((self.outrun,
                       True,
                       # empty list
                      ),loc)
    config.AddInport((self.inerror,
                      ('i_%s_error' % self.basename, 1, 'data', ),
                     ), loc)
    config.AddInport((self.indone,
                      ('s__%s__done' % self.basename, 1, 'data', ),
                     ), loc)
    # Compute bit widths.
    dw = config.Get('data_width')
    self.data_width = dw
    self.ratewidth = self.rateres + 1
    self.accelwidth = 1 + (self.accelscale + self.accelres + 1)
    self.accumwidth = self.accelres + 1
    self.controlwidth = dw*int((self.ratewidth+dw-1)/dw)
    self.controlwidth += dw*int((self.accelwidth+dw-1)/dw)
    self.controlwidth += dw*int((self.countwidth+dw-1)/dw)
    self.controlwidth += dw*int((self.modewidth+dw-1)/dw)
    self.controlwidthpacked = self.ratewidth + self.accelwidth + self.countwidth + self.modewidth
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if self.modewidth == 0:
      body = re.sub(r'@OUTMODE_BEGIN@.*?@OUTMODE_END@\n','',body,flags=re.DOTALL)
    else:
      body = re.sub(r'@OUTMODE_BEGIN@\n','',body)
      body = re.sub(r'@OUTMODE_END@\n','',body)
    for subpair in (
      ( r'@ACCEL_WIDTH@',               str(self.accelwidth),           ),
      ( r'@ACCUM_WIDTH@',               str(self.accumwidth),           ),
      ( r'@CONTROL_WIDTH@',             str(self.controlwidth),         ),
      ( r'@CONTROL_WIDTH_PACKED@',      str(self.controlwidthpacked),   ),
      ( r'@COUNT_WIDTH@',               str(self.countwidth),           ),
      ( r'@DW@',                        str(self.data_width),           ),
      ( r'@DWM1@',                      str(self.data_width-1),         ),
      ( r'@FIFO_DEPTH@',                str(self.FIFO),                 ),
      ( r'@IX_OUTCONTROL@',             str(self.ix_outcontrol),        ),
      ( r'@IX_OUTRECORD@',              str(self.ix_outrecord),         ),
      ( r'@IX_OUTRUN@',                 str(self.ix_outrun),            ),
      ( r'@MODE_WIDTH@',                str(self.modewidth),            ),
      ( r'@NBITS_FIFO_DEPTH@',          str(CeilLog2(self.FIFO)),       ),
      ( r'@OUTMODEWIDTH@',              str(self.modewidth),            ),
      ( r'@RATEMETHOD@',                str(self.ratemethod),           ),
      ( r'@RATE_WIDTH@',                str(self.ratewidth),            ),
      ( r'\bL__',                       'L__%s__' % self.basename,      ),
      ( r'\bi__',                       'i_%s_' % self.basename,        ),
      ( r'\bo__',                       'o_%s_' % self.basename,        ),
      ( r'\bs__',                       's__%s__' % self.basename,      ),
    ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
