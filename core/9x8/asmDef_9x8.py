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

  def InstructionOpcode(self,symbolName,language):
    if not self.IsInstruction(symbolName):
      raise Exception('Program Bug:  %s not in instruction list' % symbolName);
    ix = self.instruction['list'].index(symbolName);
    return self.instruction['opcode'][ix];

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
    elif firstToken['value'] == '.interrupt':
      if self.interrupt:
        raise Exception('Second definition of ".interrupt" at %s(%d)' % (filename,firstToken['line']));
      self.interrupt = self.ExpandTokens(filename,rawTokens[1:]);
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
    self.AddInstruction('-1=',          0x021);
    self.AddInstruction('0=',           0x020);
    self.AddInstruction('0>>',          0x004);
    self.AddInstruction('1>>',          0x005);
    self.AddInstruction('<<0',          0x001);
    self.AddInstruction('<<1',          0x002);
    self.AddInstruction('<<msb',        0x003);
    self.AddInstruction('>r',           0x058);
    self.AddInstruction('^',            0x01C);
    self.AddInstruction('call',         0x040);
    self.AddInstruction('callc',        0x048);
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
    self.AddInstruction('r>',           0x061);
    self.AddInstruction('r@',           0x009);
    self.AddInstruction('swap',         0x012);
