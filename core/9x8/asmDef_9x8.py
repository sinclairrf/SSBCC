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
  # Configure the class for processing directives.
  #
  ################################################################################

  def fn_directiveConstant(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveFunction(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveInclude(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveInterrupt(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveMacro(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveMain(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveMemory(methodName):
    raise Exception('Wrong or unimplemented argument');

  def fn_directiveVariable(methodName):
    raise Exception('Wrong or unimplemented argument');

  directives = dict();
  directives['predefined']= list();
  directives['predefined'].append(dict(name='.constant',    method=fn_directiveConstant));
  directives['predefined'].append(dict(name='.function',    method=fn_directiveFunction));
  directives['predefined'].append(dict(name='.include',     method=fn_directiveInclude));
  directives['predefined'].append(dict(name='.interrupt',   method=fn_directiveInterrupt));
  directives['predefined'].append(dict(name='.macro',       method=fn_directiveMacro));
  directives['predefined'].append(dict(name='.main',        method=fn_directiveMain));
  directives['predefined'].append(dict(name='.memory',      method=fn_directiveMemory));
  directives['predefined'].append(dict(name='.variable',    method=fn_directiveVariable));

  directives['list'] = list();
  for directive in directives['predefined']:
    directives['list'].append(directive['name']);

  def IsDirective(self,name):
    return name in self.directives['list'];

  ################################################################################
  #
  # Configure the class for identifying and processing macros.
  #
  ################################################################################

  def fn_macroCall(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroCallc(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetch(methodName):
    if methodName == 'length':
      return 2;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetchIndexed(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroInport(methodName):
    if methodName == 'length':
      return 1;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJump(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJumpc(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroOutport(methodName):
    if methodName == 'length':
      return 2;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroReturn(methodName):
    if methodName == 'length':
      return 2;
    if methodName == 'number of arguments':
      return 0;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStore(methodName):
    if methodName == 'length':
      return 3;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStoreIndexed(methodName):
    if methodName == 'length':
      return 4;
    if methodName == 'number of arguments':
      return 1;
    raise Exception('Wrong or unimplemented argument');

  macros = dict();

  macros['predefined']= list();
  macros['predefined'].append(dict(name='.call',        method=fn_macroCall));
  macros['predefined'].append(dict(name='.callc',       method=fn_macroCallc));
  macros['predefined'].append(dict(name='.fetch',       method=fn_macroFetch));
  macros['predefined'].append(dict(name='.fetchindexed',method=fn_macroFetchIndexed));
  macros['predefined'].append(dict(name='.inport',      method=fn_macroInport));
  macros['predefined'].append(dict(name='.jump',        method=fn_macroJump));
  macros['predefined'].append(dict(name='.jumpc',       method=fn_macroJumpc));
  macros['predefined'].append(dict(name='.outport',     method=fn_macroOutport));
  macros['predefined'].append(dict(name='.return',      method=fn_macroReturn));
  macros['predefined'].append(dict(name='.store',       method=fn_macroStore));
  macros['predefined'].append(dict(name='.storeindexed',method=fn_macroStoreIndexed));

  macros['list'] = list();
  for macro in macros['predefined']:
    macros['list'].append(macro['name']);

  def IsMacro(self,name):
    return name in self.macros['list'];

  def MacroNumberArgs(self,name):
    if name not in self.macros['list']:
      raise Exception('Program bug:  macro "%s" not a macro' % name);
    i = self.macros['list'].index(name);
    return self.macros['predefined'][i]['method']('number of arguments');

  ################################################################################
  #
  # Configure the class for processing instructions.
  #
  ################################################################################

  instructions = dict();

  instructions['opcodes'] = list();
  instructions['opcodes'].append(dict(name='&',         opcode=0x01A));
  instructions['opcodes'].append(dict(name='+',         opcode=0x018));
  instructions['opcodes'].append(dict(name='-',         opcode=0x019));
  instructions['opcodes'].append(dict(name='-1=',       opcode=0x021));
  instructions['opcodes'].append(dict(name='0=',        opcode=0x020));
  instructions['opcodes'].append(dict(name='0>>',       opcode=0x004));
  instructions['opcodes'].append(dict(name='1>>',       opcode=0x005));
  instructions['opcodes'].append(dict(name='<<0',       opcode=0x001));
  instructions['opcodes'].append(dict(name='<<1',       opcode=0x002));
  instructions['opcodes'].append(dict(name='<<msb',     opcode=0x003));
  instructions['opcodes'].append(dict(name='>r',        opcode=0x058));
  instructions['opcodes'].append(dict(name='^',         opcode=0x01C));
  instructions['opcodes'].append(dict(name='call',      opcode=0x040));
  instructions['opcodes'].append(dict(name='callc',     opcode=0x048));
  instructions['opcodes'].append(dict(name='dis',       opcode=0x01C));
  instructions['opcodes'].append(dict(name='drop',      opcode=0x01E));
  instructions['opcodes'].append(dict(name='dup',       opcode=0x008));
  instructions['opcodes'].append(dict(name='ena',       opcode=0x019));
  instructions['opcodes'].append(dict(name='inport',    opcode=0x030));
  instructions['opcodes'].append(dict(name='lsb>>',     opcode=0x007));
  instructions['opcodes'].append(dict(name='msb>>',     opcode=0x006));
  instructions['opcodes'].append(dict(name='nip',       opcode=0x01F));
  instructions['opcodes'].append(dict(name='nop',       opcode=0x000));
  instructions['opcodes'].append(dict(name='or',        opcode=0x01B));
  instructions['opcodes'].append(dict(name='outport',   opcode=0x038));
  instructions['opcodes'].append(dict(name='over',      opcode=0x00A));
  instructions['opcodes'].append(dict(name='r>',        opcode=0x061));
  instructions['opcodes'].append(dict(name='r@',        opcode=0x009));
  instructions['opcodes'].append(dict(name='swap',      opcode=0x012));

  instructions['list'] = list();
  for instruction in instructions['opcodes']:
    instructions['list'].append(instruction['name']);

  def IsInstruction(self,name):
    return name in self.instructions['list'];

  def InstructionOpcode(self,symbolName,language):
    for instruction in self.instructions['opcodes']:
      if instruction['name'] == symbolName:
        if language == 'Verilog':
          return '9\'h%03x' % (instruction['opcode']);
        raise Exception('Unrecognized language: ' + language);
    raise Exception('Wrong or unimplemented instruction');

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
    # Ensure local lables are defined and used.
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
