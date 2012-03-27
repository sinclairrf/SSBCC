################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Assembly language definitions for SSBCC 9x8.
#
################################################################################

class asmDef_9x8:
  """SSBCC 9x8 specific parsing"""

  ################################################################################
  #
  # External interface to the directives.
  #
  ################################################################################

  def IsDirective(self,name):
    return name in self.directives['list'];

  ################################################################################
  #
  # Configure the class for identifying and processing macros.
  #
  ################################################################################

  def AddMacro(self,name,macroLength,nArgs=1):
    self.macros['list'].append(name);
    self.macros['length'].append(macroLength);
    self.macros['nArgs'].append(nArgs);

  def IsMacro(self,name):
    return name in self.macros['list'];

  def MacroLength(self,name):
    if name not in self.macros['list']:
      raise Exception('Program Bug');
    ix = self.macros['list'].index(name);
    return self.macros['length'][ix];

  def MacroNumberArgs(self,name):
    if name not in self.macros['list']:
      raise Exception('Program bug' % name);
    ix = self.macros['list'].index(name);
    return self.macros['nArgs'][ix];

  ################################################################################
  #
  # Configure the class for processing instructions.
  #
  ################################################################################

  def AddInstruction(self,name,opcode):
    self.instructions['list'].append(name);
    self.instructions['opcode'].append(opcode);

  def IsInstruction(self,name):
    return name in self.instructions['list'];

  def InstructionOpcode(self,symbolName):
    if not self.IsInstruction(symbolName):
      raise Exception('Program Bug:  %s not in instruction list' % symbolName);
    ix = self.instructions['list'].index(symbolName);
    return self.instructions['opcode'][ix];

  ################################################################################
  #
  # Register input and output port names and addresses.
  #
  ################################################################################

  def IsInport(self,name):
    return name in self.inports;

  def IsOutport(self,name):
    return name in self.outports;

  def InportAddress(self,name):
    if not self.IsInport(name):
      raise Exception('Program Bug');
    return self.inports[name];

  def OutportAddress(self,name):
    if not self.IsOutport(name):
      raise Exception('Program Bug');
    return self.outports[name];

  def RegisterInport(self,name,address):
    if self.IsInport(name):
      raise Exception('Program Bug');
    self.inports[name] = address;

  def RegisterOutport(self,name,address):
    if self.IsOutport(name):
      raise Exception('Program Bug');
    self.outports[name] = address;

  ################################################################################
  #
  # Check a list of raw tokens to ensure their proper format.
  #
  ################################################################################

  def CheckRawTokens(self,filename,rawTokens):
    # Ensure the first token is a directive.
    firstToken = rawTokens[0];
    if firstToken['type'] != 'directive':
      raise Exception('Program Bug triggered by %s(%d), column %d' % (filename,firstToken['line'],firstToken['col']));
    # Ensure the main body ends in a ".jump".
    lastToken = rawTokens[-1];
    if firstToken['value'] == '.main':
      if (lastToken['type'] != 'macro') or (lastToken['value'] != '.jump'):
        raise Exception('.main body does not end in ".jump" at %s(%d), column %d' % (filename,lastToken['line'],lastToken['col']));
    # Ensure functions and interrupts end in a ".jumpc" or ".return".
    if firstToken['value'] in ('.function','.interrupt',):
      errorMsg = 'Last entry in ".function" or ".interrupt" must be a ".jump" or ".return" at %s(%d), column %d' % (filename,lastToken['line'],lastToken['col']);
      if lastToken['type'] != 'macro':
        raise Exception(errorMsg);
      if lastToken['value'] not in ('.jump','.return',):
        raise Exception(errorMsg);
    # Ensure no macros and no instructions in non-"functions".
    # Byproduct:  No labels allowed in non-"functions".
    if firstToken['value'] not in ('.function','.interrupt','.main',):
      for token in rawTokens[2:]:
        if (token['type'] == 'macro'):
          raise Exception('Macro not allowed in directive at %s(%d), column %d' % (filename,token['line'],token['col']));
        if token['type'] == 'instruction':
          raise Exception('Instruction not allowed in directive at %s(%d), column %d' % (filename,token['line'],token['col']));
    # Ensure local labels are defined and used.
    labelDefs = list();
    for token in rawTokens:
      if token['type'] == 'label':
        name = token['value'];
        if name in labelDefs:
          raise Exception('Repeated label definition at %s(%d), column %d', (filename,token['line'],token['col']));
        labelDefs.append(name);
    labelsUsed = list();
    for token in rawTokens:
      if (token['type'] == 'macro') and (token['value'] in ('.jump','.jumpc',)):
        target = token['argument'][0];
        if target not in labelDefs:
          raise Exception('label definition for target missing at %s(%d), column %d' % (filename,token['line'],token['col']));
        labelsUsed.append(target);
    labelsUnused = set(labelDefs) - set(labelsUsed);
    if labelsUnused:
      raise Exception('Unused label(s) %s in body %s(%d)' % (labelsUnused,filename,firstToken['line']));
    # Ensure symbols referenced by ".input" and ".outport" are defined.
    for token in rawTokens:
      if (token['type'] == 'macro') and (token['value'] == '.inport'):
        if self.IsInport(token['argument'][0]):
          raise Exception('Input port "%s" not defined at %s(%d), column %d', (token['argument'][0],filename,token['line'],token['col']));
      if (token['type'] == 'macro') and (token['value'] == '.inport'):
        if self.IsOutport(token['argument'][0]):
          raise Exception('Output port "%s" not defined at %s(%d), column %d', (token['argument'][0],filename,token['line'],token['col']));
    # Ensure referenced symbols are already defined.
    checkBody = False;
    if (rawTokens[0]['type'] == 'directive') and (rawTokens[0]['value'] in ('.function','.interrupt','.main',)):
      checkBody = True;
    if checkBody:
      for token in rawTokens[2:]:
        if token['type'] == 'symbol':
          name = token['value'];
          if name not in symbols['list']:
            raise Exception('Undefined symbol at %s(%d), column %d' % (filename,token['line'],token['col']));
          ixName = symbols['list'].index(name);
          if symbols['type'][ixName] not in ('constant','macro','variable',):
            raise Exception('Illegal symbol at %s(%d), column %d' % (filename,token['line'],token['col']));

  ################################################################################
  #
  # fill in symbols, etc. in the list of raw tokens.
  #
  ################################################################################

  def ExpandTokens(self,filename,rawTokens):
    tokens = list();
    offset = 0;
    for token in rawTokens:
      if token['type'] == 'label':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
        # labels don't change the offset
      elif token['type'] in ('character','instruction','value',):
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
        offset = offset + 1;
      elif token['type'] == 'string':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
        offset = offset + len(token['value']) + 1;
      elif token['type'] == 'macro':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset, argument=token['argument']));
        offset = offset + self.MacroLength(token['value']);
      elif token['type'] == 'symbol':
        if token['value'] not in self.symbols['list']:
          raise Exception('Program bug:  symbol %s not in symbol list at %s(%d), column %d' %(token['value'],filename,token['line'],token['col']));
        ix = symbols['list'].index(token['value']);
        for lToken in symbols['tokens']:
          tokens.append(dict(type=lToken['type'], value=lToken['value'], offset=offset+lToken['offset']));
        offset = offset + symbols['length'][ix];
      else:
        raise Exception('Program bug:  unexpected token type "%s"' % token['type']);
    return dict(tokens=tokens, length=offset);

  def FillRawTokens(self,filename,rawTokens):
    firstToken = rawTokens[0];
    secondToken = rawTokens[1];
    if firstToken['value'] == '.abbr':
      raise Exception('TODO -- implement ".abbr"');
    elif firstToken['value'] == '.constant':
      raise Exception('TODO -- implement ".constant"');
    # Process ".function" definition.
    elif firstToken['value'] == '.function':
      if secondToken['type'] != 'symbol':
        raise Exception('Expected symbol at %s(%d), column %d' % (filename, secondToken['line'], secondToken['col']));
      if secondToken['value'] in self.symbols['list']:
        raise Exception('Symbol %s already defined at %s(%d), column %d' % (secondToken['value'], filename, secondToken['line'], secondToken['col']));
      et = self.ExpandTokens(filename,rawTokens[2:]);
      self.symbols['list'].append(secondToken['value']);
      self.symbols['type'].append('function');
      self.symbols['tokens'].append(et['tokens']);
      self.symbols['length'].append(et['length']);
    # Process ".interrupt" definition.
    elif firstToken['value'] == '.interrupt':
      if self.interrupt:
        raise Exception('Second definition of ".interrupt" at %s(%d)' % (filename,firstToken['line']));
      self.interrupt = self.ExpandTokens(filename,rawTokens[1:]);
    # Process ".main" definition.
    elif firstToken['value'] == '.main':
      if self.main:
        raise Exception('Second definition of ".main" at %s(%d)' % (filename,firstToken['line']));
      self.main = self.ExpandTokens(filename,rawTokens[1:]);
    elif firstToken['value'] == '.memory':
      raise Exception('TODO -- implement ".memory"');
    elif firstToken['value'] == '.variable':
      raise Exception('TODO -- implement ".variable"');
    else:
      raise Exception('Program Bug:  Unrecognized directive %s at %s(%d)' % (firstToken['value'],filename,firstToken['line']));

  def Main(self):
    return self.main;

  def Interrupt(self):
    return self.interrupt;

  def Symbols(self):
    return self.symbols;

  ################################################################################
  #
  # Generate the list of required functions from the ".main" and ".interrupt"
  # bodies.
  #
  # Look for function calls with the bodies of the required functions.  If the
  # function has not already been identified as a required function then (1)
  # ensure it exists and is a function and then (2) add it to the list of
  # required functions.
  #
  # Whenever a function is added to the list, set its start address and get its
  # length.
  #
  ################################################################################

  def EvaluateFunctionTree(self):
    self.functionEvaluation = dict(list=list(), length=list(),body=list(), address=list());
    nextStart = 0;
    # ".main" is always required.
    self.functionEvaluation['list'].append('.main');
    self.functionEvaluation['length'].append(self.main['length']);
    self.functionEvaluation['body'].append(self.main['tokens']);
    self.functionEvaluation['address'].append(nextStart);
    nextStart = nextStart + self.functionEvaluation['length'][-1];
    # ".interrupt" is optionally required (and is sure to exist by this function
    # call if it is required).
    if self.interrupt:
      self.functionEvaluation['list'].append('.interrupt');
      self.functionEvaluation['length'].append(self.interrupt['length']);
      self.functionEvaluation['body'].append(self.interrupt['tokens']);
      self.functionEvaluation['address'].append(nextStart);
      nextStart = nextStart + self.functionEvaluation['length'][-1];
    # Loop through the required function bodies as they are identified.
    ix = 0;
    while ix < len(self.functionEvaluation['body']):
      for token in self.functionEvaluation['body'][ix]:
        if (token['type'] == 'macro') and (token['value'] in ('.call','.callc',)):
          callName = token['argument'][0];
          if callName not in self.functionEvaluation['list']:
            if callName not in self.symbols['list']:
              raise Exception('Function "%s" not defined for function "%s"' % (callName,self.functionEvaluation['list'][ix],));
            ixName = self.symbols['list'].index(callName);
            if self.symbols['type'][ixName] != 'function':
              raise Exception('Function "%s" called by "%s" is not a function', (callName, self.functionEvaluation['list'][ix],));
            self.functionEvaluation['list'].append(callName);
            self.functionEvaluation['length'].append(self.symbols['length'][ixName]);
            self.functionEvaluation['body'].append(self.symbols['tokens'][ixName]);
            self.functionEvaluation['address'].append(nextStart);
            nextStart = nextStart + self.functionEvaluation['length'][-1];
      ix = ix + 1;
    # Within each function, compute the list of label addresses and then fill in
    # the address for all jumps and calls.
    for ix in range(len(self.functionEvaluation['list'])):
      startAddress = self.functionEvaluation['address'][ix];
      labelAddress = dict(list=list(), address=list());
      for token in self.functionEvaluation['body'][ix]:
        if token['type'] == 'label':
          labelAddress['list'].append(token['value']);
          labelAddress['address'].append(startAddress + token['offset']);
      for token in self.functionEvaluation['body'][ix]:
        if (token['type'] == 'macro') and (token['value'] in ('.jump','.jumpc',)):
          ix = labelAddress['list'].index(token['argument'][0]);
          token['address'] = labelAddress['address'][ix];
        if (token['type'] == 'macro') and (token['value'] in ('.call','.callc',)):
          ix = self.functionEvaluation['list'].index(token['argument'][0]);
          token['address'] = self.functionEvaluation['address'][ix];
    # Sanity checks for address range
    if self.functionEvaluation['address'][-1] + self.functionEvaluation['length'][-1] > 2**14-1:
      raise Exception('Max address for program requires more than 14 bits');
