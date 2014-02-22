# Copyright 2014, Sinclair R.F., Inc.

def fetchoffset(ad):
  """
  Built-in macro to copy the value at the specified offset into the specified
  variable to the top of the data stack.\n
  Usage:
    .fetchoffset(variable,ix)
  where
    variable    is a variable
    ix          is the index into the variable\n
  The effect is:  T = variable[ix]\n
  ( - u_mem )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.fetchoffset', 2, [
                                   ['','symbol'],
                                   ['','singlevalue','symbol']
                                 ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    name = argument[0]['value'];
    (addr,ixBank,bankName) = ad.Emit_GetAddrAndBank(name);
    offset = ad.Emit_EvalSingleValue(argument[1]);
    ad.EmitPush(fp,addr+offset,ad.Emit_String('%s+%s' % (name,offset,)),argument[0]['loc']);
    ad.EmitOpcode(fp,ad.specialInstructions['fetch'] | ixBank,'fetch '+bankName);
  ad.EmitFunction['.fetchoffset'] = emitFunction;
