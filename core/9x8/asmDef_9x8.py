################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Assembly language definitions for SSBCC 9x8.
#
################################################################################

class asmDef_9x8:
  """SSBCC 9x8 assembler definitions"""

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

  ################################################################################
  #
  # Configure the class for identifying and processing macros.
  #
  ################################################################################

  def fn_macroCall(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroCallc(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetch(methodName):
    if methodName == 'length':
      return 2;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetchIndexed(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJump(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJumpc(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroReturn(methodName):
    if methodName == 'length':
      return 2;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStore(methodName):
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStoreIndexed(methodName):
    if methodName == 'length':
      return 4;
    raise Exception('Wrong or unimplemented argument');

  macros = dict();

  macros['predefined']= list();
  macros['predefined'].append(dict(name='.call',        method=fn_macroCall));
  macros['predefined'].append(dict(name='.callc',       method=fn_macroCallc));
  macros['predefined'].append(dict(name='.fetch',       method=fn_macroFetch));
  macros['predefined'].append(dict(name='.fetchindexed',method=fn_macroFetchIndexed));
  macros['predefined'].append(dict(name='.jump',        method=fn_macroJump));
  macros['predefined'].append(dict(name='.jumpc',       method=fn_macroJumpc));
  macros['predefined'].append(dict(name='.return',      method=fn_macroReturn));
  macros['predefined'].append(dict(name='.store',       method=fn_macroStore));
  macros['predefined'].append(dict(name='.storeindexed',method=fn_macroStoreIndexed));

  macros['directives'] = list();
  for macro in macros['predefined']:
    macros['directives'].append(macro['name']);

  def IsDirective(self,macroName):
    return macroName in self.macros['directives'];

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

  def IsInstruction(self,symbolName):
    return symbolName in self.instructions['list'];

  def InstructionOpcode(self,symbolName,language):
    for instruction in self.instructions['opcodes']:
      if instruction['name'] == symbolName:
        if language == 'Verilog':
          return '9\'h%03x' % (instruction['opcode']);
        raise Exception('Unrecognized language: ' + language);
    raise Exception('Wrong or unimplemented instruction');
