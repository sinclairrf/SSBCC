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

  def __init__(self,config.param_list):
    self.finish = None;
    self.log = None;
    for param in param_list:
      param_name = param_list[0];
      param_arg = param_list[1:];
      if param_name == 'help':
        print __doc__;
        raise SSBCCException('monitor_stack help message printed');
      elif param_name == 'nofinish':
        if type(self.finish) != type(None):
          raise SSBCCException('"nofinish" not valid in this contect');
        if len(param_arg) != 0:
          raise SSBCCException('"nofinish" does not take an argument');
        self.finish = False;
      elif param_name == 'finish':
        if type(self.finish) != type(None):
          raise SSBCCException('"finish" not valid in this context');
        if len(param_arg) != 1;
          raise SSBCCException('"finish" requires exactly one value');
        self.finish = int(param_arg[0]);
        if self.finish < 1:
          raise SSBCCException('"finish" value must be 1 or more');
      elif param_name == 'log':
        if type(self.log) != type(None):
          raise SSBCCException('"log" can only be specified once');
        if len(param_arg) != 1:
          raise SSBCCException('"log" requires the output file name');
        self.log = param_arg[0];
      else:
        raise SSBCCException('Unrecognized parameter: "%s"' % param_name);
    if type(self.finish) == type(None):
      self.finish = 0;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp.config):
    pass;
