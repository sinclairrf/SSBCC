################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Assembly language definitions for SSBCC 9x8.
#
################################################################################

import copy
import string

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

  def MacroLength(self,token):
    if token['value'] not in self.macros['list']:
      raise Exception('Program Bug');
    ix = self.macros['list'].index(token['value']);
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
    if name not in self.symbols['list']:
      return False;
    ix = self.symbols['list'].index(name);
    return self.symbols['type'][ix] == 'inport';

  def IsOutport(self,name):
    if name not in self.symbols['list']:
      return False;
    ix = self.symbols['list'].index(name);
    return self.symbols['type'][ix] == 'outport';

  def InportAddress(self,name):
    if not self.IsInport(name):
      raise Exception('Program Bug');
    ix = self.symbols['list'].index(name);
    return self.symbols['body'][ix]['address'];

  def OutportAddress(self,name):
    if not self.IsOutport(name):
      raise Exception('Program Bug');
    ix = self.symbols['list'].index(name);
    return self.symbols['body'][ix]['address'];

  def RegisterInport(self,name,address):
    if self.IsInport(name):
      raise Exception('Program Bug');
    self.AddSymbol(name,'inport',dict(address=address));

  def RegisterOutport(self,name,address):
    if self.IsOutport(name):
      raise Exception('Program Bug');
    self.AddSymbol(name,'outport',dict(address=address));

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
    # Ensure functions and interrupts end in a ".jump" or ".return".
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
        if not self.IsInport(token['argument'][0]):
          raise Exception('Input port "%s" not defined at %s(%d), column %d', (token['argument'][0],filename,token['line'],token['col']));
      if (token['type'] == 'macro') and (token['value'] == '.outport'):
        if not self.IsOutport(token['argument'][0]):
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

  def ByteList(self,filename,rawTokens):
    tokens=list();
    for token in rawTokens:
      if token['type'] == 'value':
        if type(token['value']) == int:
          tokens.append(token['value']);
        else:
          for lToken in token['value']:
            tokens.append(lToken);
      else:
        raise Exception('Illegal token "%s" at %s(%d), column %d', (token['type'],filename,token['line'],token['col']));
    return tokens;

  def ExpandTokens(self,filename,rawTokens):
    tokens = list();
    offset = 0;
    for token in rawTokens:
      # insert labels
      if token['type'] == 'label':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
        # labels don't change the offset
      # append instructions
      elif token['type'] == 'instruction':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
        offset = offset + 1;
      # append values
      elif token['type'] == 'value':
        if type(token['value']) == int:
          tokens.append(dict(type=token['type'], value=token['value'], offset=offset));
          offset = offset + 1;
        else:
          revTokens = copy.copy(token['value']);
          revTokens.reverse();
          for lToken in revTokens:
            tokens.append(dict(type=token['type'], value=lToken, offset=offset));
            offset = offset + 1;
      # append macros
      elif token['type'] == 'macro':
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset, argument=token['argument']));
        offset = offset + self.MacroLength(token);
      # interpret and append symbols
      elif token['type'] == 'symbol':
        if token['value'] not in self.symbols['list']:
          raise Exception('Program bug:  symbol "%s" not in symbol list at %s(%d), column %d' %(token['value'],filename,token['line'],token['col']));
        ix = self.symbols['list'].index(token['value']);
        if self.symbols['type'][ix] == 'variable':
          tokens.append(dict(type='variable', value=token['value'], offset=offset));
          offset = offset + 1;
        else:
          raise Exception('Unrecognized symbol type "%s" for %s" at %s(%d), column %d' % (token['type'],token['value'],filename,token['line'],token['col']));
      # everything else is an error
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
      self.symbols['list'].append(secondToken['value']);
      self.symbols['type'].append('function');
      self.symbols['body'].append(self.ExpandTokens(filename,rawTokens[2:]));
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
    # Process ".memory" declaration.
    elif firstToken['value'] == '.memory':
      if len(rawTokens) != 3:
        raise Exception('".memory" directive requires exactly two arguments at %s(%d)' % (filename, firstToken['line']));
      if (secondToken['type'] != 'symbol') or (secondToken['value'] not in ('RAM','ROM',)):
        raise Exception('First argument to ".memory" directive must be "RAM" or "RAM" at %s(%d), column %d' % (filename,secondToken['line'],secondToken['col']));
      thirdToken = rawTokens[2];
      if thirdToken['type'] != 'symbol':
        raise Exception('".memory" directive requires name for second argument at %s(%d)' % (filename,thirdToken['line']));
      if thirdToken['value'] in self.symbols['list']:
        ix = self.symbols['list'].index(thirdToken['value']);
        if self.symbols['type'] != secondToken['value']:
          raise Exception('Redefinition of ".memory %s %s" not allowed at %s(%d)' % (filename,firstToken['line']));
      else:
        self.AddSymbol(thirdToken['value'],secondToken['value'],dict(length=0));
      self.currentMemory = thirdToken['value'];
    # Process ".variable" declaration.
    elif firstToken['value'] == '.variable':
      if not self.currentMemory:
        raise Exception('".memory" directive required before ".variable" directive at %s(%d)' % (filename,firstToken('line')));
      if secondToken['type'] != 'symbol':
        raise Exception('Bad variable name at %s(%d), column %d' % (filename, secondToken['line'], secondToken['col']));
      ixMem = self.symbols['list'].index(self.currentMemory);
      currentMemoryBody = self.symbols['body'][ixMem];
      byteList = self.ByteList(filename,rawTokens[2:]);
      body = dict(memory=self.currentMemory, start=currentMemoryBody['length'], value=byteList);
      self.AddSymbol(secondToken['value'], 'variable', body=body);
      currentMemoryBody['length'] = currentMemoryBody['length'] + len(byteList);
      if currentMemoryBody['length'] > 256:
        raise Exception('Memory "%s" becomes too long at %s(%d)' % (filename,firstToken['line']));
    # Everything else is an error.
    else:
      raise Exception('Program Bug:  Unrecognized directive %s at %s(%d)' % (firstToken['value'],filename,firstToken['line']));

  def Main(self):
    return self.main;

  def Interrupt(self):
    return self.interrupt;

  def AddSymbol(self,name,stype,body):
    self.symbols['list'].append(name);
    self.symbols['type'].append(stype);
    self.symbols['body'].append(body);

  def Symbols(self):
    return self.symbols;

  ################################################################################
  #
  # Compute the memory bank indices.
  #
  ################################################################################

  def EvaluateMemoryTree(self):
    self.memories = dict(list=list(), type=list(), length=list(), bank=list());
    ramBank = 0;
    romBank = 3;
    for ix in range(len(self.symbols['list'])):
      if self.symbols['type'][ix] in ('RAM','ROM',):
        memBody = self.symbols['body'][ix];
        if memBody['length'] == 0:
          raise Exception('Empty memory:  %s' % self.symbols['list'][ix]);
        self.memories['list'].append(self.symbols['list'][ix]);
        self.memories['type'].append(self.symbols['type'][ix]);
        self.memories['length'].append(memBody['length']);
        if self.symbols['type'][ix] == 'RAM':
          self.memories['bank'].append(ramBank);
          ramBank = ramBank + 1;
        else:
          self.memories['bank'].append(romBank);
          romBank = romBank - 1;
    if len(self.memories['list']) > 4:
      raise Exception('Too many memory banks');

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
    self.functionEvaluation = dict(list=list(), length=list(), body=list(), address=list());
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
            self.functionEvaluation['length'].append(self.symbols['body'][ixName]['length']);
            self.functionEvaluation['body'].append(self.symbols['body'][ixName]['tokens']);
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
    if self.functionEvaluation['address'][-1] + self.functionEvaluation['length'][-1] > 2**13-1:
      raise Exception('Max address for program requires more than 13 bits');
