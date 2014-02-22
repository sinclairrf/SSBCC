# Copyright 2014, Sinclair R.F., Inc.

def fetchvector(ad):
  """
  Built-in macro to move multiple bytes from memory to the data stack.  The byte
  at the specified memory address is stored at the top of the data stack with
  subsequent bytes store below it.\n
  Usage:
    .fetchvector(variable,N)
  where
    variable    is the name of a variable
    N           is the constant number of bytes to transfer\n
  The effect is to push the values u_LSB=variable[N-1], ..., u_msb=variable[0]
  onto the data stack.\n
  ( - u_LSB ... u_MSB )
  """

  def length(ad,argument):
    return int(argument[1]['value']) + 1;

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.fetchvector', length, [
                                        ['','symbol'],
                                        ['','singlevalue','symbol']
                                      ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    variableName = argument[0]['value'];
    (addr,ixBank,bankName) = ad.Emit_GetAddrAndBank(variableName);
    N = int(argument[1]['value']);
    ad.EmitPush(fp,addr+N-1,'%s+%d' % (variableName,N-1));
    for dummy in range(N-1):
      ad.EmitOpcode(fp,ad.specialInstructions['fetch-'] | ixBank,'fetch- '+bankName);
    ad.EmitOpcode(fp,ad.specialInstructions['fetch'] | ixBank,'fetch '+bankName);
  ad.EmitFunction['.fetchvector'] = emitFunction;
