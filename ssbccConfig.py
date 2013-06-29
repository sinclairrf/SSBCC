################################################################################
#
# Copyright 2012-2013, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math
import os
import re
import sys

from ssbccUtil import *

class SSBCCconfig():
  """
  Container for ssbcc configuration commands, the associated parsing, and
  program generation.
  """

  def __init__(self):
    """
    Initialize the empty dictionaries holding the processor configuration
    parameters.  Initialize the paths to search for peripherals.
    """
    self.config         = dict();               # various settings, etc.
    self.constants      = dict();               # CONSTANTs
    self.functions      = dict();               # list of functions to define
    self.inports        = list();               # INPORT definitions
    self.ios            = list();               # List of I/Os
    self.outports       = list();               # OUTPORT definitions
    self.parameters     = list();               # PARAMETERs and LOCALPARAMs
    self.peripheral     = list();               # PERIPHERALs
    self.signals        = list();               # internal signals
    self.symbols        = list();               # constant, I/O, inport, etc.  names

    # list of memories
    self.memories = dict(name=list(), type=list(), maxLength=list());

    # initial search paths for peripherals
    self.peripheralpaths= list();
    self.peripheralpaths.append('.');
    self.peripheralpaths.append('peripherals');
    self.peripheralpaths.append(os.path.join(sys.path[0],'core/peripherals'));

  def AddConstant(self,name,value,ixLine):
    """
    Add the constant for the "CONSTANT" configuration command to the "constants"
    dictionary.\n
    name        symbol for the constant
    value       value of the constant
    ixLine      line number in the architecture file for error messages
    """
    if name in self.constants:
      raise SSBCCException('CONSTANT "%s" already declared at line %d' % (name,ixLine,));
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined' % name);
    self.constants[name] = value;
    self.symbols.append(name);

  def AddIO(self,name,nBits,iotype,ixLine):
    """
    Add an I/O signal to the processor interface to the system.\n
    name        name of the I/O signal
    nBits       number of bits in the I/O signal
    iotype      signal direction:  "input", "output", or "inout"
    """
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined at line %d' % (name,ixLine,));
    self.ios.append((name,nBits,iotype,));
    self.symbols.append(name);

  def AddInport(self,port,ixLine):
    """
    Add an INPORT symbol to the processor.\n
    port        name of the INPORT symbol
    ixLine      line number in the architecture file for error messages
    """
    name = port[0];
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.inports.append(port);
    self.symbols.append(name);

  def AddMemory(self,cmd,ixLine):
    """
    Add a memory to the list of memories.\n
    cmd         3-element list as follows:
                [0] ==> type:  "RAM" or "ROM"
                [1] ==> memory name
                [2] ==> memory length (must be a power of 2)
    ixLine      line number in the architecture file for error messages
    """
    self.memories['type'].append(cmd[0]);
    self.memories['name'].append(cmd[1]);
    maxLength = eval(cmd[2]);
    if not IsPowerOf2(maxLength):
      raise SSBCCException('Memory length must be a power of 2, not "%s", at line %d' % (cmd[2],ixLine,));
    self.memories['maxLength'].append(eval(cmd[2]));

  def AddOutport(self,port,ixLine):
    """
    Add an OUTPORT symbol to the processor.\n
    port        name of the INPORT symbol
    ixLine      line number in the architecture file for error messages
    """
    name = port[0];
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.outports.append(port);
    self.symbols.append(name);

  def AddParameter(self,name,value,ixLine):
    """
    Add a PARAMETER to the processor.\n
    name        name of the PARAMETER
    value       value of the PARAMETER
    ixLine      line number in the architecture file for error messages
    """
    if not re.match(r'[LG]_\w+$',name):
      raise Exception('Program Bug -- bad parameter name at line %d' % ixLine);
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.parameters.append((name,value,));
    self.symbols.append(name);

  def AddSignal(self,name,nBits,ixLine):
    """
    Add a signal without an initial value to the processor.\n
    name        name of the signal
    nBits       number of bits in the signal
    ixLine      line number in the architecture file for error messages
    """
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.signals.append((name,nBits,));
    self.symbols.append(name);

  def AddSignalWithInit(self,name,nBits,init,ixLine):
    """
    Add a signal with an initial/reset value to the processor.\n
    name        name of the signal
    nBits       number of bits in the signal
    init        initial/reset value of the signal
    ixLine      line number in the architecture file for error messages
    """
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.signals.append((name,nBits,init,));
    self.symbols.append(name);

  def CompleteCombines(self):
    """
    Ensure all memories are assigned addresses.\n
    The return value is a list of dictionaries, each of which defines a single
    isolated or combined memory.  Each dictionary has the following entries:\n
      packing   a list of the combined memories as per PackCombinedMemory
      width     bit width of the memory
      ixMemory  if a MEMORY is included in the packing, this optional parameter
                is a unique integer used to generate the name of the memory.
    """
    # Create singleton entries for memory types and memories that aren't already listed in 'combine'.
    if not self.Exists('combine'):
      self.config['combine'] = dict(mems=[], memArch=[]);
    if not self.IsCombined('INSTRUCTION'):
      self.config['combine']['mems'].append(['INSTRUCTION']);
      self.config['combine']['memArch'].append('sync');
    for memType in ('DATA_STACK','RETURN_STACK',):
      if not self.IsCombined(memType):
        self.config['combine']['mems'].append([memType]);
        self.config['combine']['memArch'].append('LUT');
    for memName in self.memories['name']:
      if not self.IsCombined(memName):
        self.config['combine']['mems'].append([memName]);
        self.config['combine']['memArch'].append('LUT');
    # Create the addresses for all combined memories.
    self.config['combine']['packed'] = list();
    ixMemory = 0;
    for ixCombine in range(len(self.config['combine']['mems'])):
      thisMemList = self.config['combine']['mems'][ixCombine];
      thisPacked = self.PackCombinedMemory(thisMemList);
      if thisPacked['packing'][0]['name'] in self.memories['name']:
        thisPacked['ixMemory'] = ixMemory;
        ixMemory = ixMemory + 1;
      thisPacked['memArch'] = self.config['combine']['memArch'][ixCombine];
      self.config['combine']['packed'].append(thisPacked);

  def Exists(self,name):
    """
    Return true if the requested attribute has been created in the ssbccConfig
    object.
    """
    return name in self.config;

  def Get(self,name):
    """
    Return the requested attribute from the ssbccConfig object.
    """
    if not self.Exists(name):
      raise Exception('Program Bug:  "%s" not found in config' % name);
    return self.config[name];

  def GetMemoryByBank(self,ixBank):
    """
    Return the parameters for a memory by its bank address.\n
    ixBank      index of the requested memory bank
    """
    if not 'bank' in self.memories:
      return None;
    if ixBank not in self.memories['bank']:
      return None;
    ixMem = self.memories['bank'].index(ixBank);
    return self.GetMemoryParameters(ixMem);

  def GetMemoryByName(self,name):
    """
    Return the parameters for a memory by its name.\n
    name        name of the requested memory
    """
    if not name in self.memories['name']:
      return None;
    ixMem = self.memories['name'].index(name);
    return self.GetMemoryParameters(ixMem);

  def GetMemoryParameters(self,rawIndex):
    """
    Return the parameters for a memory by its index in the list of memories.\n
    rawIndex    index within the list of memories
    """
    if type(rawIndex) == str:
      if not self.IsMemory(rawIndex):
        raise Exception('Program Bug:  reference to non-existent memory');
      ix = self.memories['name'].index(rawIndex);
    elif type(rawIndex) == int:
      if (rawIndex < 0) or (rawIndex >= len(self.memories['name'])):
        raise Exception('Program Bug:  bad memory index %d' % rawIndex);
      ix = rawIndex;
    else:
      raise Exception('Program Bug:  unrecognized index type "%s"' % type(rawIndex));
    outvalue = dict();
    outvalue['index'] = ix;
    for field in self.memories:
      outvalue[field] = self.memories[field][ix];
    return outvalue;

  def GetPackedAndPacking(self,name):
    """
    Get the memory packing for the provided memory.
    """
    mems = self.config['combine']['mems'];
    ixCombine = [ix for ix in range(len(mems)) if name in mems[ix]];
    if len(ixCombine) == 0:
      raise Exception('Program Bug -- %s not found in combined memories' % name);
    if len(ixCombine) > 1:
      raise Exception('Program Bug == %s occurs too many times in combined memories' % name);
    ixCombine = ixCombine[0];
    ix = mems[ixCombine].index(name);
    thisPacked = self.config['combine']['packed'][ixCombine];
    return (thisPacked,thisPacked['packing'][ix],);

  def InsertPeripheralPath(self,path):
    """
    Add the specified path to the beginning of the paths to search for
    peripherals.\n
    path        path to add to the list
    """
    self.peripheralpaths.insert(-1,path);

  def IsCombined(self,name):
    """
    Indicate whether or not the specified memory type has already been listed
    in a "COMBINE" configuration command.  The memory type should be one of
    DATA_STACK, INSTRUCTION, or RETURN_STACK.\n
    name        name of the specified memory type\n
    """
    if not self.Exists('combine'):
      return False;
    mems = self.config['combine']['mems'];
    for ix in range(len(mems)):
      if name in mems[ix]:
        return True;
    return False;

  def IsMemory(self,name):
    """
    Indicate whether or not the specified symbol is the name of a memory.
    """
    return (name in self.memories['name']);

  def IsParameter(self,name):
    """
    Indicate whether or not the specified symbol is  the name of a parameter.
    """
    if re.match(r'[GL]_\w+',name) and name in self.symbols:
      return True;
    else:
      return False;

  def IsSymbol(self,name):
    """
    Indicate whether or not the specified name is a symbol.
    """
    return (name in self.symbols);

  def MemoryNameLengthList(self):
    """
    Return a list of tuples where each tuple is the name of a memory and its
    length.
    """
    outlist = list();
    for ix in range(len(self.memories['name'])):
      outlist.append((self.memories['name'][ix],self.memories['maxLength'][ix],));
    return outlist;

  def NInports(self):
    """
    Return the number of INPORTS.
    """
    return len(self.inports);

  def NMemories(self):
    """
    Return the number of memories.
    """
    return len(self.memories['name']);

  def NOutports(self):
    """
    Return the number of OUTPORTS.
    """
    return len(self.outports);

  def OverrideParameter(self,name,value):
    """
    Change the value of the specified parameter (based on the command line
    argument instead of the architecture file).\n
    name        name of the parameter to change
    value       new value of the parameter
    """
    for ix in range(len(self.parameters)):
      if self.parameters[ix][0] == name:
        break;
    else:
      raise SSBCCException('Command-line parameter or localparam "%s" not specified in the architecture file' % name);
    self.parameters[ix] = (name,value,);

  def PackCombinedMemory(self,memlist):
    """
    Utility function for CompleteCombines.\n
    Pack the memories being combined in as little address space as possible.
    This is done by recursively combining the two smallest memories or smallest
    combinations of memories until everything is combined.  This tree of memory
    lengths is then divided into leaves with the following parameters:\n
      lane      start bit (for when memories are packed in parallel)
      length    number of elements in the memory based on the declared memory
                size
                Note:  This is based on the number of addresses required for
                       each memory entry (see ratio).
      name      memory name
      offset    start address of the memory in the packing
      occupy    number of memory addresses allocated for the memory based on
                the packing
                Note:  This will be larger than length when a small memory is
                       in the same branch as a larger memory.
      nbits     width of the memory type
      ratio     number of base memory entries required to extract the number of
                bits required for the memory type
                Note:  This allows instruction addresses to occupy more than 1
                       memory address when the return stack is combined with
                       other memory addresses.\n
      width     base width of the containing memory
    Note:  If memories are being combined with the instructions space, they are
           always packed at the end of the instruction space, so the
           instruction space allocation is not included in the packing.
    """
    # Create a list of the memories being combined.
    entries = [];
    nSinglePort = 0;
    nDualPort = 0;
    for memName in memlist:
      if memName == 'INSTRUCTION':
        entries.append(dict(length=self.Get('nInstructions')['length'], name=memName, nbits=9, ratio=1, width=9));
        nSinglePort += 1;
      elif memName == 'DATA_STACK':
        entries.append(dict(length=self.Get('data_stack'), name=memName, nbits=self.Get('data_width'), ratio=1, width=self.Get('data_width')));
        nSinglePort += 1;
      elif memName == 'RETURN_STACK':
        # Return stack must hold data as well as addresses and each entry may
        # need to cross multiple addresses.
        # Note:  Combines with the return stack should only occur on block
        #        RAMs, not with distributed RAMs.
        nbits = max(self.Get('data_width'),self.Get('nInstructions')['nbits']);
        if len(memlist) == 1:
          ratio = 1;
          width=nbits;
        else:
          width = self.Get('sram_width');
          ratio = CeilPow2((nbits+width-1)/width);
        entries.append(dict(length=ratio*self.Get('return_stack'), name=memName, nbits=nbits, ratio=ratio, width=width));
        nSinglePort += 1;
      else:
        thisMemory = self.GetMemoryParameters(memName);
        entries.append(dict(length=CeilPow2(thisMemory['maxLength']), name=memName, nbits=self.Get('data_width'), ratio=1, width=self.Get('data_width')));
        nDualPort += 1;
    if ('INSTRUCTION' in memlist) and (len(memlist)>1):
      entries[0]['length'] -= sum(e['length'] for e in entries[1:]);
      if entries[0]['length'] <= 0:
        raise SSBCCException('INSTRUCTION length too small for "COMBINE INSTRUCTION,%s"' % entries[1]['name']);
    # Pack the single-port memories sequentially and the dual-port memories in parallel.
    if nSinglePort and nDualPort:
      raise Exception('Program Bug -- should have precluded mixed memory types earlier');
    if nSinglePort != 0:
      packingMode = 'sequential';
      width = max(e['width'] for e in entries);
      if 'INSTRUCTION' in memlist:
        for e in entries:
          e['occupy'] = e['length'];
      else:
        occupy = max(e['length'] for e in entries);
        for e in entries:
          e['occupy'] = occupy;
      offset = 0;
      for e in entries:
        e['lane'] = 0;
        e['offset'] = offset;
        offset += e['occupy'];
      length = sum(e['occupy'] for e in entries);
    else:
      packingMode = 'parallel';
      length = max(e['length'] for e in entries);
      width = sum(e['width'] for e in entries);
      lane = 0;
      for e in entries:
        e['occupy'] = length;
        e['lane'] = lane;
        lane += self.Get('data_width');
        e['offset'] = 0;
    # Construct the return container.
    retval = dict(length=length, width=width, packing=entries, packingMode=packingMode);
    return retval;

  def ProcessCombine(self,ixLine,line):
    """
    Parse the "COMBINE" configuration command as follows:\n
    Validate the arguments to the "COMBINE" configuration command and append
    the list of combined memories and the associated arguments to "combine"
    property.\n
    The argument consists of one of the following:
      INSTRUCTION,DATA_STACK
      INSTRUCTION,RETURN_STACK
      DATA_STACK,RETURN_STACK
      DATA_STACK
      RETURN_STACK
      mem_name[,mem_name]*
    """
    # Perform some syntax checking and get the list of memories to combine.
    cmd = re.findall(r'\s*COMBINE\s+(\S+)\s*$',line);
    if not cmd:
      raise SSBCCException('Malformed COMBINE configuration command on line %d' % ixLine);
    mems = re.split(r',',cmd[0]);
    if (len(mems)==1) and ('INSTRUCTION' in mems):
      raise SSBCCException('"COMBINE INSTRUCTION" doesn\'t make sense at line %d' % ixLine);
    if ('INSTRUCTION' in mems) and (mems[0] != 'INSTRUCTION'):
      raise SSBCCException('"INSTRUCTION" must be listed first in COMBINE configuration command at line %d' % ixLine);
    recognized = ['INSTRUCTION','DATA_STACK','RETURN_STACK'] + self.memories['name'];
    unrecognized = [memName for memName in mems if memName not in recognized];
    if unrecognized:
      raise SSBCCException('"%s" not recognized in COMBINE configuration command at line %d' % (unrecognized[0],ixLine,));
    alreadyUsed = [memName for memName in mems if self.IsCombined(memName)];
    if alreadyUsed:
      raise SSBCCException('"%s" already used in COMBINE configuration command before line %d' % (alreadyUsed[0],ixLine,));
    repeated = [mems[ix] for ix in range(len(mems)-1) if mems[ix] in mems[ix+1]];
    if repeated:
      raise SSBCCException('"%s" repeated in COMBINE configuration command on line %d' % (repeated[0],ixLine,));
    # Count the number of the different memory types being combined and validate the combination.
    nSinglePort = sum([thisMemName in ('INSTRUCTION','DATA_STACK','RETURN_STACK',) for thisMemName in mems]);
    nDualPort = len(mems) - nSinglePort;
    if nSinglePort and nDualPort:
      raise SSBCCException('Prohibited combination of memory types in COMBINE configuration command at line %d' % ixLine);
    if nSinglePort > 2:
      raise SSBCCException('Too many single-port memory types in COMBINE configuration command at line %d' % ixLine);
    # Append the listed memory types to the list of combined memories.
    if not self.Exists('combine'):
      self.config['combine'] = dict(mems=[], memArch=[]);
    self.config['combine']['mems'].append(mems);
    self.config['combine']['memArch'].append('sync');

  def ProcessInport(self,ixLine,line):
    """
    Parse the "INPORT" configuration commands as follows:
      The configuration command is well formatted.
      The number of signals matches the corresponding list of signal declarations.
      The port name starts with 'I_'.
      The signal declarations are valid.
        n-bit where n is an integer
        set-reset
        strobe
      That no other signals are specified in conjunction with a "set-reset" signal.
      The total input data with does not exceed the maximum data width.\n
    The input port is appended to the list of inputs as a tuple.  The first
    entry in the tuple is the port name.  The subsequent entries are tuples
    consisting of the following:
      signal name
      signal width
      signal type
    """
    cmd = re.findall(r'\s*INPORT\s+(\S+)\s+(\S+)\s+(I_\w+)\s*$',line);
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
        thisNBits = int(modes[ix][0:-4]);
        self.AddIO(names[ix],thisNBits,'input',ixLine);
        thisPort += ((names[ix],thisNBits,'data',),);
        nBits = nBits + thisNBits;
      elif modes[ix] == 'set-reset':
        has__set_reset = True;
        self.AddIO(names[ix],1,'input',ixLine);
        thisPort += ((names[ix],1,'set-reset',),);
        self.AddSignal('s_SETRESET_%s' % names[ix],1,ixLine);
      elif modes[ix] == 'strobe':
        self.AddIO(names[ix],1,'output',ixLine);
        thisPort += ((names[ix],1,'strobe',),);
      else:
        raise SSBCCException('Unrecognized INPORT signal type "%s"' % modes[ix]);
      if has__set_reset and len(names) > 1:
        raise SSBCCException('set-reset cannot be simultaneous with other signals in "%s"' % line[:-1]);
      if nBits > self.Get('data_width'):
        raise SSBCCException('Signal width too wide in "%s"' % line[:-1]);
    self.AddInport(thisPort,ixLine);

  def ProcessOutport(self,line,ixLine):
    """
    Parse the "OUTPORT" configuration commands as follows:
      The configuration command is well formatted.
      The number of signals matches the corresponding list of signal declarations.
      The port name starts with 'O_'.
      The signal declarations are valid.
        n-bit[=value]
        strobe
      The total output data with does not exceed the maximum data width.\n
    The output port is appended to the list of outports as a tuple.  The first
    entry in this tuple is the port name.  The subsequent entries are tuples
    consisting of the following:
      signal name
      signal width
      signal type
      initial value (optional)
    """
    cmd = re.findall(r'^\s*OUTPORT\s+(\S+)\s+(\S+)\s+(O_\w+)\s*$',line);
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
        self.AddIO(names[ix],thisNBits,'output',ixLine);
        if a.group(2):
          thisPort += ((names[ix],thisNBits,'data',a.group(2)[1:],),);
        else:
          thisPort += ((names[ix],thisNBits,'data',),);
        nBits = nBits + thisNBits;
        self.config['haveBitOutportSignals'] = 'True';
      elif modes[ix] == 'strobe':
        self.AddIO(names[ix],1,'output',ixLine);
        thisPort += ((names[ix],1,'strobe',),);
      else:
        raise SSBCCException('Unrecognized OUTPORT signal type on line %d: "%s"' % (ixLine,modes[ix],));
      if nBits > 8:
        raise SSBCCException('Signal width too wide on line %d:  in "%s"' % (ixLine,line[:-1],));
    self.AddOutport(thisPort,ixLine);

  def ProcessPeripheral(self,ixLine,line):
    """
    Process the "PERIPHERAL" configuration command as follows:
      Validate the format of the configuration command.
      Find the peripheral in the candidate list of paths for peripherals.
      Execute the file declaring the peripheral.
        Note:  This is done since I couldn't find a way to "import" the
               peripheral.  Executing the peripheral makes its definition local
               to this invokation of the ProcessPeripheral function, but the
               object subsequently created retains the required functionality
               to instantiate the peripheral
      Go through the parameters for the peripheral and do the following for each:
        If the argument for the peripheral is the string "help", then print the
          docstring for the peripheral and exit.
        Append the parameter name and its argument to the list of parameters
          (use "None" as the argument if no argument was provided).
      Append the instantiated peripheral to the list of peripherals.
        Note:  The "exec" function dynamically executes the instruction to
               instantiate the peripheral and append it to the list of
               peripherals.
    """
    # Validate the format of the peripheral configuration command and the the name of the peripheral.
    cmd = re.findall(r'\s*PERIPHERAL\s+(\w+)\s*(.*)$',line);
    if not cmd:
      raise SSBCCException('Missing peripheral name in line %d:  %s' % (ixLine,line[:-1],));
    peripheral = cmd[0][0];
    # Find and execute the peripheral Python script.
    # Note:  Because "execfile" and "exec" method are used to load the
    #        peripheral python script, the __file__ object is set to be this
    #        file, not the peripheral source file.
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
    exec('self.peripheral.append(%s(fullperipheral,self,param_list,ixLine));' % peripheral);

  def Set(self,name,value):
    """
    Create or override the specified attribute in the ssbccConfig object.
    """
    self.config[name] = value;

  def SetMemoryBlock(self,name,value,errorInfo):
    """
    Set an attribute in the ssbccConfig object for the specified memory with
    the specified memory architecture.\n
    "value" must be a string with the format "\d+" or "\d+*\d+" where "\d+" is
    an integer.  The first format specifies a single memory with the stated
    size and the size must be a power of two.  The second format specified
    allocation of multiple memory blocks where the size is given by the first
    integer and must be a power of 2 and the number of blocks is given by the
    second integer and doesn't need to be a power of 2.
    """
    findStar = value.find('*');
    if findStar == -1:
      blockSize = int(value);
      nBlocks = 1;
    else:
      blockSize = int(value[0:findStar]);
      nBlocks = int(value[findStar+1:]);
    nbits_blockSize = int(round(math.log(blockSize,2)));
    if blockSize != 2**nbits_blockSize:
      raise SSBCCException('block size must be a power of 2 on line %d: "%s"' % errorInfo);
    nbits_nBlocks = CeilLog2(nBlocks);
    self.Set(name, dict(
                   length=blockSize*nBlocks,
                   nbits=nbits_blockSize+nbits_nBlocks,
                   blockSize=blockSize,
                   nbits_blockSize=nbits_blockSize,
                   nBlocks=nBlocks,
                   nbits_nBlocks=nbits_nBlocks));

  def SetMemoryParameters(self,memParam,values):
    """
    Record the body of the specified memory based on the assembler output.
    """
    index = memParam['index'];
    for field in values:
      if field not in self.memories:
        self.memories[field] = list();
        for ix in range(len(self.memories['name'])):
          self.memories[field].append(None);
      self.memories[field][index] = values[field];
