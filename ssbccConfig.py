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
    dictionary.

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
    Add an I/O signal to the processor interface to the system.

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
    Add an INPORT symbol to the processor.

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
    Add a memory to the list of memories.

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
    Add an OUTPORT symbol to the processor.

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
    Add a PARAMETER to the processor.

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
    Add a signal without an initial value to the processor.

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
    Add a signal with an initial/reset value to the processor.

    name        name of the signal
    nBits       number of bits in the signal
    init        initial/reset value of the signal
    ixLine      line number in the architecture file for error messages
    """
    if name in self.symbols:
      raise SSBCCException('Symbol "%s" already defined before line %d' % (name,ixLine,));
    self.signals.append((name,nBits,init,));
    self.symbols.append(name);

  # TODO -- remove this method?
  def CombinedComplementaryArg(self,name):
    if not self.IsCombined(name):
      raise Exception('Program bug');
    mems = self.config['combine']['mems'];
    for ixCombine in range(len(mems)):
      if name in mems[ixCombine]:
        if len(mems[ixCombine]) == 1:
          raise Exception('Program bug');
        ixName = mems[ixCombine].index(name);
        return self.config['combine']['args'][ixCombine][1-ixName];
    raise Exception('Program bug');

  def CompleteCombines(self):
    """
    Ensure all memories are assigned addresses.

    The return value is a list of dictionaries, each of which defines a single
    isolated or combined memory.  Each dictionary has the following entries:

      packing   a list of the combined memories as per PackCombinedMemory
      width     bit width of the memory
      ixMemory  if a MEMORY is included in the packing, this optional parameter
                is a unique integer used to generate the name of the memory.
    """
    # Create singleton entries for memory types and memories that aren't already listed in 'combine'.
    if not self.Exists('combine'):
      self.config['combine'] = dict(mems=[], args=[]);
    if not self.IsCombined('INSTRUCTION'):
      self.config['combine']['mems'].append(['INSTRUCTION']);
      self.config['combine']['args'].append([dict(length=self.Get('nInstructions')['length'])]);
    if not self.IsCombined('DATA_STACK'):
      self.config['combine']['mems'].append(['DATA_STACK']);
      self.config['combine']['args'].append([dict(length=self.Get('data_stack'))]);
    if not self.IsCombined('RETURN_STACK'):
      self.config['combine']['mems'].append(['RETURN_STACK']);
      self.config['combine']['args'].append([dict(length=self.Get('return_stack'))]);
    for memName in self.memories['name']:
      if not self.IsCombinedMemory(memName):
        self.config['combine']['mems'].append(['MEMORY']);
        self.config['combine']['args'].append([dict(memlist=[memName])]);
    # Create the addresses for all combined memories.
    self.config['combine']['packed'] = [];
    ixMemory = 0;
    for ixCombine in range(len(self.config['combine']['mems'])):
      thisMem = self.config['combine']['mems'][ixCombine];
      hasInstructions = False;
      thisMemList = [];
      for ixMemEntry in range(len(thisMem)):
        thisMemEntry = thisMem[ixMemEntry];
        if thisMemEntry == 'INSTRUCTION':
          thisMemList.append('_instructions');
          hasInstructions = True;
        elif thisMemEntry == 'DATA_STACK':
          thisMemList.append('_data_stack');
        elif thisMemEntry == 'RETURN_STACK':
          thisMemList.append('_return_stack');
        elif thisMemEntry == 'MEMORY':
          for memName in self.config['combine']['args'][ixCombine][ixMemEntry]['memlist']:
            thisMemList.append(memName);
        else:
          raise Exception('Program bug');
      thisPacked = self.PackCombinedMemory(thisMemList);
      if hasInstructions:
        instructionLength = self.Get('nInstructions')['length'];
        if len(thisMemList) > 1:
          if thisPacked['length'] >= self.Get('nInstructions')['blockSize']:
            raise SSBCCException('Second argument of "COMBINE INSTRUCTION,..." configuration command exceeds instruction block size');
          instructionLength = instructionLength - thisPacked['length'];
          thisPacked['length'] = self.Get('nInstructions')['length'];
          self.Get('nInstructions')['length'] = instructionLength;
        eInstructions = dict(length=instructionLength, name='_instructions', offset=0, occupy=instructionLength, width=9, ratio=1);
        for e in thisPacked['packing']:
          e['offset'] = e['offset'] + instructionLength;
        thisPacked['packing'].insert(0,eInstructions);
      if len(thisPacked['packing']) == 0:
        raise Exception('Program Bug -- packing is empty');
      width = 0;
      for thisPacking in thisPacked['packing']:
        if thisPacking['ratio'] > 1:
          if self.Get('sram_width') > width:
            width = self.Get('sram_width');
        elif thisPacking['width'] > width:
          width = thisPacking['width'];
      thisPacked['width'] = width;
      if thisMem[0] == 'MEMORY':
        thisPacked['ixMemory'] = ixMemory;
        ixMemory = ixMemory + 1;
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
    Return the parameters for a memory by its bank address.

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
    Return the parameters for a memory by its name.

    name        name of the requested memory
    """
    if not name in self.memories['name']:
      return None;
    ixMem = self.memories['name'].index(name);
    return self.GetMemoryParameters(ixMem);

  def GetMemoryParameters(self,rawIndex):
    """
    Return the parameters for a memory by its index in the list of memories.

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

  def InsertPeripheralPath(self,path):
    """
    Add the specified path to the beginning of the paths to search for
    peripherals.

    path        path to add to the list
    """
    self.peripheralpaths.insert(-1,path);

  # TODO -- check use of this function and IsCombinedMemory
  def IsCombined(self,name):
    """
    Indicate whether or not the specified memory has already been listed in a
    "COMBINE" configuration command.

    name        name of the specified memory
    """
    if not self.Exists('combine'):
      return False;
    mems = self.config['combine']['mems'];
    for ix in range(len(mems)):
      if name in mems[ix]:
        return True;
    return False;

  # TODO -- add docstring after doing preceding "TODO"
  def IsCombinedMemory(self,name):
    if not self.Exists('combine'):
      return False;
    mems = self.config['combine']['mems'];
    for ixCombine in range(len(mems)):
      if 'MEMORY' not in mems[ixCombine]:
        continue;
      ixMemory = mems[ixCombine].index('MEMORY');
      tmpMem = self.config['combine']['args'][ixCombine][ixMemory];
      if 'memlist' not in tmpMem:
        continue;
      memlist = self.config['combine']['args'][ixCombine][ixMemory]['memlist'];
      if name in memlist:
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
    if re.match(r'G_\w+',name) and name in self.symbols:
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
    argument instead of the architecture file).

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
    Utility function for CompleteCombines.

    Pack the memories being combined in as little address space as possible.
    This is done by recursively combining the two smallest memories or smallest
    combinations of memories until everything is combined.  This tree of memory
    lengths is then divided into leaves with the following parameters:

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
      width     bit width of each memory entry
      ratio     number of addresses for each memory entry
                Note:  This allows instruction addresses to occupy more than 1
                       memory address when the return stack is combined with
                       other memory addresses.

    Note:  If memories are being combined with the instructions space, they are
           always packed at the end of the instruction space, so the
           instruction space allocation is not included in the packing.
    """
    entries = [];
    for memName in memlist:
      if memName == '_instructions':
        # Instruction block packing is done elsewhere.
        pass;
      elif memName == '_data_stack':
        entries.append(dict(length=self.Get('data_stack'), name=memName, width=self.Get('data_width'), ratio=1));
      elif memName == '_return_stack':
        # Return stack must hold data as well as addresses and each entry may
        # need to cross multiple addresses.
        # Note:  Combines with the return stack should only occur on block
        #        RAMs, not with distributed RAMs.
        nbits = max(self.Get('data_width'),self.Get('nInstructions')['nbits']);
        if len(memlist) == 1:
          ratio = 1;
        else:
          sram_width = self.Get('sram_width');
          ratio = CeilPow2((nbits+sram_width-1)/sram_width);
        entries.append(dict(length=ratio*self.Get('return_stack'), name=memName, width=nbits, ratio=ratio));
      else:
        thisMemories = self.GetMemoryParameters(memName);
        entries.append(dict(length=CeilPow2(thisMemories['maxLength']), name=memName, width=self.Get('data_width'), ratio=1));
    # If the list of memories to pack is empty, then return an empty packing.
    # This should only happen when the memlist is a singleton consisting of the
    # instructions.
    if len(entries) == 0:
      return dict(packing=[]);
    # Sort and coalesce the entries until the list is only one unit long.
    def sortfn(x):
      return x['length'];
    while len(entries) > 1:
      entries.sort(key=sortfn);
      # Coalesce the two smallest entries.
      [e0,e1] = entries[0:2];
      del entries[0:2];
      e0['offset'] = 0;
      e1['offset'] = e1['length'];
      entries.append(dict(length=CeilPow2(e0['length']+e1['length']), body=[e0, e1]));
    entries[0]['offset'] = 0;
    entries[0]['occupy'] = entries[0]['length'];
    # Extract the combined length.
    retval = dict(length=entries[0]['length']);
    # Convert the coalesced list into name, length, address segments.
    retval['packing'] = [];
    while len(entries) > 0:
      if 'name' in entries[0]:
        retval['packing'].append(entries[0]);
        del entries[0];
      else:
        [e0, e1] = entries[0]['body'];
        e0['offset'] = e0['offset'] + entries[0]['offset'];
        e1['offset'] = e1['offset'] + entries[0]['offset'];
        e0['occupy'] = e1['length'];
        e1['occupy'] = entries[0]['occupy']-e0['occupy'];
        del entries[0];
        entries.append(e0);
        entries.append(e1);
    # Sort by order of occurrence.
    retval['packing'].sort(None,lambda(x):x['offset']);
    return retval;

  def ProcessCombine(self,ixLine,line):
    """
    Parse the "COMBINE" configuration command as follows:

    Validate the arguments to the "COMBINE" configuration command and append
    the list of combined memories and the associated arguments to "combine"
    property.
    """
    cmd = re.findall(r'\s*COMBINE\s+(\S+)\s*(\S+)?\s*$',line);
    if not cmd:
      raise SSBCCException('Malformed "COMBINE" configuration command on line %d' % ixLine);
    cmd = list(cmd[0]);
    if re.match(r'^\s*MEMORY(\(\S+\))?\s*$',cmd[0]):
      mems = [ cmd[0] ];
    else:
      mems = re.findall(r'(\w+),(\S+)$',cmd[0]);
      if mems:
        mems = list(mems[0]);
    if not mems:
      raise SSBCCException('Malformed memory types "%s" in COMBINE configuration command at line %d' % (cmd[0],ixLine,));
    if len(mems) > 1 and mems[0] == mems[1]:
      raise SSBCCException('Memory types "%s" must be different in COMBINE configuration command at line %d' % (cmd[0],ixLine,));
    if self.Exists('combine'):
      for memtype in mems:
        if memtype in ['DATA_STACK', 'INSTRUCTION', 'RETURN_STACK']:
          if self.IsCombined(memtype):
            raise SSBCCException('Memory type "%s" already used in COMBINE configuration command at line %d' % (memtype,ixLine,));
    # Compare arguments to allowed values
    allows = ['DATA_STACK', 'INSTRUCTION', 'MEMORY(\(\S+\))?', 'RETURN_STACK'];
    for ix in range(len(allows)):
      if re.match(allows[ix]+'$',mems[0]):
        break;
    else:
      raise SSBCCException('Malformed memory type "%s" in COMBINE configuration command at line %d' % (mems[0],ixLine,));
    if mems[0] in ('DATA_STACK', 'INSTRUCTION', 'RETURN_STACK',):
      if mems[1] == '':
        raise SSBCCException('Second memory type missing in "COMBINE INSTRUCTION,..." at line %d' % ixLine);
      if mems[0] in allows:
        allows.remove(mems[0]);
      if 'INSTRUCTION' in allows:
        allows.remove('INSTRUCTION');
      for ix in range(len(allows)):
        if re.match(allows[ix]+'$',mems[1]):
          break;
      else:
        raise SSBCCException('Malformed second memory type "%s" in COMBINE configuration command at line %d' % (mems[1],ixLine,));
    elif re.match(r'MEMORY(\(\S+\))?$',mems[0]):
      if len(mems) > 1:
        raise SSBCCException('Second memory type not allowed after "COMBINE MEMORY(...)" configuration command at line %d', ixLine);
    else:
      raise Exception('Program Bug -- missing case for "%s"' % mems[0]);
    # Allocate space for argument descriptions.
    args = [ dict() ];
    if len(mems) > 1:
      args.append(dict());
    # Ensure listed memories exist (can only be in one of the two locations because of preceding test)
    for ixMem in range(len(mems)):
      if re.match(r'MEMORY$',mems[ixMem]):
        memlist = self.memories['name'];
      elif re.match(r'MEMORY\(\S+\)$',mems[ixMem]):
        memlist = re.split(r',',mems[ixMem][7:-1]);
        if not memlist:
          raise SSBCCException('Malformed memory list "%s" in COMBINE configuration command at line %d' % (memory,ixLine,));
        mems[ixMem] = 'MEMORY';
        for mem in memlist:
          if not self.IsMemory(mem):
            raise SSBCCException('Memory "%s" not found in COMBINE configuration command at line %d' % (mem,ixLine,));
      else:
        continue;
      # Ensure each memory is only combined once.
      if self.Exists('combine'):
        for ixCombine in range(len(self.config['combine']['mems'])):
          if 'MEMORY' in self.config['combine']['mems'][ixCombine]:
            ixMemOld = self.config['combine']['mems'][ixCombine].index('MEMORY');
            memListOld = self.config['combine']['args'][ixCombine][ixMemOld]['memlist'];
            for memName in memlist:
              if memName in memListOld:
                raise SSBCCException('Memory "%s" already used in previous "COMBINE" configuration command at line %d' % (memName,ixLine,));
      args[ixMem] = dict(memlist=memlist);
      entries = [];
      for memName in memlist:
        if not self.IsCombined(memName):
          thisMemories = self.GetMemoryParameters(memName);
          entries.append(dict(length=CeilPow2(thisMemories['maxLength']), name=memName));
    # Check for required INSTRUCTION length
    if mems[0] == 'INSTRUCTION':
      if self.Exists('nInstructions'):
        raise SSBCCException('Instruction memory size already specified before "COMBINE INSTRUCTION" at line %d' % ixLine);
      if not re.match(r'[1-9]\d*(\*[1-9]\d*)?$',cmd[1]):
        raise SSBCCException('Malformed length "%s" in configuration command at line %d' % (cmd[1],ixLine,));
      self.SetMemoryBlock('nInstructions',cmd[1],(ixLine,line[:-1],));
      cmd[1] = '';
    # Check for required RETURN_STACK architecture
    elif mems[0] == 'RETURN_STACK':
      if not self.Exists('nInstructions'):
        raise SSBCCException('INSTRUCTION space must be sized before "COMBINE RETURN_STACK,..." configuration command at line %d' % ixLine);
    # Ensure second parameter isn't provided in all other cases
    if cmd[1] != '':
      raise SSBCCException('Extra parameter "%s" in COMBINE configuration command at line %d' % (mems[1],ixLine,));
    # Append the parsed COMMAND configuration command to the associated dictionary
    if not self.Exists('combine'):
      self.config['combine'] = dict(mems=[], args=[]);
    self.config['combine']['mems'].append(mems);
    self.config['combine']['args'].append(args);

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
      The total input data with does not exceed the maximum data width.

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
      The total output data with does not exceed the maximum data width.

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
    the specified memory architecture.

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
