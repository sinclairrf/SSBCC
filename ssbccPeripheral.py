################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import re

from ssbccUtil import SSBCCException

class SSBCCperipheral:
  """Base class for peripherals"""

  def __init__(self,peripheralFile,config,param_list,ixLine):
    """
    Prototype constructor.
    peripheralFile      the full path name of the peripheral source
                        Note:  "__file__" doesn't work because 'execfile" and
                        "exec" are used to load the python script for the
                        peripheral.
    config              the ssbccConfig object for the processor core
    param_list          parameter list for the processor
    ixLine              line number for the peripheral in the architecture file
    """
    pass;

  def AddAttr(self,config,name,value,reformat,ixLine):
    """
    Add attribute to the peripheral:
    config      ssbccConfig object for the procedssor core
    name        attribute name
    value       possibly optional value for the attribute
    reformat    regular expression format for the attribute value
                Note:  reformat=None means the attribute can only be set to True
    ixLine      line number for the peripheral for error messages
    """
    if hasattr(self,name):
      raise SSBCCException('%s repeated at line %d' % (name,ixLine,));
    if reformat == None:
      if value != None:
        raise SSBCCException('No parameter allowed for %s at line %d' % (name,ixLine,));
      setattr(self,name,True);
    else:
      if value == None:
        raise SSBCCException('%s missing value at line %d' % (name,ixLine,));
      if not re.match(reformat,value):
        raise SSBCCException('Inport symbol at line %d does not match required format "%s":  "%s"' % (ixLine,reformat,value,));
      setattr(self,name,value);

  def GenAssembly(self,config):
    """
    Used to generate any assembly modules associated with the peripheral.
    """
    pass;

  def GenHDL(self,fp,config):
    """
    Generate the peripheral HDL.
    fp          file pointer for the output processor
    config      ssbccConfig object for the procedssor core
    """
    if config.Get('hdl') == 'Verilog':
      self.GenVerilog(fp,config);
    elif config.Get('hdl') == 'VHDL':
      self.GenVHDL(fp,config);
    else:
      raise SSBCCException('HDL "%s" not implemented' % config.Get('hdl'));

  def GenVerilog(self,fp,config):
    """
    Generate the Verilog version of the peripheral.
    Raise an exception if there is no Verilog version of the peripheral.
    """
    raise Exception('Verilog is not implemented for this peripheral');

  def GenVerilogFinal(self,config,body):
    """
    Clean up the peripheral code.
    Change "$clog2" to "clog2" for simulators and synthesis tools that don't
      recognize or process "$clog2."
    """
    if config.Get('define_clog2'):
      body = re.sub('\$clog2','clog2',body);
    return body;

  def GenVHDL(self,fp,config):
    """
    Generate the VHDL version of the peripheral.
    Raise an exception if there is no VHDL version of the peripheral.
    """
    raise Exception('VHDL is not implemented for this peripheral');

  def IsInt(self,value):
    """
    Test the string to see if it is a well-formatted integer.
    Allow underscores as per Verilog.
    """
    if re.match(r'[1-9][0-9_]*$',value):
      return True;
    else:
      return False;

  def IsIntExpr(self,value):
    """
    Test the string to see if it is a well-formatted integer or multiplication
    of two integers.
    Allow underscores as per Verilog.
    """
    if re.match(r'[1-9][0-9_]*',value):
      return True;
    elif re.match(r'\([1-9][0-9_]*(\*[1-9][0-9_]*)+\)',value):
      return True;
    else:
      return False;

  def IsParameter(self,config,name):
    """
    See if the provided symbol name is a parameter in the processor core.
    config      ssbccConfig object for the procedssor core
    name        symbol name
    """
    return config.IsParameter(name);

  def LoadCore(self,filename,extension):
    """
    Read the source HDL for the peripheral from the same directory as the python
    script.
    filename    name for the python peripheral (usually "__file__")
    extension   the string such as ".v" or ".vhd" required by the HDL
    """
    hdlName = re.sub(r'\.py$',extension,filename);
    fp = open(hdlName,'r');
    body = fp.read();
    fp.close();
    return body;

  def ParseInt(self,value):
    """
    Convert a well-formatted integer string to an integer.
    Allow underscores as per Verilog.
    Note:  If this routine is called, then the value should have already been
           verified to be a well-formatted integer string.
    """
    if not self.IsInt(value):
      raise Exception('Program Bug -- shouldn\'t call with a badly formatted integer');
    return int(re.sub('_','',value));

  def ParseIntExpr(self,value):
    """
    Convert a string containing well-formatted integer or multiplication of two
    integers.
    Allow underscores as per Verilog.
    Note:  If this routine is called, then the value should have already been
           verified to be a well-formatted integer string.
    """
    if not self.IsIntExpr(value):
      raise Exception('Program Bug -- shouldn\'t call with a badly formatted integer expression');
    return eval(re.sub('_','',value));
