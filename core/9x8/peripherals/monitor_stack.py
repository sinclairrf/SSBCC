################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import re

class monitor_stack:
  """Simulation-specific peripheral to flag invalid data stack operations and to
  flag invalid return statck operatons.

  Invalid data stack operations are:
    pushing onto a full data stack
    dropping from an empty data stack
    nipping from an almost empty data stack
    in-place operations on an empty or almost empty data stack

  Invalid return stack operations are:
    pushing onto a full return stack
    dropping values from an empty return stack
    returns from a data entry on the return stack
    non-return  operations from an address entry on the return stack

  Usage:
    PERIPHERAL monitor_stack \\
      [help] \\
      [nofinish|finish=n] \\
      log=filename
  Where:
    help
      prints this message and terminates the computer compiler
    nofinish
      do not terminate the simulation when an error is encountered
    finish=n
      terminate the simulation n processor clock cycles after an error is
      encountered
      Note:  The normal behavior is to terminate the simulation when an error is
             encountered.
    log=filename
      store a trace of the simulation in filename
  """

  def __init__(self,config.param_strings):
    pass;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp.config):
    pass;
