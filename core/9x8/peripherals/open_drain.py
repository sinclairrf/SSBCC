################################################################################
#
# Copyright 2012-2014, Sinclair R.F., Inc.
# Copyright 2020, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class open_drain(SSBCCperipheral):
  """
  The documentation is recorded in the file open_drain.md.
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'inport',       r'I_\w+$',      None,   ),
      ( 'iosignal',     r'io_\w+$',     None,   ),
      ( 'outport',      r'O_\w+$',      None,   ),
      ( 'width',        r'\S+$',        lambda v : self.IntMethod(config,v,lowLimit=1,highLimit=config.Get('data_width')), ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Ensure the required parameters are set.
    for paramname in ('inport','iosignal','outport',):
      if not hasattr(self,paramname):
        raise SSBCCException('Required parameter "%s" is missing at %s' % (paramname,loc,))
    # Set defaults for non-specified values.
    if not hasattr(self,'width'):
      self.width = 1
    # Create the internal signal name and initialization.
    self.sname = 's__%s' % self.iosignal
    sname_init = '%d\'b%s' % (self.width, '1'*self.width, )
    # Add the I/O port, internal signals, and the INPORT and OUTPORT symbols for this peripheral.
    config.AddIO(self.iosignal,self.width,'inout',loc)
    config.AddSignalWithInit(self.sname,self.width,None,loc)
    config.AddInport((self.inport,
                     (self.iosignal,self.width,'data',),
                    ),
                    loc)
    config.AddOutport((self.outport,False,
                      (self.sname,self.width,'data',sname_init,),
                     ),
                     loc)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if self.width == 1:
      body = re.sub(r'@NARROW_BEGIN@','',body)
      body = re.sub(r'@NARROW_END@','',body)
      body = re.sub(r'@WIDE_BEGIN@.*?@WIDE_END@','',body,flags=re.DOTALL)
    else:
      body = re.sub(r'@NARROW_BEGIN@.*?@NARROW_END@','',body,flags=re.DOTALL)
      body = re.sub(r'@WIDE_BEGIN@','',body)
      body = re.sub(r'@WIDE_END@','',body)
    for subpair in (
        ( r'\bix\b',            'ix__@IOSIGNAL@', ),
        ( r'@IOSIGNAL@',        self.iosignal, ),
        ( r'@WIDTH@',           str(self.width), ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
