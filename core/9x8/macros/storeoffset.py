# Copyright 2014, Sinclair R.F., Inc.

def storeoffset(ad):
  """
  Built-in macro to store the top of the data stack at the specified offset
  into the specified variable.\n
  Usage:
    <v> .storeoffset(variable,ix[,op])
  where:
    <v>         is the value to be stored
    variable    is the name of the variable
    ix          is the index into the variable
    op          is an optional instruction to override the default "drop"
                instruction at the end of the instruction sequence\n
  The effect is:  variable[ix] = v\n
  ( v - )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.storeoffset', 3, [
                                   ['','symbol'],
                                   ['','singlevalue','symbol'],
                                   ['drop','instruction','singlemacro','singlevalue','symbol']
                                 ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    (addr,ixBank,bankName) = ad.Emit_GetAddrAndBank(argument[0]);
    offset = ad.Emit_EvalSingleValue(argument[1]);
    ad.EmitPush(fp,addr+offset,ad.Emit_String('%s+%s' % (argument[0]['value'],offset,)),argument[0]['loc']);
    ad.EmitOpcode(fp,ad.specialInstructions['store'] | ixBank,'store '+bankName);
    ad.EmitOptArg(fp,argument[2]);

  ad.EmitFunction['.storeoffset'] = emitFunction;
