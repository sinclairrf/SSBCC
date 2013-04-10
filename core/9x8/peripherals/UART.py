################################################################################
#
# Copyright 2013, Sinclair R.F., Inc.
#
################################################################################

import math;
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class UART(SSBCCperipheral):
  """
  Transmit/receive UART:
    1 start bit
    8 data bits
    1 or 2 stop bits\n
  Usage:
    PERIPHERAL UART    inport=I_inport_name        \\
                       outport=O_outport_name      \\
                       inempty=I_inempty_name      \\
                       inerror=I_inerror_name      \\
                       outstatus=I_outstatus_name  \\
                       baudmethod={clk/rate|count} \\
                       [insignal=i_name]           \\
                       [outsignal=o_name]          \\
                       [noSync|sync=n]             \\
                       [noDeglitch|deglitch=n]     \\
                       [noInFIFO|inFIFO=n]         \\
                       [noOutFIFO|outFIFO=n]       \\
                       [nStop={1|2}]               \\
                       [edgetol=x]                 \n
  Where:
    inport=I_inport_name
      specifies the symbol used by the inport instruction to read a received by
      from the peripheral
      Note:  The name must start with "I_".
    outport=O_outport_name
      specifies the symbol used by the outport instruction to write a byte to
      the peripheral
      Note:  The name must start with "O_".
    inempty=I_inempty_name
      specifies the symbol used by the inport instruction to get the empty
      status of the input side of the peripheral
      Note:  The name must start with "I_".
    inerror=I_inerror_name
      specified the symbol used by the inport instruction to get the error
      status of the input side of the peripheral
      Note:  The name must start with "I_".
    outstatus=I_outstatus_name
      specifies the symbol used by the inport instruction to get the status of
      the output side of the peripheral
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
    outsignal=o_name
      optionally specifies the name of the output signal
      Default:  o_UART_Tx
    noSync
      optionally state no synchronization or registration is performed on the
      input signal.
    sync=n
      optionally state that an n-bit synchronizer will be performed on the
      input signal.
      Note:  sync=3 is the default.
    noDeglitch
      optionally state that no deglitching is performed on the input signal.
      Note:  This is the defalt.
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
    noOutFIFO
      optionally state that the peripheral will not have an output FIFO
      Note:  This is the default.
    outFIFO=n
      optionally add a FIFO of depth n to the output side of the UART
      Note:  n must be a power of 2.
    nStop=n
      optionally configure the peripheral for n stop bits
      default:  1 stop bit
      Note:  n must be 1 or 2
      Note:  the peripheral does not accept 1.5 stop bits
    edgetol=x
      optionally specify the tolerance for edge detection/generation for the
      deserializer as x%
      Note:  The default is 2.5%
      Note:  The tolerance is cumulative as edges are missed, so a tolerance
             that accumulates to 50% or more in 9 edges, i.e., about 5.5%, is
             excessive.  A reasonable limit is about half of that, i.e., about
             2.5%, so that is what is specified.  Smaller tolerances required
             the recevied signal and the edge generating using the provided
             micro controller clock to more closely match the nominal baud rate.\n
      Note:  The tolerance is limited to be between 0.1 and 5.5 and may be
             expressed as an integer or as a fraction with a single digit after
             the decimal.
  The following ports are provided by this peripheral:
    I_inport_name
      input a recieved byte from the peripheral
      Note:  If there is no input FIFO, then this is the last received byte.
             If there is an input FIFO, then this is the next byte in the FIFO.
      Note:  If there is an input FIFO and the read would cause a FIFO
             underflow, this will repeat the last received byte.
    O_outport_name
      output the next 8-bit value to transmit or to queue for transmission
      Note:  If there is no output FIFO or if there is an output FIFO and this
             write would cause a FIFO overflow, then this byte will be
             discarded.
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
    I_inerror_name
      input the error status of the input side of the peripheral
      Note:  The 3 bits in this value have the following meaning:
             bit 0 -- a read was performed when no data was available or a new
                      byte of data was received and the input buffer or FIFO was
                      already full
                      Note:  This bit indicates that an error has occured and
                             one or more bytes is missing in the data stream.
             bit 1 -- the received edge rate does not match the commanded edge
                      rate, clock, and tolerance
                      Note:  This error is cleared by an idle input stream.
             bit 2 -- missing start bit or stop bit(s) in data stream
                      Note:  This error is cleared by an idle input stream.
    I_outstatus_name
      input the status of the output side of the peripheral
      bit 0:  output busy
        this bit will be high when the output side of the peripheral cannot
        accept more writes
        Note:  If there is no FIFO this means that the peripheral is still
               transmitting the last byte.  If there is an output FIFO it means
               that it is full.\n
        Note:  "Busy" is used rather that "ready" to facilitate loops that wait
               for a not-busy status to send the next byte.  See the examples below.
  WARNING:  The peripheral is very simple and does not protect against writing a
            new value in the middle of a transmition or writing to a full FIFO.
            Adding such logic would be contrary to the design principle of
            keeping the HDL small and relying on the assembly code to provide
            the protection.\n
  Example:  Configure the UART for 115200 baud using a 100 MHz clock and
            transmit the message "Hello World!"\n
    Within the processor architecture file include the configuration command:\n
    PERIPHERAL UART_Tx O_UART_TX I_UART_TX baudmethod=100_000_000/115200\n
    Use the following assembly code to transmit the message "Hello World!".
    This transmits the entire message whether or not the peripheral has a FIFO.\n
    N"Hello World!\\r\\n"
      :loop .outport(O_UART_TX) :wait .inport(I_UART_TX_BUSY) .jumpc(wait) .jumpc(loop,nop) drop
  """

  def __init__(self,peripheralFile,config,param_list,ixLine):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile;
    # Get the parameters.
    for param_tuple in param_list:
      param = param_tuple[0];
      param_arg = param_tuple[1];
      for param_test in (
          ('deglitch',   r'[1-9]\d*$', int,   ),
          ('edgetol',    r'(0\.[1-9]|[1-4](\.\d)?|5(\.[0-5])?)$',
                                       lambda(x):int(10*float(x)+0.5), ),
          ('inempty',    r'I_\w+$',    None,  ),
          ('inerror',    r'I_\w+$',    None,  ),
          ('inport',     r'I_\w+$',    None,  ),
          ('insignal',   r'i_\w+$',    None,  ),
          ('noDeglitch', None,         None,  ),
          ('noInFIFO',   None,         None,  ),
          ('noOutFIFO',  None,         None,  ),
          ('noSync',     None,         None,  ),
          ('nStop',      r'[12]$',     int,   ),
          ('outport',    r'O_\w+$',    None,  ),
          ('outsignal',  r'o_\w+$',    None,  ),
          ('outstatus',  r'I_\w+$',    None,  ),
          ('sync',       r'[1-9]\d*$', int,   ),
        ):
        if param == param_test[0]:
          self.AddAttr(config,param,param_arg,param_test[1],ixLine,param_test[2]);
          break;
      else:
        if param == 'baudmethod':
          self.AddRateMethod(config,param,param_arg,ixLine);
        elif param in ('inFIFO','outFIFO',):
          self.AddAttr(config,param,param_arg,r'[1-9]\d*$',ixLine,int);
          x = getattr(self,param);
          if math.modf(math.log(x,2))[0] != 0:
            raise SSBCCException('%s=%d must be a power of 2 at line %d' % (param,x,ixLine,));
        else:
          raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are provided.
    for paramname in (
        'baudmethod',
        'inempty',
        'inerror',
        'inport',
        'outport',
        'outstatus',
      ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at line %d' % (paramname,ixLine,));
    # Set optional parameters.
    for optionalpair in (
        ('edgetol',   25,          ),
        ('insignal',  'i_UART_Rx', ),
        ('nStop',     1,           ),
        ('outsignal', 'o_UART_Tx', ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1]);
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
        ('noSync',     'sync',     'sync',       3,    ),
        ('noDeglitch', 'deglitch', 'noDeglitch', True, ),
        ('noInFIFO',   'inFIFO',   'noInFIFO',   True, ),
        ('noOutFIFO',  'outFIFO',  'noOutFIFO',  True, ),
      ):
      if hasattr(self,exclusivepair[0]) and hasattr(self,exclusivepair[1]):
        raise SSBCCException('Only one of "%s" and "%s" can be specified at line %d' % (exclusivepair[0],exclusivepair[1],ixLine,));
      if not hasattr(self,exclusivepair[0]) and not hasattr(self,exclusivepair[1]):
        setattr(self,exclusivepair[2],exclusivepair[3]);
      if hasattr(self,exclusivepair[0]):
        delattr(self,exclusivepair[0]);
        setattr(self,exclusivepair[1],0);
    # Set the string used to identify signals associated with this peripheral.
    self.namestring = self.outsignal;
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.insignal,1,'input',ixLine);
    config.AddIO(self.outsignal,1,'output',ixLine);
    config.AddSignal('s__%s__Rx'          % self.namestring,8,ixLine);
    config.AddSignal('s__%s__Rx_empty'    % self.namestring,1,ixLine);
    config.AddSignal('s__%s__Rx_error'    % self.namestring,3,ixLine);
    config.AddSignal('s__%s__Rx_error_rd' % self.namestring,1,ixLine);
    config.AddSignal('s__%s__Rx_rd'       % self.namestring,1,ixLine);
    config.AddSignal('s__%s__Tx'          % self.namestring,8,ixLine);
    config.AddSignal('s__%s__Tx_busy'     % self.namestring,1,ixLine);
    config.AddSignal('s__%s__Tx_wr'       % self.namestring,1,ixLine);
    config.AddInport((self.inport,
                    ('s__%s__Rx'          % self.namestring,8,'data',),
                    ('s__%s__Rx_rd'       % self.namestring,1,'strobe',),
                   ),ixLine);
    config.AddInport((self.inempty,
                   ('s__%s__Rx_empty'     % self.namestring,1,'data',),
                  ),ixLine);
    config.AddInport((self.inerror,
                   ('s__%s__Rx_error'     % self.namestring,3,'data',),
                   ('s__%s__Rx_error_rd'  % self.namestring,1,'strobe',),
                  ),ixLine);
    config.AddOutport((self.outport,
                   ('s__%s__Tx'           % self.namestring,8,'data',),
                   ('s__%s__Tx_wr'        % self.namestring,1,'strobe',),
                  ),ixLine);
    config.AddInport((self.outstatus,
                   ('s__%s__Tx_busy'      % self.namestring,1,'data',),
                 ),ixLine);
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True;

  def GenVerilog(self,fp,config):
    for bodyextension in ('_Rx.v','_Tx.v',):
      body = self.LoadCore(self.peripheralFile,bodyextension);
      for subpair in (
                    (r'\bL__',          'L__@NAME@__', ),
                    (r'\bgen__',        'gen__@NAME@__', ),
                    (r'\bs__',          's__@NAME@__', ),
                    (r'@INPORT@',       self.insignal, ),
                    (r'@BAUDMETHOD@',   str(self.baudmethod), ),
                    (r'@EDGETOL@',      str(self.edgetol), ),
                    (r'@SYNC@',         str(self.sync), ),
                    (r'@DEGLITCH@',     str(self.deglitch), ),
                    (r'@INFIFO@',       str(self.inFIFO), ),
                    (r'@NSTOP@',        str(self.nStop), ),
                    (r'@OUTFIFO@',      str(self.outFIFO), ),
                    (r'@NAME@',         self.namestring, ),
                  ):
        body = re.sub(subpair[0],subpair[1],body);
      body = self.GenVerilogFinal(config,body);
      fp.write(body);
