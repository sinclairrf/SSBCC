################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Assembly language definitions for SSBCC 9x8.
#
################################################################################

import copy
import string

import asmDef

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

  def AddMacro(self,name,macroLength,args):
    self.macros['list'].append(name);
    self.macros['length'].append(macroLength);
    self.macros['args'].append(args);
    ix = len(args);
    while (ix > 0) and (len(args[ix-1][0]) != 0):
      ix = ix - 1;
    self.macros['nArgs'].append(range(ix,len(args)+1));

  def IsMacro(self,name):
    return name in self.macros['list'];

  def MacroArgTypes(self,name,ixArg):
    if name not in self.macros['list']:
      raise Exception('Program Bug');
    ix = self.macros['list'].index(name);
    return self.macros['args'][ix][ixArg][1:];

  def MacroDefault(self,name,ixArg):
    if name not in self.macros['list']:
      raise Exception('Program Bug');
    ix = self.macros['list'].index(name);
    return self.macros['args'][ix][ixArg][0];

  def MacroLength(self,token):
    if token['value'] not in self.macros['list']:
      raise Exception('Program Bug');
    ix = self.macros['list'].index(token['value']);
    length = self.macros['length'][ix];
    if length >= 0:
      return length;
    if token['value'] == '.fetchvector':
      return int(token['argument'][1]) + 1;
    if token['value'] == '.storevector':
      return int(token['argument'][1]) + 2;
    raise Exception('Program Bug');

  def MacroNumberArgs(self,name):
    if name not in self.macros['list']:
      raise Exception('Program bug');
    ix = self.macros['list'].index(name);
    return self.macros['nArgs'][ix];

  def MacroOptArgIsSymbol(self,token):
    if not token['argument']:
      return False;
    lastArg = token['argument'][-1];
    if type(lastArg) == str:
      return False;
    return lastArg['type'] == 'symbol';

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

  def RegisterMemoryLength(self,name,length):
    self.memoryLength[name] = length;

  ################################################################################
  #
  # Check a list of raw tokens to ensure their proper format.
  #
  ################################################################################

  def CheckRawTokens(self,filename,rawTokens):
    # Ensure the first token is a directive.
    firstToken = rawTokens[0];
    if firstToken['type'] != 'directive':
      raise Exception('Program Bug triggered at %s:%d:%d' % (filename,firstToken['line'],firstToken['col']));
    # Ensure the main body ends in a ".jump".
    lastToken = rawTokens[-1];
    if firstToken['value'] == '.main':
      if (lastToken['type'] != 'macro') or (lastToken['value'] != '.jump'):
        raise asmDef.AsmException('.main body does not end in ".jump" at %s:%d:%d' % (filename,lastToken['line'],lastToken['col']));
    # Ensure functions and interrupts end in a ".jump" or ".return".
    if firstToken['value'] in ('.function','.interrupt',):
      if (lastToken['type'] != 'macro') or (lastToken['value'] not in ('.jump','.return',)):
        raise asmDef.AsmException('Last entry in ".function" or ".interrupt" must be a ".jump" or ".return" at %s:%d:%d' % (filename,lastToken['line'],lastToken['col']));
    # Ensure no macros and no instructions in non-"functions".
    # Byproduct:  No labels allowed in non-"functions".
    if firstToken['value'] not in ('.function','.interrupt','.main',):
      for token in rawTokens[2:]:
        if (token['type'] == 'macro'):
          raise asmDef.AsmException('Macro not allowed in directive at %s:%d:%d' % (filename,token['line'],token['col']));
        if token['type'] == 'instruction':
          raise asmDef.AsmException('Instruction not allowed in directive at %s:%d:%d' % (filename,token['line'],token['col']));
    # Ensure local labels are defined and used.
    labelDefs = list();
    for token in rawTokens:
      if token['type'] == 'label':
        name = token['value'];
        if name in labelDefs:
          raise asmDef.AsmException('Repeated label definition at %s:%d:%d', (filename,token['line'],token['col']));
        labelDefs.append(name);
    labelsUsed = list();
    for token in rawTokens:
      if (token['type'] == 'macro') and (token['value'] in ('.jump','.jumpc',)):
        target = token['argument'][0]['value'];
        if target not in labelDefs:
          raise asmDef.AsmException('label definition for target missing at %s:%d:%d' % (filename,token['line'],token['col']));
        labelsUsed.append(target);
    labelsUnused = set(labelDefs) - set(labelsUsed);
    if labelsUnused:
      raise asmDef.AsmException('Unused label(s) %s in body %s:%d' % (labelsUnused,filename,firstToken['line']));
    # Ensure symbols referenced by ".input" and ".outport" are defined.
    for token in rawTokens:
      if (token['type'] == 'macro') and (token['value'] == '.inport'):
        if not self.IsInport(token['argument'][0]['value']):
          raise asmDef.AsmException('Input port "%s" not defined at %s:%d:%d' % (token['argument'][0]['value'],filename,token['line'],token['col']));
      if (token['type'] == 'macro') and (token['value'] == '.outport'):
        if not self.IsOutport(token['argument'][0]['value']):
          raise asmDef.AsmException('Output port "%s" not defined at %s:%d:%d' % (token['argument'][0]['value'],filename,token['line'],token['col']));
    # Ensure referenced symbols are already defined.
    checkBody = False;
    if (rawTokens[0]['type'] == 'directive') and (rawTokens[0]['value'] in ('.function','.interrupt','.main',)):
      checkBody = True;
    if checkBody:
      for token in rawTokens[2:]:
        if token['type'] == 'symbol':
          name = token['value'];
          allowableTypes = ('constant','inport','macro','outport','variable',);
        elif token['type'] == 'macro' and self.MacroOptArgIsSymbol(token):
          name = token['argument'][-1]['value'];
          allowableTypes = ('RAM','ROM','constant','inport','outport','variable',);
        else:
          continue;
        if name not in self.symbols['list']:
          raise asmDef.AsmException('Undefined symbol at %s:%d:%d' % (filename,token['line'],token['col']));
        ixName = self.symbols['list'].index(name);
        if self.symbols['type'][ixName] not in allowableTypes:
          raise asmDef.AsmException('Illegal symbol at %s:%d:%d' % (filename,token['line'],token['col']));

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
        raise asmDef.AsmException('Illegal token "%s" at %s:%d:%d', (token['type'],filename,token['line'],token['col']));
    return tokens;

  def ExpandSymbol(self,filename,token,singleValue):
    if token['value'] not in self.symbols['list']:
      raise asmDef.AsmException('Symbol "%s" not in symbol list at %s:%d:%d' %(token['value'],filename,token['line'],token['col']));
    ix = self.symbols['list'].index(token['value']);
    if self.symbols['type'][ix] == 'RAM':
      return dict(type='RAM', value=token['value']);
    elif self.symbols['type'][ix] == 'ROM':
      return dict(type='ROM', value=token['value']);
    elif self.symbols['type'][ix] == 'constant':
      if singleValue and len(self.symbols['body'][ix])!=1:
        raise asmDef.AsmException('Constant "%s" must evaluate to a single byte at %s:%d:%d' % (token['value'],filename,token['line'],token['col']))
      return dict(type='constant', value=token['value']);
    elif self.symbols['type'][ix] == 'inport':
      return dict(type='inport', value=token['value']);
    elif self.symbols['type'][ix] == 'outport':
      return dict(type='outport', value=token['value']);
    elif self.symbols['type'][ix] == 'variable':
      return dict(type='variable', value=token['value']);
    else:
      print token
      raise Exception('Program Bug');

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
        if self.MacroOptArgIsSymbol(token):
          token['argument'][-1] = self.ExpandSymbol(filename,token['argument'][-1],singleValue=True);
        tokens.append(dict(type=token['type'], value=token['value'], offset=offset, argument=token['argument']));
        offset = offset + self.MacroLength(token);
      # interpret and append symbols
      elif token['type'] == 'symbol':
        newToken = self.ExpandSymbol(filename,token,singleValue=False);
        newToken['offset'] = offset;
        tokens.append(newToken);
        if token['type'] == 'constant':
          ix = self.symbols['list'].index(newToken['value']);
          offset = offset + len(self.symbols['body'][ix]);
        else:
          offset = offset + 1;
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
      if secondToken['type'] != 'symbol':
        raise asmDef.AsmException('Bad constant name at %s:%d:%d' % (filename,secondToken['line'],secondToken['col']));
      byteList = self.ByteList(filename,rawTokens[2:]);
      self.AddSymbol(secondToken['value'], 'constant', body=byteList);
    # Process ".function" definition.
    elif firstToken['value'] == '.function':
      if secondToken['type'] != 'symbol':
        raise asmDef.AsmException('Expected symbol at %s:%d:%d' % (filename,secondToken['line'],secondToken['col']));
      if secondToken['value'] in self.symbols['list']:
        raise asmDef.AsmException('Symbol %s already defined at %s:%d:%d' % (secondToken['value'],filename,secondToken['line'],secondToken['col']));
      self.symbols['list'].append(secondToken['value']);
      self.symbols['type'].append('function');
      self.symbols['body'].append(self.ExpandTokens(filename,rawTokens[2:]));
    # Process ".interrupt" definition.
    elif firstToken['value'] == '.interrupt':
      if self.interrupt:
        raise asmDef.AsmException('Second definition of ".interrupt" at %s:%d' % (filename,firstToken['line']));
      self.interrupt = self.ExpandTokens(filename,rawTokens[1:]);
    # Process ".main" definition.
    elif firstToken['value'] == '.main':
      if self.main:
        raise asmDef.AsmException('Second definition of ".main" at %s:%d' % (filename,firstToken['line']));
      self.main = self.ExpandTokens(filename,rawTokens[1:]);
    # Process ".memory" declaration.
    elif firstToken['value'] == '.memory':
      if len(rawTokens) != 3:
        raise asmDef.AsmException('".memory" directive requires exactly two arguments at %s:%d' % (filename, firstToken['line']));
      if (secondToken['type'] != 'symbol') or (secondToken['value'] not in ('RAM','ROM',)):
        raise asmDef.AsmException('First argument to ".memory" directive must be "RAM" or "RAM" at %s:%d:%d' % (filename,secondToken['line'],secondToken['col']));
      thirdToken = rawTokens[2];
      if thirdToken['type'] != 'symbol':
        raise asmDef.AsmException('".memory" directive requires name for second argument at %s:%d' % (filename,thirdToken['line']));
      if thirdToken['value'] in self.symbols['list']:
        ix = self.symbols['list'].index(thirdToken['value']);
        if self.symbols['type'] != secondToken['value']:
          raise asmDef.AsmException('Redefinition of ".memory %s %s" not allowed at %s:%d' % (secondToken['value'],thirdToken['value'],filename,firstToken['line']));
      else:
        self.AddSymbol(thirdToken['value'],secondToken['value'],dict(length=0));
      self.currentMemory = thirdToken['value'];
    # Process ".variable" declaration.
    elif firstToken['value'] == '.variable':
      if not self.currentMemory:
        raise asmDef.AsmException('".memory" directive required before ".variable" directive at %s:%d' % (filename,firstToken('line')));
      if secondToken['type'] != 'symbol':
        raise asmDef.AsmException('Bad variable name at %s:%d:%d' % (filename,secondToken['line'],secondToken['col']));
      ixMem = self.symbols['list'].index(self.currentMemory);
      currentMemoryBody = self.symbols['body'][ixMem];
      byteList = self.ByteList(filename,rawTokens[2:]);
      body = dict(memory=self.currentMemory, start=currentMemoryBody['length'], value=byteList);
      self.AddSymbol(secondToken['value'], 'variable', body=body);
      currentMemoryBody['length'] = currentMemoryBody['length'] + len(byteList);
      if currentMemoryBody['length'] > 256:
        raise asmDef.AsmException('Memory "%s" becomes too long at %s:%d' % (self.currentMemory,filename,firstToken['line']));
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

  def SymbolDict(self):
    """return a dict object usable by the eval function with the currently defines symbols"""
    t = dict();
    for ixSymbol in range(len(self.symbols['list'])):
      name = self.symbols['list'][ixSymbol];
      stype = self.symbols['type'][ixSymbol];
      if stype == 'constant':
        t[name] = self.symbols['body'][ixSymbol][0];
      elif stype == 'variable':
        t[name] = self.symbols['body'][ixSymbol]['start'];
    sizes=dict();
    for name in self.memoryLength:
      sizes[name] = self.memoryLength[name];
    t['size'] = sizes;
    return t;

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
          raise asmDef.AsmException('Empty memory:  %s' % self.symbols['list'][ix]);
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
      raise asmDef.AsmException('Too many memory banks');

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
          callName = token['argument'][0]['value'];
          if callName not in self.functionEvaluation['list']:
            if callName not in self.symbols['list']:
              raise asmDef.AsmException('Function "%s" not defined for function "%s"' % (callName,self.functionEvaluation['list'][ix],));
            ixName = self.symbols['list'].index(callName);
            if self.symbols['type'][ixName] != 'function':
              raise asmDef.AsmException('Function "%s" called by "%s" is not a function', (callName, self.functionEvaluation['list'][ix],));
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
          ix = labelAddress['list'].index(token['argument'][0]['value']);
          token['address'] = labelAddress['address'][ix];
        if (token['type'] == 'macro') and (token['value'] in ('.call','.callc',)):
          ix = self.functionEvaluation['list'].index(token['argument'][0]['value']);
          token['address'] = self.functionEvaluation['address'][ix];
    # Sanity checks for address range
    if self.functionEvaluation['address'][-1] + self.functionEvaluation['length'][-1] > 2**13-1:
      raise asmDef.AsmException('Max address for program requires more than 13 bits');
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

  def Emit_AddLabel(self,name):
    self.emitLabelList += ':' + name + ' ';

  def Emit_GetAddrAndBank(self,name):
    if name not in self.symbols['list']:
      raise asmDef.AsmException('"%s" is not a recognized symbol' % name);
    ixName = self.symbols['list'].index(name);
    if self.symbols['type'][ixName] != 'variable':
      raise asmDef.AsmException('"%s" is not a variable' % name);
    body = self.symbols['body'][ixName];
    ixMem = self.memories['list'].index(body['memory']);
    return (self.memories['bank'][ixMem],body['start'],);

  def Emit_GetBank(self,name):
    if name not in self.memories['list']:
      raise asmDef.AsmException('"%s" not a memory' % name);
    ixMem = self.memories['list'].index(name);
    return self.memories['bank'][ixMem];

  def EmitName(self,name):
    name = self.emitLabelList + name;
    self.emitLabelList = '';
    return name;

  def EmitOpcode(self,fp,opcode,name):
    fp.write('%03X %s\n' % (opcode,self.EmitName(name)));

  def EmitOptArg(self,fp,token):
    if token['type'] in ('constant','inport','outport','variable',):
      name = token['value'];
      if name not in self.symbols['list']:
        raise Exception('Program Bug');
      ix = self.symbols['list'].index(name);
      self.EmitPush(fp,self.symbols['body'][ix][0],self.EmitName(name));
    elif token['type'] == 'instruction':
      self.EmitOpcode(fp,self.InstructionOpcode(token['value']),token['value']);
    elif token['type'] == 'value':
      self.EmitPush(fp,token['value']);
    else:
      raise asmDef.AsmException('Unrecognized optional argument "%s"' % token['value']);

  def EmitPush(self,fp,value,name=None):
    if type(name) == str:
      fp.write('1%02X %s\n' % ((value % 0x100),self.EmitName(name)));
    elif (chr(value) in string.printable) and (chr(value) not in string.whitespace):
      fp.write('1%02X %02X %s\n' % ((value % 0x100),value,self.EmitName('\'%c\'' % value)));
    else:
      fp.write('1%02X %s\n' % ((value % 0x100),self.EmitName('0x%02X' % value)));

  def EmitVariable(self,fp,name):
    if name not in self.symbols['list']:
      raise asmDef.AsmException('Variable "%s" not recognized' % name);
    ixName = self.symbols['list'].index(name);
    body = self.symbols['body'][ixName];
    fp.write('1%02X %s\n' % (body['start'],self.EmitName(name)));
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
      self.emitLabelList = '';
      for token in self.functionEvaluation['body'][ix]:
        if token['type'] == 'value':
          self.EmitPush(fp,token['value']);
        elif token['type'] == 'label':
          self.Emit_AddLabel(token['value']);
        elif token['type'] == 'constant':
          if token['value'] not in self.symbols['list']:
            raise Exception('Program Bug');
          ix = self.symbols['list'].index(token['value']);
          body = self.symbols['body'][ix];
          self.EmitPush(fp,body[-1],token['value']);
          for v in body[-2::-1]:
            self.EmitPush(fp,v);
        elif token['type'] in ('inport','outport',):
          if token['value'] not in self.symbols['list']:
            raise Exception('Program Bug');
          ix = self.symbols['list'].index(token['value']);
          self.EmitPush(fp,self.symbols['body'][ix]['address'],token['value']);
        elif token['type'] == 'instruction':
          self.EmitOpcode(fp,self.InstructionOpcode(token['value']),token['value']);
        elif token['type'] == 'macro':
          if token['value'] == '.call':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['call'] | (token['address'] >> 8),'call '+token['argument'][0]['value']);
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.callc':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['callc'] | (token['address'] >> 8),'callc '+token['argument'][0]['value']);
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.fetch':
            name = token['argument'][0]['value'];
            ixBank = self.Emit_GetBank(name);
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch '+name);
          elif token['value'] == '.fetch-':
            name = token['argument'][0]['value'];
            ixBank = self.Emit_GetBank(name);
            self.EmitOpcode(fp,self.specialInstructions['fetch-'] | ixBank,'fetch- '+name);
          elif token['value'] == '.fetchindexed':
            ixBank = self.EmitVariable(fp,token['argument'][0]['value']);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch');
          elif token['value'] == '.fetchvalue':
            ixBank = self.EmitVariable(fp,token['argument'][0]['value']);
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch');
          elif token['value'] == '.fetchvector':
            name = token['argument'][0]['value']
            (addr,ixBank) = self.Emit_GetAddrAndBank(name);
            N = int(token['argument'][1]['value']);
            self.EmitPush(fp,addr+N-1,'%s+%d' % (name,N-1));
            for dummy in range(N-1):
              self.EmitOpcode(fp,self.specialInstructions['fetch-'] | ixBank,'fetch-');
            self.EmitOpcode(fp,self.specialInstructions['fetch'] | ixBank,'fetch');
          elif token['value'] == '.inport':
            name = token['argument'][0]['value'];
            self.EmitPush(fp,self.InportAddress(name) & 0xFF,name);
            self.EmitOpcode(fp,self.InstructionOpcode('inport'),'inport');
          elif token['value'] == '.jump':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['jump'] | (token['address'] >> 8),'jump '+token['argument'][0]['value']);
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.jumpc':
            self.EmitPush(fp,token['address'] & 0xFF,'');
            self.EmitOpcode(fp,self.specialInstructions['jumpc'] | (token['address'] >> 8),'jumpc '+token['argument'][0]['value']);
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.outport':
            name = token['argument'][0]['value'];
            self.EmitPush(fp,self.OutportAddress(name) & 0xFF,name);
            self.EmitOpcode(fp,self.InstructionOpcode('outport'),'outport');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          elif token['value'] == '.return':
            self.EmitOpcode(fp,self.specialInstructions['return'],'return');
            self.EmitOptArg(fp,token['argument'][0]);
          elif token['value'] == '.store':
            name = token['argument'][0]['value'];
            ixBank = self.Emit_GetBank(name);
            self.EmitOpcode(fp,self.specialInstructions['store'] | ixBank,'store '+name);
          elif token['value'] == '.store+':
            name = token['argument'][0]['value'];
            ixBank = self.Emit_GetBank(name);
            self.EmitOpcode(fp,self.specialInstructions['store+'] | ixBank,'store+ '+name);
          elif token['value'] == '.store-':
            name = token['argument'][0]['value'];
            ixBank = self.Emit_GetBank(name);
            self.EmitOpcode(fp,self.specialInstructions['store-'] | ixBank,'store- '+name);
          elif token['value'] == '.storeindexed':
            ixBank = self.EmitVariable(fp,token['argument'][0]['value']);
            self.EmitOpcode(fp,self.InstructionOpcode('+'),'+');
            self.EmitOpcode(fp,self.specialInstructions['store'] | ixBank,'store');
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.storevalue':
            ixBank = self.EmitVariable(fp,token['argument'][0]['value']);
            self.EmitOpcode(fp,self.specialInstructions['store'] | ixBank,'store');
            self.EmitOptArg(fp,token['argument'][1]);
          elif token['value'] == '.storevector':
            (addr,ixBank) = self.Emit_GetAddrAndBank(token['argument'][0]['value']);
            N = int(token['argument'][1]['value']);
            self.EmitPush(fp,addr+N-1,token['argument'][0]['value']);
            for dummy in range(N):
              self.EmitOpcode(fp,self.specialInstructions['store+'] | ixBank,'store+');
            self.EmitOpcode(fp,self.InstructionOpcode('drop'),'drop');
          else:
            raise Exception('Program Bug:  Unrecognized macro "%s"' % token['value']);
        elif token['type'] == 'symbol':
          self.EmitPush(fp,token['value'],token['name']);
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
    # Configure the instructions.
    #

    self.instructions = dict(list=list(), opcode=list());
    self.AddInstruction('&',            0x01A);
    self.AddInstruction('+',            0x018);
    self.AddInstruction('-',            0x019);
    self.AddInstruction('-1<>',         0x023);
    self.AddInstruction('-1=',          0x022);
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
    self.AddInstruction('inport',       0x030);
    self.AddInstruction('lsb>>',        0x007);
    self.AddInstruction('msb>>',        0x006);
    self.AddInstruction('nip',          0x01F);
    self.AddInstruction('nop',          0x000);
    self.AddInstruction('or',           0x01B);
    self.AddInstruction('outport',      0x038);
    self.AddInstruction('over',         0x00A);
    self.AddInstruction('r>',           0x049);
    self.AddInstruction('r@',           0x009);
    self.AddInstruction('swap',         0x012);

    self.specialInstructions = dict();
    self.specialInstructions['call']    = 0x0C0;
    self.specialInstructions['callc']   = 0x0E0;
    self.specialInstructions['fetch']   = 0x068;
    self.specialInstructions['fetch+']  = 0x078;
    self.specialInstructions['fetch-']  = 0x07C;
    self.specialInstructions['jump']    = 0x080;
    self.specialInstructions['jumpc']   = 0x0A0;
    self.specialInstructions['return']  = 0x028;
    self.specialInstructions['store']   = 0x060;
    self.specialInstructions['store+']  = 0x070;
    self.specialInstructions['store-']  = 0x074;

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

    self.macros = dict(list=list(), length=list(), args=list(), nArgs=list());
    self.AddMacro('.call',              3, [
                                             ['','symbol'],
                                             ['nop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.callc',             3, [
                                             ['','symbol'],
                                             ['drop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.fetch',             1, [ ['','symbol'] ]);
    self.AddMacro('.fetch+',            1, [ ['','symbol'] ]);
    self.AddMacro('.fetch-',            1, [ ['','symbol'] ]);
    self.AddMacro('.fetchindexed',      3, [
                                             ['','symbol'],
                                             ['','singlevalue','symbol']
                                           ]);
    self.AddMacro('.fetchvalue',        2, [ ['','symbol'] ]);
    self.AddMacro('.fetchvector',      -1, [
                                             ['','symbol'],
                                             ['','singlevalue','symbol']
                                           ]);
    self.AddMacro('.inport',            2, [ ['','symbol'] ]);
    self.AddMacro('.jump',              3, [
                                             ['','symbol'],
                                             ['nop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.jumpc',             3, [
                                             ['','symbol'],
                                             ['drop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.outport',           3, [
                                             ['','symbol'],
                                             ['drop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.return',            2, [ ['nop','instruction','singlevalue','symbol'] ]);
    self.AddMacro('.store',             1, [ ['','symbol'] ]);
    self.AddMacro('.store+',            1, [ ['','symbol'] ]);
    self.AddMacro('.store-',            1, [ ['','symbol'] ]);
    self.AddMacro('.storeindexed',      4, [
                                             ['','symbol'],
                                             ['drop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.storevalue',        3, [
                                             ['','symbol'],
                                             ['drop','instruction','singlevalue','symbol']
                                           ]);
    self.AddMacro('.storevector',      -1, [
                                             ['','symbol'],
                                             ['','singlevalue','symbol'],
                                           ]);

    #
    # Externally defined parameters.
    #

    self.memoryLength = dict();

    #
    # Configure the containers for the expanded main, interrupt, function,
    # macro, etc. definitions.
    #

    self.interrupt = list();
    self.main = list();
    self.symbols = dict(list=list(), type=list(), body=list());
    self.currentMemory = None;
