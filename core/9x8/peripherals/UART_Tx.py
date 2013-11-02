################################################################################
#
# Copyright 2012-2013, Sinclair R.F., Inc.
#
################################################################################

import math;
import re;

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException;

class UART_Tx(SSBCCperipheral):
  """
  Transmit side of a UART:
    1 start bit
    8 data bits
    1 or 2 stop bits\n
  Usage:
    PERIPHERAL UART_Tx outport=O_outport_name      \\
                       outstatus=I_outstatus_name  \\
                       baudmethod={clk/rate|count} \\
                       [outsignal=o_name]          \\
                       [noOutFIFO|outFIFO=n]       \\
                       [nStop={1|2}]\n
  Where:
    outport=O_outport_name
      specifies the symbol used by the outport instruction to write a byte to
      the peripheral
      Note:  The name must start with "O_".
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
    outsignal=o_name
      optionally specifies the name of the output signal
      Default:  o_UART_Tx
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
      Note:  the peripheral does not accept 1.5 stop bits\n
  The following ports are provided by this peripheral:
    O_outport_name
      output the next 8-bit value to transmit or to queue for transmission
      Note:  If there is no output FIFO or if there is an output FIFO and this
             write would cause a FIFO overflow, then this byte will be
             discarded.
    I_outstatus_name
      input the status of the output side of the peripheral
      bit 0:  output busy
        this bit will be high when the output side of the peripheral cannot
        accept more writes
        Note:  If there is no FIFO this means that the peripheral is still
               transmitting the last byte.  If there is an output FIFO it means
               that it is full.\n
        Note:  "Busy" is used rather that "ready" to facilitate loops that wait
               for a not-busy status to send the next byte.  See the examples below.\n
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
          ('noOutFIFO',  None,         None,  ),
          ('nStop',      r'[12]$',     int,   ),
          ('outport',    r'O_\w+$',    None,  ),
          ('outsignal',  r'o_\w+$',    None,  ),
          ('outstatus',  r'I_\w+$',    None,  ),
        ):
        if param == param_test[0]:
          self.AddAttr(config,param,param_arg,param_test[1],ixLine,param_test[2]);
          break;
      else:
        if param == 'baudmethod':
          self.AddRateMethod(config,param,param_arg,ixLine);
        elif param in ('outFIFO',):
          self.AddAttr(config,param,param_arg,r'[1-9]\d*$',ixLine,int);
          x = getattr(self,param);
          if math.modf(math.log(x,2))[0] != 0:
            raise SSBCCException('%s=%d must be a power of 2 at line %d' % (param,x,ixLine,));
        else:
          raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are provided.
    for paramname in (
        'baudmethod',
        'outport',
        'outstatus',
      ):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at line %d' % (paramname,ixLine,));
    # Set optional parameters.
    for optionalpair in (
        ('nStop',     1,           ),
        ('outsignal', 'o_UART_Tx', ),
      ):
      if not hasattr(self,optionalpair[0]):
        setattr(self,optionalpair[0],optionalpair[1]);
    # Ensure exclusive pair configurations are set and consistent.
    for exclusivepair in (
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
    config.AddIO(self.outsignal,1,'output',ixLine);
    config.AddSignal('s__%s__Tx'          % self.namestring,8,ixLine);
    config.AddSignal('s__%s__Tx_busy'     % self.namestring,1,ixLine);
    config.AddSignal('s__%s__Tx_wr'       % self.namestring,1,ixLine);
    config.AddOutport((self.outport,False,
                   ('s__%s__Tx'           % self.namestring,8,'data',),
                   ('s__%s__Tx_wr'        % self.namestring,1,'strobe',),
                  ),ixLine);
    config.AddInport((self.outstatus,
                   ('s__%s__Tx_busy'      % self.namestring,1,'data',),
                 ),ixLine);
    # Add the 'clog2' function to the processor (if required).
    config.functions['clog2'] = True;

  def GenVerilog(self,fp,config):
    for bodyextension in ('.v',):
      body = self.LoadCore(self.peripheralFile,bodyextension);
      for subpair in (
                    (r'\bL__',          'L__@NAME@__', ),
                    (r'\bgen__',        'gen__@NAME@__', ),
                    (r'\bs__',          's__@NAME@__', ),
                    (r'@BAUDMETHOD@',   str(self.baudmethod), ),
                    (r'@NSTOP@',        str(self.nStop), ),
                    (r'@OUTFIFO@',      str(self.outFIFO), ),
                    (r'@NAME@',         self.namestring, ),
                  ):
        body = re.sub(subpair[0],subpair[1],body);
      body = self.GenVerilogFinal(config,body);
      fp.write(body);
