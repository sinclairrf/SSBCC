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
  """Transmit side of a UART:
  1 start bit
  8 data bits
  n stop bits

Usage:
  PERIPHERAL UART_Tx outport=O_name \\
                     inport=I_name \\
                     outsignal=o_name \\
                     baudmethod={clk/rate|count} \\
                     [noFIFO|FIFO=n] \\
                     [nStop={1|2}]

Where:
  outport=O_name
    specifies the symbol used by the outport instruction to write a byte to the
    peripheral
    Note:  The name must start with "O_".
  inport=I_name
    specifies the symbol used by the inport instruction to get the status of the
    peripheral
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
      the following uses the parameter G_CLK_FREQ_HZ for the clock frequency
      and a hard-wired baud rate of 9600:  "baudmethod=G_CLK_FREQ_HZ/9600".
    Note:  The numeric values can have Verilog-style '_' separators between the
      digits.  For example, 100_000_000 represents 100 million.
  noFIFO
    the peripheral will not have a FIFO
    Note:  This is the default.
  FIFO=n
    adds a FIFO of depth n
    Note:  n must be a power of 2.
  nStop=n
    configures the peripheral for n stop bits
    default:  1 stop bit
    Note:  n must be at least 1
    Note:  normal values are 1 and 2
  outsignal=o_name
    specifies the name of the output signal
    Default:  o_UART_Tx

The following OUTPORT is provided by this peripheral:
  O_name
    output the next 8-bit value to transmit or to queue for transmission

The following INPORT is provided by this peripheral:
  I_name
    bit 0:  busy status
      this bit will be high when the core cannot accept more data
      Note:  If there is no FIFO this means that the core is still
        transmitting the last byte.  If there is a FIFO it means that the FIFO
        cannot accept any more data.

WARNING:  The HDL core is very simple and does not protect against writing a new
          value in the middle of a transmition or writing to a full FIFO.
          Adding such logic would be contrary to the design principle of
          keeping the HDL small and relying on the assembly code to provide the
          protection.

Example:  Configure the UART for 115200 baud using a 100 MHz clock and transmit
          the message "Hello World!"

  Within the processor architecture file include the configuration command:

  PERIPHERAL UART_Tx O_UART_TX I_UART_TX baudmethod=100_000_000/115200

  Use the following assembly code to transmit the message "Hello World!".  This
  transmits the entire message whether or not the core has a FIFO.

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
      if param == 'baudmethod':
        self.ProcessBaudMethod(config,param_arg,ixLine);
      elif param == 'FIFO':
        self.AddAttr(config,param,param_arg,r'[1-9]\d*$',ixLine);
        self.FIFO = int(self.FIFO);
        if math.modf(math.log(self.FIFO,2))[0] != 0:
          raise SSBCCException('FIFO=%d must be a power of 2 at line %d' % (self.FIFO,ixLine,));
      elif param == 'inport':
        self.AddAttr(config,param,param_arg,'I_\w+$',ixLine);
      elif param == 'noFIFO':
        self.AddAttr(config,param,param_arg,None,ixLine);
      elif param == 'nStop':
        self.AddAttr(config,param,param_arg,r'[12]$',ixLine);
        self.nStop = int(self.nStop);
      elif param == 'outport':
        self.AddAttr(config,param,param_arg,r'O_\w+$',ixLine);
      elif param == 'outsignal':
        self.AddAttr(config,param,param_arg,r'o_\w+$',ixLine);
      else:
        raise SSBCCException('Unrecognized parameter at line %d: %s' % (ixLine,param,));
    # Ensure the required parameters are provided.
    if not hasattr(self,'baudmethod'):
      raise SSBCCException('Required parameter "baudmethod" is missing at line %d' % ixLine);
    if not hasattr(self,'inport'):
      raise SSBCCException('Required parameter "inport" is missing at line %d' % ixLine);
    if not hasattr(self,'outport'):
      raise SSBCCException('Required parameter "outport" is missing at line %d' % ixLine);
    # Set optional parameters.
    if not hasattr(self,'nStop'):
      self.nStop = 1;
    if not hasattr(self,'outsignal'):
      self.outsignal = 'o_UART_Tx';
    if not hasattr(self,'FIFO') and not hasattr(self,'noFIFO'):
      self.noFIFO = True;
    # Ensure parameters do not conflict.
    if hasattr(self,'FIFO') and hasattr(self,'noFIFO'):
      raise SSBCCException('Only one of "FIFO" and "noFIFO" can be specified at line %d' % ixLine);
    # Final parameter settings.
    if not hasattr(self,'noFIFO'):
      self.noFIFO = False;
    if self.noFIFO:
      self.FIFO = 0;
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.outsignal,1,'output');
    config.AddSignal('s__%s__Tx' % self.outsignal,8);
    config.AddSignal('s__%s__busy' % self.outsignal,1);
    config.AddSignal('s__%s__wr' % self.outsignal,1);
    config.AddInport((self.inport,
                     ('s__%s__busy' % self.outsignal,1,'data',),
                    ));
    config.AddOutport((self.outport,
                      ('s__%s__Tx' % self.outsignal,8,'data',),
                      ('s__%s__wr' % self.outsignal,1,'strobe',),
                     ));
    # Add the 'clog2' function to the core (if required).
    config.functions['clog2'] = True;

  def ProcessBaudMethod(self,config,param_arg,ixLine):
    if hasattr(self,'baudmethod'):
      raise SSBCCException('baudmethod repeated at line %d' % ixLine);
    if param_arg.find('/') < 0:
      if self.IsInt(param_arg):
        self.baudmethod = str(self.ParseInt(param_arg));
      elif self.IsParameter(config,param_arg):
        self.baudmethod = param_arg;
      else:
        raise SSBCCException('baudmethod with no "/" must be an integer or a previously declared parameter at line %d' % ixLine);
    else:
      baudarg = re.findall('([^/]+)',param_arg);
      if len(baudarg) == 2:
        if not self.IsInt(baudarg[0]) and not self.IsParameter(config,baudarg[0]):
          raise SSBCCException('Numerator in baudmethod must be an integer or a previously declared parameter at line %d' % ixLine);
        if not self.IsInt(baudarg[1]) and not self.IsParameter(config,baudarg[1]):
          raise SSBCCException('Denominator in baudmethod must be an integer or a previously declared parameter at line %d' % ixLine);
        for ix in range(2):
          if self.IsInt(baudarg[ix]):
            baudarg[ix] = str(self.ParseInt(baudarg[ix]));
        self.baudmethod = '('+baudarg[0]+'+'+baudarg[1]+'/2)/'+baudarg[1];
    if not hasattr(self,'baudmethod'):
      raise SSBCCException('Bad baudmethod value at line %d:  "%s"' % (ixLine,param_arg,));

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v');
    for subs in (
                  (r'\bL__',            'L__@NAME@__',),
                  (r'\bs__',            's__@NAME@__',),
                  (r'@BAUDMETHOD@',     str(self.baudmethod),),
                  (r'@FIFO@',           str(self.FIFO),),
                  (r'@NSTOP@',          str(self.nStop), ),
                  (r'@NAME@',           self.outsignal,),
                ):
      body = re.sub(subs[0],subs[1],body);
    body = self.GenVerilogFinal(config,body);
    fp.write(body);
