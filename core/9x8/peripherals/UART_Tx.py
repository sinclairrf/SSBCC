################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Transmit side of a UART:
#   1 start bit
#   8 data bits
#   n stop bits
#
# Usage:
#   PERIPHERAL UART_Tx O_name I_name [name=valid_name],[noFIFO|FIFO=n],[nStop=n],baudmethod=[clk/rate,count]
# Where:
#   O_name
#     is the symbol used by the outport instruction to write a byte to the
#     peripheral
#     Note:  This name must start with "O_".
#   I_name
#     is the symbol used by the inport instruction to get the status of the
#     peripheral
#     Note:  This name must start with "I_".
#   name
#     is the base name for the outport symbol within the assembly code
#     default:  UART
#   noFIFO
#     the peripheral will not have a FIFO
#     this is the default
#   FIFO=n
#     adds a FIFO of depth n
#   nStop=n
#     configures the peripheral for n stop bits
#     default:  1 stop bit
#     Note:  n must be at least 1
#   baudmethod
#     specifies the method to generate the desired bit rate:
#     1st method:  clk/rate
#       clk is the frequency of "i_clk" in Hz
#         a number will be interpreted as the clock frequency in Hz
#         a symbol will be interpreted as a parameter
#           Note:  this parameter must have been declared with a "PARAMETER"
#           command
#       rate is the desired baud rate
#         this is specified as per "clk"
#     2nd method:
#       specify the number of "i_clk" clock cycles between bit edges
#
# The following INPORTs are provided by the peripheral:
#   I_name_STATUS
#     bit 0:  busy status
#       this bit will be high when the core cannot accept more data
#       Note:  If there is no FIFO this means that the core is still
#         transmitting the last byte.  If there is a FIFO it means that the FIFO
#         cannot accept any more data.
#
# The following OUTPORTs are provided by the peripheral:
#   O_name_TX
#     this is the next 8-bit value to transmit or to queue for transmission
#
################################################################################

import re;

from ssbccUtil import *;

class UART_Tx:

  def __init__(self,config,param_list):
    # Set the defaults.
    self.baudmethod = None;
    self.FIFO = None;
    self.name = None;
    self.nStop = None;
    # Ensure there are enough arguments to the peripheral
    if len(param_list) < 2:
      raise SSBCCException('UART_Tx peripheral requires outport and inport names');
    # Get the outport symbol
    param_outport = param_list[0];
    if len(param_outport) != 1:
      raise SSBCCException('No "=" allowed in UART_Tx peripheral outport symbol');
    param_outport = param_outport[0];
    if not re.match('^O_\w+$',param_outport):
      raise SSBCCException('First argument must be the outport name starting with "O_"');
    self.outport = param_outport;
    # Get the inport symbol
    param_inport = param_list[1];
    if len(param_inport) != 1:
      raise SSBCCException('No "=" allowed in UART_Tx peripheral inport symbol');
    param_inport = param_inport[0];
    if not re.match('^I_\w+$',param_inport):
      raise SSBCCException('First argument must be the inport name starting with "I_"');
    self.inport = param_inport;
    # Parse the optional parameters.
    for param_tuple in param_list[2:]:
      param = param_tuple[0];
      param_arg = param_tuple[1:];
      # baudmethod=rate/baudrate or baudmethod=decimate_count
      if param == 'baudmethod':
        if type(self.baudmethod) != type(None):
          raise SSBCCException('baudmethod can only be specified once');
        if not param_arg:
          raise SSBCCException('baudmethod argument missing');
        self.ProcessBaudMethod(config,param_arg[0]);
      # FIFO=
      elif param == 'FIFO':
        if type(self.FIFO) != type(None):
          raise SSBCCException('FIFO length cannot be specified after "noFIFO"');
        self.FIFO = int(param_arg);
        if self.FIFO <= 0:
          raise SSBCCException('FIFO length must be positive');
      # name=
      elif param=='name':
        if type(self.name) != type(None):
          raise SSBCCException('name can only be specified once');
        self.name = param_arg;
      # noFIFO
      elif param == 'noFIFO':
        if type(self.FIFO) != type(None):
          raise SSBCCException('noFIFO follows FIFO=xxx specification');
        self.FIFO = False;
      # nStop=
      elif param == 'nStop':
        if type(self.nStop) != type(None):
          raise SSBCCException('nStop can only be specified once');
        self.nStop = int(param_arg);
        if self.nStop <= 0:
          raise SSBCCException('nStop must be 1 or more');
      # no match
      else:
        raise SSBCCException('Unrecognized parameter: %s' % param);
    # Ensure the required parameters are provided and set non-specified optional parameters.
    if not self.baudmethod:
      raise SSBCCException('Required parameter "baudmethod" is missing');
    if type(self.FIFO) == type(None):
      self.FIFO = False;
    if not self.name:
      self.name = 'UART';
    if type(self.nStop) == type(None):
      self.nStop = 1;
    # List the I/Os and global signals required by this peripheral.
    config['signals'].append(('s_%s_Tx' % self.name,8,));
    config['inports'].append(('I_%s_STATUS' % self.name,
                             ('s_%s_status' % self.name,1,'data'),
                            ));
    config['outports'].append(('O_%s_TX' % self.name,
                              ('o_%s_Tx' % self.name,1,'data',),
                             ));

  def ProcessBaudMethod(self,config,param_arg):
    if param_arg.find('/') > 0:
      baudarg = re.findall('([^/]+)',param_arg);
      if len(baudarg) != 2:
        raise SSBCCException('baudmethod cannot have more than one "/"');
      if not (re.match(r'^\d+$',baudarg[0]) and re.match(r'^\d+$',baudarg[1])):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet');
      self.baudmethod = (int(baudarg[0])+int(baudarg[1])/2)/int(baudarg[1]);
    else:
      baudarg = param_arg;
      if not re.match(r'^\d+$',baudarg):
        raise SSBCCException('baudmethod doesn\'t accept parameters yet');
      self.baudmethod = int(baudarg);
    print baudarg;

  def GenAssembly(self,config):
    pass;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    pass;
