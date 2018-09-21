# Copyright 2014, Sinclair R.F., Inc.

def pushByte(ad):
  """
  User-defined macro to push a specific byte of a multi-byte value onto the data
  stack.\n
  Usage:
    .pushByte(v,ix)
  where
    v           is a multi-byte value, a constant, or an evaluated expression
    ix          is the index to the byte to push (ix=0 ==> push the LSB, ...)\n
  The effect is to push "(v/256**ix) % 0x100" onto the data stack.\n
  ( - u_byte )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.pushByte', 1, [
                                ['','singlevalue','symbol'],
                                ['','singlevalue','symbol'],
                              ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    v  = ad.Emit_IntegerValue(argument[0]);
    ix = ad.Emit_IntegerValue(argument[1]);
    if ix < 0:
      raise asmDef.AsmException('ix must be non-negative in .pushByte at %s' % argument[1]['loc']);
    v = int(v/256**ix) % 0x100;
    printValue = argument[0]['value'] if type(argument[0]['value']) == str else '0x%X' % argument[0]['value'];
    printIx    = argument[1]['value'] if type(argument[1]['value']) == str else '0x%X' % argument[1]['value'];
    ad.EmitPush(fp,v,'.pushByte(%s,%s)' % (printValue,printIx,));

  ad.EmitFunction['.pushByte'] = emitFunction;
