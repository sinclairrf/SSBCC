################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math
import os
import re
import sys

from ssbccUtil import SSBCCException

class SSBCCconfig():
  """Container for ssbcc configuration commands, the associated parsing, and program generation"""

  def __init__(self):
    self.config         = dict();               # various settings, etc.
    self.constants      = dict();               # CONSTANTs
    self.functions      = dict();               # list of functions to define
    self.inports        = list();               # INPORT definitions
    self.ios            = list();               # List of I/Os
    self.outports       = list();               # OUTPORT definitions
    self.parameters     = list();               # PARAMETERs
    self.peripheral     = list();               # PERIPHERALs
    self.signals        = list();               # internal signals
    self.symbols        = list();               # constant, I/O, inport, etc.  names

    # initial search paths for peripherals
    self.peripheralpaths= list();
    self.peripheralpaths.append('.');
    self.peripheralpaths.append('peripherals');
    self.peripheralpaths.append(os.path.join(sys.path[0],'core/peripherals'));

  def AddConstant(self,name,value,ixLine):
    if name in self.constants:
      raise SSBCCException('CONSTANT "%s" already declared at line %d' % (name,ixLine,));
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.constants[name] = value;
    self.symbols.append(name);

  def AddIO(self,name,nBits,iotype):
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.ios.append((name,nBits,iotype,));
    self.symbols.append(name);

  def AddInport(self,port):
    name = port[0];
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.inports.append(port);
    self.symbols.append(name);

  def AddOutport(self,port):
    name = port[0];
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.outports.append(port);
    self.symbols.append(name);

  def AddParameter(self,name,value):
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.parameters.append((name,value,));
    self.symbols.append(name);

  def AddSignal(self,name,nBits):
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.signals.append((name,nBits,));
    self.symbols.append(name);

  def AddSignalWithInit(self,name,nBits,init):
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.signals.append((name,nBits,init,));
    self.symbols.append(name);

  def Exists(self,name):
    return name in self.config;

  def Get(self,name):
    if name not in self.config:
      raise Exception('Program Bug:  "%s" not found in config' % name);
    return self.config[name];

  def InsertPeripheralPath(self,path):
    self.peripheralpaths.insert(-1,path);

  def OverrideParameter(self,name,value):
    for ix in range(len(self.parameters)):
      if self.parameters[ix][0] == name:
        break;
    else:
      raise SSBCCException('Command-line parameter "%s" must be specified in the architecture file' % name);
    self.parameters[ix] = (name,value,);

  def ProcessInport(self,ixLine,line):
    cmd = re.findall(r'\s*INPORT\s+(\S+)\s+(\S+)\s+(\w+)',line);
    modes = re.findall(r'([^,]+)',cmd[0][0]);
    names = re.findall(r'([^,]+)',cmd[0][1]);
    portName = cmd[0][2];
    if len(modes) != len(names):
      raise SSBCCException('Malformed INPORT configuration command -- number of options don\'t match on line %d: "%s"' % (ixLine,line[:-1],));
    # Append the input signal names, mode, and bit-width to the list of I/Os.
    has__set_reset = False;
    nBits = 0;
    thisPort = (portName,);
    for ix in range(len(names)):
      if re.match(r'^\d+-bit$',modes[ix]):
        # TODO -- parse more than one digit in \d+-bit
        thisNBits = int(modes[ix][0]);
        self.AddIO(names[ix],thisNBits,'input');
        thisPort += ((names[ix],thisNBits,'data',),);
        nBits = nBits + thisNBits;
      elif modes[ix] == 'set-reset':
        has__set_reset = True;
        self.AddIO(names[ix],1,'input');
        thisPort += ((names[ix],1,'set-reset',),);
        self.AddSignal('s_SETRESET_%s' % names[ix],1);
      elif modes[ix] == 'strobe':
        self.AddIO(names[ix],1,'output');
        thisPort += ((names[ix],1,'strobe',),);
      else:
        raise SSBCCException('Unrecognized INPORT signal type "%s"' % modes[ix]);
      if has__set_reset and len(names) > 1:
        raise SSBCCException('set-reset cannot be simultaneous with other signals in "%s"' % line[:-1]);
      if nBits > 8:
        raise SSBCCException('Signal width too wide in "%s"' % line[:-1]);
    self.AddInport(thisPort);

  def ProcessOutport(self,line,ixLine):
    cmd = re.findall(r'^\s*OUTPORT\s+(\S+)\s+(\S+)\s+(\w+)\s*$',line);
    if not cmd:
      raise SSBCCException('Malformed OUTPUT configuration command on line %d: "%s"' % (ixLine,line[:-1],));
    modes = re.findall(r'([^,]+)',cmd[0][0]);
    names = re.findall(r'([^,]+)',cmd[0][1]);
    portName = cmd[0][2];
    if len(modes) != len(names):
      raise SSBCCException('Malformed OUTPORT configuration command -- number of widths/types and signal names don\'t match on line %d: "%s"' % (ixLine,line[:-1],));
    # Append the input signal names, mode, and bit-width to the list of I/Os.
    nBits = 0;
    thisPort = (portName,);
    for ix in range(len(names)):
      if re.match(r'\d+-bit',modes[ix]):
        a = re.match(r'(\d+)-bit(=\S+)?$',modes[ix]);
        if not a:
          raise SSBCCException('Malformed bitwith/bitwidth=initialization on line %d:  "%s"' % (ixLine,modes[ix],));
        thisNBits = int(a.group(1));
        self.AddIO(names[ix],thisNBits,'output');
        if a.group(2):
          thisPort += ((names[ix],thisNBits,'data',a.group(2)[1:],),);
        else:
          thisPort += ((names[ix],thisNBits,'data',),);
        nBits = nBits + thisNBits;
        self.config['haveBitOutportSignals'] = 'True';
      elif modes[ix] == 'strobe':
        self.AddIO(names[ix],1,'output');
        thisPort += ((names[ix],1,'strobe',),);
      else:
        raise SSBCCException('Unrecognized OUTPORT signal type on line %d: "%s"' % (ixLine,modes[ix],));
      if nBits > 8:
        raise SSBCCException('Signal width too wide on line %d:  in "%s"' % (ixLine,line[:-1],));
    self.AddOutport(thisPort);

  def ProcessPeripheral(self,ixLine,line):
    # Validate the format of the peripheral configuration command and the the name of the peripheral.
    cmd = re.findall(r'\s*PERIPHERAL\s+(\w+)\s*(.*)',line);
    if not cmd:
      raise SSBCCException('Missing peripheral name in line %d:  %s' % (ixLine,line[:-1],));
    peripheral = cmd[0][0];
    # Find and execute the peripheral Python script.
    for testPath in self.peripheralpaths:
      fullperipheral = os.path.join(testPath,'%s.py' % peripheral);
      if os.path.isfile(fullperipheral):
        break;
    else:
      raise SSBCCException('Peripheral "%s" not found' % peripheral);
    execfile(fullperipheral);
    # Convert the space delimited parameters to a list of tuples.
    param_list = list();
    for param_string in re.findall(r'(\w+="[^"]*"|\w+=\S+|\w+)\s*',cmd[0][1]):
      if param_string == "help":
        exec('helpmsg = %s.__doc__' % peripheral);
        if not helpmsg:
          raise SSBCCException('No help for peripheral %s is provided' % fullperipheral);
        print;
        print 'Help message for peripheral:  %s' % peripheral;
        print 'Located at:  %s' % fullperipheral;
        print;
        print helpmsg;
        raise SSBCCException('Terminated by "help" for peripheral %s' % peripheral);
      ix = param_string.find('=');
      if param_string.find('="') > 0:
        param_list.append((param_string[:ix],param_string[ix+2:-1],));
      elif param_string.find('=') > 0:
        param_list.append((param_string[:ix],param_string[ix+1:],));
      else:
        param_list.append((param_string,None));
    # Add the peripheral to the micro controller configuration.
    exec('self.peripheral.append(%s(self,param_list,ixLine));' % peripheral);

  def Set(self,name,value):
    self.config[name] = value;
