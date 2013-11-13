################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math
import re

################################################################################
#
# Classes
#
################################################################################

class SSBCCException(Exception):
  """
  Exception class for ssbcc.
  """
  def __init__(self,message):
    self.message = message;
  def __str__(self):
    return self.message;

################################################################################
#
# Methods
#
################################################################################

def CeilLog2(v):
  """
  Return the smallest integer that has a power of 2 greater than or equal to
  the argument.
  """
  tmp = int(math.log(v,2));
  while 2**tmp < v:
    tmp = tmp + 1;
  return tmp;

def CeilPow2(v):
  """
  Return the smallest power of 2 greater than or equal to the argument.
  """
  return 2**CeilLog2(v);

def ExtractBits(v,bits):
  """
  Extract the bits specified by bits from v.
  bits must have a Verilog-type format.  I.e., [7:0], [0+:8], etc.
  """
  if type(v) != int:
    raise SSBCCException('%s must be an int' % v);
  if re.match(r'[[]\d+:\d+]$',bits):
    cmd = re.findall(r'[[](\d+):(\d+)]$',bits)[0];
    b0 = int(cmd[1]);
    bL = int(cmd[0]) - b0 + 1;
  elif re.match(r'[[]\d+\+:\d+]$',bits):
    cmd = re.findall(r'[[](\d+)\+:(\d+)]$',bits)[0];
    b0 = int(cmd[0]);
    bL = int(cmd[1]);
  else:
    raise SSBCCException('Unrecognized bit slice format:  %s' % bits);
  if not 1 <= bL <= 8:
    raise SSBCCException('Malformed range "%s" doesn\'t provide 1 to 8 bits' % bits)
  v /= 2**b0;
  v %= 2**bL;
  return v;

def IntValue(v):
  """
  Convert a Verilog format integer into an integer value.
  """
  ov = 0;
  for vv in [v[i] for i in range(len(v)) if '0' <= v[i] <= '9']:
    ov *= 10;
    ov += ord(vv)-ord('0');
  return ov;

def IsPowerOf2(v):
  """
  Indicate whether or not the argument is a power of 2.
  """
  return v == 2**int(math.log(v,2)+0.5);

################################################################################
#
# Unit test.
#
################################################################################

if __name__ == "__main__":

  def Test_ExtractBits(v,bits,vExpect):
    vGot = ExtractBits(v,bits);
    if vGot != vExpect:
      raise Exception('ExtractBits failed: 0x%04X %s ==> 0x%02X instead of 0x%02X' % (v,bits,ExtractBits(v,bits),vExpect,));

  for v in (256,257,510,):
    Test_ExtractBits(v,'[0+:8]',v%256);
    Test_ExtractBits(v,'[7:0]',v%256);
    Test_ExtractBits(v,'[4+:6]',(v/16)%64);
    Test_ExtractBits(v,'[9:4]',(v/16)%64);

  print 'Unit test passed';
