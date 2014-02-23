# Copyright 2014, Sinclair R.F., Inc.

def push16(ad):
  """
  User-defined macro to push a 16 bit value onto the data stack so that the LSB
  is deepest in the data stack and the MSB is at the top of the data stack.\n
  Usage:
    .push16(v)
  where
    v           is a 16-bit value, a constant, or an evaluated expression\n
  The effect is to push v%0x100 and int(v/2**8)%0x100 onto the data stack.\n
  ( - u_LSB u u u_MSB )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.push16', 2, [ ['','singlevalue','symbol'] ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    argument = argument[0];
    if argument['type'] == 'value':
      v = argument['value'];
    elif argument['type'] == 'symbol':
      name = argument['value'];
      if not ad.IsSymbol(name):
        raise asmDef.AsmException('Symbol "%s" not recognized at %s' % (argument['value'],argument['loc'],));
      ix = ad.symbols['list'].index(name);
      v = ad.symbols['body'][ix];
      if len(v) != 1:
        raise asmDef.AsmException('Argument can only be one value at %s' % argument['loc']);
      v = v[0];
    else:
      raise asmDef.AsmException('Argument "%s" of type "%s" not recognized at %s' % (argument['value'],argument['type'],argument['loc'],));
    if type(v) != int:
      raise Exception('Program Bug -- value should be an "int"');
    ad.EmitPush(fp,v%0x100,''); v >>= 8;
    printValue = argument['value'] if type(argument['value']) == str else '0x%08X' % argument['value'];
    ad.EmitPush(fp,v%0x100,'.push16(%s)' % printValue);
  ad.EmitFunction['.push16'] = emitFunction;
