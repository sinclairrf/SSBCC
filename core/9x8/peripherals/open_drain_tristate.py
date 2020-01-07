################################################################################
#
# Copyright 2020, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class open_drain_tristate(SSBCCperipheral):
  """
  The documentation is recorded in the file open_drain_tristate.md.
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'basesignal',   r'\w+$',        None,   ),
      ( 'inport',       r'I_\w+$',      None,   ),
      ( 'outport',      r'O_\w+$',      None,   ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the required parameters are set.
    for paramname in names:
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    tristate_i = 'i_%s_i' % self.basesignal
    tristate_o = 'o_%s_o' % self.basesignal
    tristate_t = 'o_%s_t' % self.basesignal
    config.AddIO(tristate_i,1,'input',loc)
    config.AddIO(tristate_o,1,'output',loc)
    config.AddIO(tristate_t,1,'output',loc)
    config.AddInport((self.inport,
                     (tristate_i,1,'data',),
                    ),
                    loc)
    config.AddOutport((self.outport,False,
                      (tristate_t,1,'data',"1'b1",),
                     ),
                     loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
        ( r'@BASESIGNAL@',      self.basesignal, ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
