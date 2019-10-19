################################################################################
#
# Copyright 2012-2014, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

import math
import re

from ssbccPeripheral import SSBCCperipheral
from ssbccUtil import SSBCCException

class monitor_stack(SSBCCperipheral):
  """
  The documentation is recorded in the file monitor_stack.md
  """

  def __init__(self,peripheralFile,config,param_list,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # Get the parameters.
    allowables = (
      ( 'history',      r'[1-9]\d*$',   int,    ),
    )
    names = [a[0] for a in allowables]
    for param_tuple in param_list:
      param = param_tuple[0]
      if param not in names:
        raise SSBCCException('Unrecognized parameter "%s" at %s' % (param,loc,))
      param_test = allowables[names.index(param)]
      self.AddAttr(config,param,param_tuple[1],param_test[1],loc,param_test[2])
    # Set optional parameters.
    if not hasattr(self,'history'):
      self.history = 50
    # Configure the system for this peripheral.
    config.functions['display_trace'] = True

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    if not config.InterruptVector():
      for replace in (r's_interrupt\b',r's_interrupted\b',):
        body = re.sub(replace,'1\'b0',body)
    outport_pure_strobe = ''
    for ix in range(config.NOutports()):
      thisPort = config.outports[ix][2:]
      thisIsStrobe = True
      for jx in range(len(thisPort)):
        signal = thisPort[jx]
        signalType = signal[2]
        if signalType == 'data':
          thisIsStrobe = False
        elif signalType == 'strobe':
          pass
        else:
          raise Exception('Program Bug:  Unrecognized outport signal type "%s"' % signalType)
      if thisIsStrobe:
        if len(outport_pure_strobe) > 0:
          outport_pure_strobe += ' || '
        outport_pure_strobe += ('(s_T == 8\'h%02X)' % ix)
    if len(outport_pure_strobe) == 0:
      outport_pure_strobe = '1\'b0'
    outport_pure_strobe = 'wire s__outport_pure_strobe = ' + outport_pure_strobe + ';'
    for subpair in (
        ( r'\\bix__',                   'ix__monitor_stack__', ),
        ( r'\\bs__',                    's__monitor_stack__', ),
        ( r'@CORENAME@',                config.Get('outCoreName'), ),
        ( r'@HISTORY@',                 str(self.history), ),
        ( r'@HISTORY-1@',               str(self.history-1), ),
        ( r'@LAST_INPORT@',             '9\'h%03X' % config.NInports(), ),
        ( r'@LAST_OUTPORT@',            '9\'h%03X' % config.NOutports(), ),
        ( r'@NINSTRUCTIONS-1@',         str(config.Get('nInstructions')['length']-1), ),
        ( r'@OUTPORT_PURE_STROBE@',     outport_pure_strobe, ),
        ( r'@UC_CLK@',                  'i_clk', ),
        ( r'@UC_RST@',                  'i_rst', ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    for ixBank in range(4):
      memParam = config.GetMemoryByBank(ixBank)
      if memParam:
        maxLength = memParam['maxLength']
      else:
        maxLength = 0
      body = re.sub('@MEM_LIMIT_%d@' % ixBank, str(maxLength), body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
