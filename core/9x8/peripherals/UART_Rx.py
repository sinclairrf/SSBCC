################################################################################
#
# Copyright 2013, Sinclair R.F., Inc.
#
################################################################################

import math;
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class UART_Rx(SSBCCperipheral):
  """
  Receive UART:
    1 start bit
    8 data bits
    1 or 2 stop bits\n
  Usage:
    PERIPHERAL UART_Rx inport=I_inport_name        \\
                       inempty=I_inempty_name      \\
                       baudmethod={clk/rate|count} \\
                       [insignal=i_name]           \\
                       [noSync|sync=n]             \\
                       [noDeglitch|deglitch=n]     \\
                       [noInFIFO|inFIFO=n]         \\
                       [nStop={1|2}]               \n
  Where:
    inport=I_inport_name
      specifies the symbol used by the inport instruction to read a received by
      from the peripheral
      Note:  The name must start with "I_".
    inempty=I_inempty_name
      specifies the symbol used by the inport instruction to get the empty
      status of the input side of the peripheral
      Note:  The name must start with "I_".
    baudmethod
      specifies the method to generate the desired bit rate:
      1st method:  clk/rate
        clk is the frequency of "i_clk" in Hz
          a number will be interpreted as the clock frequency in Hz
          a symbol will be interpreted as a parameter
            Note:  this parameter must have been declared with a "PARAMETER"
            command
        rate is the desired baud rate
          this is specified as per "clk"
      2nd method:
        specify the number of "i_clk" clock cycles between bit edges
      Note:  clk, rate, and count can be parameters or constants.  For example,
             the following uses the parameter G_CLK_FREQ_HZ for the clock
             frequency and a hard-wired baud rate of 9600:
             "baudmethod=G_CLK_FREQ_HZ/9600".
      Note:  The numeric values can have Verilog-style '_' separators between
               the digits.  For example, 100_000_000 represents 100 million.
    insignal=i_name
      optionally specifies the name of the single-bit transmit signal
      Default:  i_UART_Rx
    noSync
      optionally state no synchronization or registration is performed on the
      input signal.
    sync=n
      optionally state that an n-bit synchronizer will be performed on the
      input signal.
      Note:  sync=3 is the default.
    noDeglitch
      optionally state that no deglitching is performed on the input signal.
      Note:  This is the default.
    deglitching=n
      optionally state that an n-bit deglitcher is performed on the input signal
      Note:  Deglitching consists of changing the output state when n
             successive input bits are in the opposite state.
    noInFIFO
      optionally state that the peripheral will not have an input FIFO
      Note:  This is the default.
    inFIFO=n
      optionally add a FIFO of depth n to the input side of the UART
      Note:  n must be a power of 2.
    nStop=n
      optionally configure the peripheral for n stop bits
      default:  1 stop bit
      Note:  n must be 1 or 2
      Note:  the peripheral does not accept 1.5 stop bits
  The following ports are provided by this peripheral:
    I_inport_name
      input a recieved byte from the peripheral
      Note:  If there is no input FIFO, then this is the last received byte.
             If there is an input FIFO, then this is the next byte in the FIFO.
      Note:  If there is an input FIFO and the read would cause a FIFO
             underflow, this will repeat the last received byte.
    I_inempty_name
      input the empty status of the input side of the peripheral
      bit 0:  input empty
        this bit will be high when the input side of the peripheral has one or
        more bytes read to be read
        Note:  If there is no FIFO this means that a single byte is ready to be
               read and has not been read.  If there is an input FIFO this
               means that there are one or more bytes in the FIFO.
        Note:  "Empty" is used rather than "ready" to facilitate loops that
               respond when there is a new byte ready to be processed.  See the
               examples below.
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Get the parameters.
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      for param_test in (
          ('deglitch',   r'[1-9]\d*$', int,   ),
          ('inempty',    r'I_\w+$',    None,  ),
          ('inport',     r'I_\w+$',    None,  ),
          ('insignal',   r'i_\w+$',    None,  ),
          ('noDeglitch', None,         None,  ),
          ('noInFIFO',   None,         None,  ),
          ('noSync',     None,         None,  ),
          ('nStop',      r'[12]$',     int,   ),
          ('sync',       r'[1-9]\d*$', int,   ),
        ):
        if param == param_test[0]:
          self.AddAttr(config,param,param_arg,param_test[1],loc,param_test[2]);
          break;
      else:
        if param == 'baudmethod':
          self.AddRateMethod(config,param,param_arg,loc);
        elif param in ('inFIFO',):
          self.AddAttr(config,param,param_arg,r'[1-9]\d*$',loc,int);
          x = getattr(self,param);
          if math.modf(math.log(x,2))[0] != 0:
            raise SSBCCException('%s=%d must be a power of 2 at %s' % (param,x,loc,));
        else:
          raise SSBCCException('Unrecognized parameter at %s: %s' % (loc,param,));
    # Ensure the required parameters are provided.
    for paramname in (
        'baudmethod',
        'inempty',
        'inport',
      ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,));
    # Set optional parameters.
    for optionalpair in (
        ('insignal',  'i_UART_Rx', ),
        ('nStop',     1,           ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1]);
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
        ('noSync',     'sync',     'sync',       3,    ),
        ('noDeglitch', 'deglitch', 'noDeglitch', True, ),
        ('noInFIFO',   'inFIFO',   'noInFIFO',   True, ),
      ):
      if hasattr(self,exclusivepair[0]) and hasattr(self,exclusivepair[1]):
        raise SSBCCException('Only one of "%s" and "%s" can be specified at %s' % (exclusivepair[0],exclusivepair[1],loc,));
      if not hasattr(self,exclusivepair[0]) and not hasattr(self,exclusivepair[1]):
        setattr(self,exclusivepair[2],exclusivepair[3]);
      if hasattr(self,exclusivepair[0]):
        delattr(self,exclusivepair[0]);
        setattr(self,exclusivepair[1],0);
    # Set the string used to identify signals associated with this peripheral.
    self.namestring = self.insignal;
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.insignal,1,'input',loc);
    config.AddSignal('s__%s__Rx'          % self.namestring,8,loc);
    config.AddSignal('s__%s__Rx_empty'    % self.namestring,1,loc);
    config.AddSignal('s__%s__Rx_rd'       % self.namestring,1,loc);
    config.AddInport((self.inport,
                    ('s__%s__Rx'          % self.namestring,8,'data',),
                    ('s__%s__Rx_rd'       % self.namestring,1,'strobe',),
                   ),loc);
    config.AddInport((self.inempty,
                   ('s__%s__Rx_empty'     % self.namestring,1,'data',),
                  ),loc);
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True;

  def GenVerilog(self,fp,config):
    for bodyextension in ('.v',):
      body = self.LoadCore(self.peripheralFile,bodyextension);
      for subpair in (
                    (r'\bL__',          'L__@NAME@__', ),
                    (r'\bgen__',        'gen__@NAME@__', ),
                    (r'\bs__',          's__@NAME@__', ),
                    (r'@INPORT@',       self.insignal, ),
                    (r'@BAUDMETHOD@',   str(self.baudmethod), ),
                    (r'@SYNC@',         str(self.sync), ),
                    (r'@DEGLITCH@',     str(self.deglitch), ),
                    (r'@INFIFO@',       str(self.inFIFO), ),
                    (r'@NSTOP@',        str(self.nStop), ),
                    (r'@NAME@',         self.namestring, ),
                  ):
        body = re.sub(subpair[0],subpair[1],body);
      body = self.GenVerilogFinal(config,body);
      fp.write(body);