#    for ix in range(len(self.functionEvaluation['list'])):
#      print self.functionEvaluation['list'][ix], self.functionEvaluation['address'][ix], self.functionEvaluation['length'][ix];
#      for ix2 in range(len(self.functionEvaluation['body'][ix])):
#        print self.functionEvaluation['body'][ix][ix2];

  ################################################################################
  #
  # Emit the metacode from the assembler.
  #
  ################################################################################

  def EmitOpcode(self,fp,opcode,name):
    fp.write('%03X %s\n' % (opcode,name));

  def EmitPush(self,fp,value):
    fp.write('1%02X %02X\n' % (value,value));

  def Emit(self,fp):
    """Emit the program code"""
    # Write the program marker, address of .main, address or "[]" of .interrupt,
    # and the total program length.
    fp.write(':program');
    fp.write(' %d' % self.functionEvaluation['address'][0]);
    if self.interrupt:
      fp.write(' %d' % self.functionEvaluation['address'][1]);
    else:
      fp.write(' []');
    fp.write(' %d' % (self.functionEvaluation['address'][-1] + self.functionEvaluation['length'][-1]));
    fp.write('\n');
    # Emit the bodies
    for ix in range(len(self.functionEvaluation['list'])):
      fp.write('- %s\n' % self.functionEvaluation['list'][ix]);
      for token in self.functionEvaluation['body'][ix]:
        if token['type'] == 'value':
          self.EmitPush(fp,token['value']);
        elif token['type'] == 'label':
          pass;
        elif token['type'] == 'instruction':
          self.EmitOpcode(fp,self.InstructionOpcode(token['value']),token['value']);
        elif token['type'] == 'macro':
          if token['value'] == '.call':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['jump'] | (token['address'] >> 8),'jump '+token['argument'][0]);
            self.EmitOpcode(fp,self.specialInstructions['call'],'call');
          elif token['value'] == '.callc':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['jumpc'] | (token['address'] >> 8),'jumpc '+token['argument'][0]);
            self.EmitOpcode(fp,self.specialInstructions['callc'],'callc');
          elif token['value'] == '.fetch':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | (token['address'] >> 8),'fetch');
          elif token['value'] == '.fetchindexed':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | (token['address'] >> 8),'fetch');
          elif token['value'] == '.inport':
            self.EmitPush(fp,self.InportAddress(token['argument'][0]) & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['inport'],'inport');
          elif token['value'] == '.jump':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['jump'] | (token['address'] >> 8),'jump');
            self.EmitOpcode(fp,self.InstructionOpcode('nop'),'nop');
          elif token['value'] == '.jumpc':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['jumpc'] | (token['address'] >> 8),'jumpc');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.outport':
            self.EmitPush(fp,self.OutportAddress(token['argument'][0]) & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['outport'],'outport');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.return':
            self.EmitOpcode(fp,self.specialInstructions['return'],'return');
            self.EmitOpcode(fp,self.InstructionOpcode('nop'),'nop');
          elif token['value'] == '.store':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.specialInstructions['store'] | (token['address'] >> 8),'store');
            fp.write('%03X\n', self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.storeindexed':
            self.EmitPush(fp,token['address'] & 0xFF);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['store'] | (token['address'] >> 8),'store');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          else:
            raise Exception('Program Bug:  Unrecognized macro "%s"' % token['value']);
        else:
          raise Exception('Program Bug:  Unrecognized type "%s"' % token['type']);

  ################################################################################
  #
  # Initialize the object.
  #
  ################################################################################

  def __init__(self):

    #
    # Enumerate the directives
    # Note:  The ".include" directive is handled within asmDef.FileBodyIterator.
    #

    self.directives = dict();

    self.directives['list']= list();
    self.directives['list'].append('.abbr');
    self.directives['list'].append('.constant');
    self.directives['list'].append('.function');
    self.directives['list'].append('.interrupt');
    self.directives['list'].append('.main');
    self.directives['list'].append('.memory');
    self.directives['list'].append('.variable');

    #
    # Configure the pre-defined macros
    #

    self.macros = dict(list=list(), length=list(), nArgs=list());
    self.AddMacro('.call',             3);
    self.AddMacro('.callc',            3);
    self.AddMacro('.fetch',            2);
    self.AddMacro('.fetchindexed',     3);
    self.AddMacro('.inport',           2);
    self.AddMacro('.jump',             3);
    self.AddMacro('.jumpc',            3);
    self.AddMacro('.outport',          3);
    self.AddMacro('.return',           2, nArgs=0);
    self.AddMacro('.store',            3);
    self.AddMacro('.storeindexed',     4);

    #
    # Configure the containers for the expanded main, interrupt, function,
    # macro, etc. definitions.
    #

    self.interrupt = list();
    self.main = list();
    self.symbols = dict(list=list(), type=list(), tokens=list(), length=list(), used=list());

    #
    # Configure the instructions.
    #

    self.instructions = dict(list=list(), opcode=list());
    self.AddInstruction('&',            0x01A);
    self.AddInstruction('+',            0x018);
    self.AddInstruction('-',            0x019);
    self.AddInstruction('00=',          0x020);
    self.AddInstruction('01=',          0x021);
    self.AddInstruction('0>>',          0x004);
    self.AddInstruction('1>>',          0x005);
    self.AddInstruction('7E=',          0x022);
    self.AddInstruction('7F=',          0x023);
    self.AddInstruction('80=',          0x024);
    self.AddInstruction('81=',          0x025);
    self.AddInstruction('<<0',          0x001);
    self.AddInstruction('<<1',          0x002);
    self.AddInstruction('<<msb',        0x003);
    self.AddInstruction('>r',           0x058);
    self.AddInstruction('FE=',          0x026);
    self.AddInstruction('FF=',          0x027);
    self.AddInstruction('^',            0x01C);
    self.AddInstruction('dis',          0x01C);
    self.AddInstruction('drop',         0x01E);
    self.AddInstruction('dup',          0x008);
    self.AddInstruction('ena',          0x019);
    self.AddInstruction('lsb>>',        0x007);
    self.AddInstruction('msb>>',        0x006);
    self.AddInstruction('nip',          0x01F);
    self.AddInstruction('nop',          0x000);
    self.AddInstruction('or',           0x01B);
    self.AddInstruction('over',         0x00A);
    self.AddInstruction('r>',           0x061);
    self.AddInstruction('r@',           0x009);
    self.AddInstruction('swap',         0x012);

    self.specialInstructions = dict();
    self.specialInstructions['call']    = 0x040;
    self.specialInstructions['callc']   = 0x048;
    self.specialInstructions['fetch']   = 0x070;
    self.specialInstructions['inport']  = 0x030;
    self.specialInstructions['jump']    = 0x080;
    self.specialInstructions['jumpc']   = 0x0C0;
    self.specialInstructions['outport'] = 0x038;
    self.specialInstructions['return']  = 0x028;
    self.specialInstructions['store']   = 0x068;

    #
    # Create empty input and output port array definitions.
    #

    self.inports = dict();
    self.outports = dict();