#    for ix in range(len(self.functionEvaluation['list'])):
#      print self.functionEvaluation['list'][ix], self.functionEvaluation['address'][ix], self.functionEvaluation['length'][ix];
#      for ix2 in range(len(self.functionEvaluation['body'][ix])):
#        print self.functionEvaluation['body'][ix][ix2];

  ################################################################################
  #
  # Emit the meta code for the memories.
  #
  ################################################################################

  def EmitMemories(self,fp):
    """Emit the memories"""
    # Emit the individual memories.
    for ixMem in range(len(self.memories['list'])):
      fp.write(':memory %s %s %d %d\n' % (self.memories['type'][ixMem],self.memories['list'][ixMem],self.memories['bank'][ixMem],self.memories['length'][ixMem]));
      memName = self.memories['list'][ixMem];
      for ixSymbol in range(len(self.symbols['list'])):
        if self.symbols['type'][ixSymbol] != 'variable':
          continue;
        vBody = self.symbols['body'][ixSymbol];
        if vBody['memory'] != memName:
          continue;
        fp.write('- %s\n' % self.symbols['list'][ixSymbol]);
        for v in vBody['value']:
          fp.write('%02X\n' % v);
      fp.write('\n');

  ################################################################################
  #
  # Emit the metacode for the program.
  #
  ################################################################################

  def EmitOpcode(self,fp,opcode,name):
    fp.write('%03X %s\n' % (opcode,name));

  def EmitPush(self,fp,value,name=None):
    if type(name) == str:
      fp.write('1%02X %02X %s\n' % ((value % 0x100),value,name));
    elif (chr(value) in string.printable) and (chr(value) not in string.whitespace):
      fp.write('1%02X %02X \'%c\'\n' % ((value % 0x100),value,value));
    else:
      fp.write('1%02X %02X\n' % ((value % 0x100),value));

  def EmitVariable(self,fp,name):
    if name not in self.symbols['list']:
      raise Exception('Variable "%s" not recognized' + name);
    ixName = self.symbols['list'].index(name);
    body = self.symbols['body'][ixName];
    fp.write('1%02X %s\n' % (body['start'],name));
    ixMem = self.memories['list'].index(body['memory']);
    return self.memories['bank'][ixMem];

  def EmitProgram(self,fp):
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
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['call'] | (token['address'] >> 8),'call '+token['argument'][0]);
            self.EmitOpcode(fp,self.InstructionOpcode('nop'),'nop');
          elif token['value'] == '.callc':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['callc'] | (token['address'] >> 8),'callc '+token['argument'][0]);
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.fetch':
            ixBank = self.EmitVariable(fp,token['argument'][0]);
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch');
          elif token['value'] == '.fetchindexed':
            ixBank = self.EmitVariable(fp,token['argument'][0]);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch');
          elif token['value'] == '.inport':
            self.EmitPush(fp,self.InportAddress(token['argument'][0]) & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['inport'],'inport');
          elif token['value'] == '.jump':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['jump'] | (token['address'] >> 8),'jump');
            self.EmitOpcode(fp,self.InstructionOpcode('nop'),'nop');
          elif token['value'] == '.jumpc':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['jumpc'] | (token['address'] >> 8),'jumpc');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.outport':
            self.EmitPush(fp,self.OutportAddress(token['argument'][0]) & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['outport'],'outport');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.return':
            self.EmitOpcode(fp,self.specialInstructions['return'],'return');
            self.EmitOpcode(fp,self.InstructionOpcode('nop'),'nop');
          elif token['value'] == '.store':
            ixBank = self.EmitVariable(fp,token['argument'][0]);
            self.EmitOpcode(fp,self.specialInstructions['store'] | ixBank,'store');
            self.EmitOpCode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.storeindexed':
            ixBank = self.EmitVariable(fp,token['argument'][0]);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['store'] | ixBank,'store');
            self.EmitOpCode(fp,self.InstructionOpcode('drop'),'drop');
          else:
            raise Exception('Program Bug:  Unrecognized macro "%s"' % token['value']);
        elif token['type'] == 'symbol':
          self.EmitPush(fp,token['value'],name=token['name']);
        elif token['type'] == 'variable':
          self.EmitVariable(fp,token['value']);
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
    self.symbols = dict(list=list(), type=list(), body=list());
    self.currentMemory = None;

    #
    # Configure the instructions.
    #

    self.instructions = dict(list=list(), opcode=list());
    self.AddInstruction('&',            0x01A);
    self.AddInstruction('+',            0x018);
    self.AddInstruction('+ss',          0x056);
    self.AddInstruction('+su',          0x054);
    self.AddInstruction('+us',          0x052);
    self.AddInstruction('+uu',          0x050);
    self.AddInstruction('-',            0x019);
    self.AddInstruction('-1<>',         0x023);
    self.AddInstruction('-1=',          0x022);
    self.AddInstruction('-ss',          0x057);
    self.AddInstruction('-su',          0x055);
    self.AddInstruction('-us',          0x053);
    self.AddInstruction('-uu',          0x051);
    self.AddInstruction('0<>',          0x021);
    self.AddInstruction('0=',           0x020);
    self.AddInstruction('0>>',          0x004);
    self.AddInstruction('1+',           0x058);
    self.AddInstruction('1-',           0x05C);
    self.AddInstruction('1>>',          0x005);
    self.AddInstruction('2+',           0x059);
    self.AddInstruction('2-',           0x05D);
    self.AddInstruction('3+',           0x05A);
    self.AddInstruction('3-',           0x05E);
    self.AddInstruction('4+',           0x05B);
    self.AddInstruction('4-',           0x05F);
    self.AddInstruction('<<0',          0x001);
    self.AddInstruction('<<1',          0x002);
    self.AddInstruction('<<msb',        0x003);
    self.AddInstruction('>r',           0x040);
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
    self.AddInstruction('r>',           0x049);
    self.AddInstruction('r@',           0x009);
    self.AddInstruction('swap',         0x012);

    self.specialInstructions = dict();
    self.specialInstructions['call']    = 0x0C0;
    self.specialInstructions['callc']   = 0x0E0;
    self.specialInstructions['fetch']   = 0x078;
    self.specialInstructions['fetch+']  = 0x07C;
    self.specialInstructions['inport']  = 0x030;
    self.specialInstructions['jump']    = 0x080;
    self.specialInstructions['jumpc']   = 0x0A0;
    self.specialInstructions['outport'] = 0x038;
    self.specialInstructions['return']  = 0x028;
    self.specialInstructions['store+']  = 0x070;
    self.specialInstructions['store-']  = 0x074;
