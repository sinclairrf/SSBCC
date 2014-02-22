# Copyright 2014, Sinclair R.F., Inc.

def push32(ad):
  """
  User-defined macro to push a 32 bit value onto the data stack so that the LSB
  is deepest in the data stack and the MSB is at the top of the data stack.
  Usage:
    .push32(v)
  where
    v           is a 32-bit value, a constant, or an evaluated expression\n
  The effect is to push v%0x100, int(v/2**8)%0x100, int(v/2**16)%0x100, and
  int(v/2**24)%0x100 onto the data stack.\n
  ( - u_LSB u u u_MSB )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.push32', 4, [ ['','singlevalue','symbol'] ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,token):
    token = token[0];
    if token['type'] == 'value':
      v = token['value'];
    elif token['type'] == 'symbol':
      name = token['value'];
      if not ad.IsSymbol(name):
        raise asmDef.AsmException('Symbol "%s" not recognized at %s' % (token['value'],token['loc'],));
      ix = ad.symbols['list'].index(name);
      v = ad.symbols['body'][ix];
      if len(v) != 1:
        raise asmDef.AsmException('Argument can only be one value at %s' % token['loc']);
      v = v[0];
    else:
      raise asmDef.AsmException('Argument "%s" of type "%s" not recognized at %s' % (token['value'],token['type'],token['loc'],));
    if type(v) != int:
      raise Exception('Program Bug -- value should be an "int"');
    ad.EmitPush(fp,v%0x100); v >>= 8;
    ad.EmitPush(fp,v%0x100); v >>= 8;
    ad.EmitPush(fp,v%0x100); v >>= 8;
    ad.EmitPush(fp,v%0x100,'.push32(xxx)');
  ad.EmitFunction['.push32'] = emitFunction;
