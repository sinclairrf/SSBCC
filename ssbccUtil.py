################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math

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

def IsPowerOf2(v):
  """
  Indicate whether or not the argument is a power of 2.
  """
  return v == 2**int(math.log(v,2)+0.5);
