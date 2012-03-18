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
  # Configure the class for identifying and processing macros.
  #
  ################################################################################

  macros = dict();

  def fn_macroCall(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroCallc(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroConstant(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetch(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 2;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFetchIndexed(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroFunction(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroInclude(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroInterrupt(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJump(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroJumpc(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroMacro(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroMain(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroMemory(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroReturn(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 2;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStore(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 3;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroStoreIndexed(methodName):
    if methodName == 'isDirective':
      return False;
    if methodName == 'length':
      return 4;
    raise Exception('Wrong or unimplemented argument');

  def fn_macroVariable(methodName):
    if methodName == 'isDirective':
      return True;
    raise Exception('Wrong or unimplemented argument');

  macros['predefined']= list();
  macros['predefined'].append(dict(name='.call',        method=fn_macroCall));
  macros['predefined'].append(dict(name='.callc',       method=fn_macroCallc));
  macros['predefined'].append(dict(name='.constant',    method=fn_macroConstant));
  macros['predefined'].append(dict(name='.fetch',       method=fn_macroFetch));
  macros['predefined'].append(dict(name='.fetchindexed',method=fn_macroFetchIndexed));
  macros['predefined'].append(dict(name='.function',    method=fn_macroFunction));
  macros['predefined'].append(dict(name='.include',     method=fn_macroInclude));
  macros['predefined'].append(dict(name='.interrupt',   method=fn_macroInterrupt));
  macros['predefined'].append(dict(name='.jump',        method=fn_macroJump));
  macros['predefined'].append(dict(name='.jumpc',       method=fn_macroJumpc));
  macros['predefined'].append(dict(name='.macro',       method=fn_macroMacro));
  macros['predefined'].append(dict(name='.main',        method=fn_macroMain));
  macros['predefined'].append(dict(name='.memory',      method=fn_macroMemory));
  macros['predefined'].append(dict(name='.return',      method=fn_macroReturn));
  macros['predefined'].append(dict(name='.store',       method=fn_macroStore));
  macros['predefined'].append(dict(name='.storeindexed',method=fn_macroStoreIndexed));
  macros['predefined'].append(dict(name='.variable',    method=fn_macroVariable));

  macros['directives'] = list();
  for macro in macros['predefined']:
    if macro['method']('isDirective'):
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

  def InstructionOpcode(self,symbolName):
    for instruction in instructions['opcodes']:
      if instruction['name'] == symbolName:
        return instruction['opcode'];
    raise Exception('Wrong or unimplemented instruction');
