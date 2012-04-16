################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Utilities required by ssbcc
#
################################################################################

import math

def CeilLog2(v):
  tmp = int(math.log(v,2));
  while 2**tmp < v:
    tmp = tmp + 1;
  return tmp;

def IsPowerOf2(v):
  return v == 2**int(math.log(v,2)+0.5);
