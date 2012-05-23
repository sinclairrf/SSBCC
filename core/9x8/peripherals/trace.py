################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Add a code trace peripheral to the 9x8 core.
#
# Note:  This is used to generate human readable printout and to monitor the
#        stack pointers to ensure they're valid.
#
################################################################################

import math

class trace:

  def __init__(self,config,params):
    print params;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    n_PC_nibbles = math.ceil(math.log(config['data_stack'],2)/4);
    n_R_nibbles  = max(n_PC_nibbles,2);
    n_Rp_nibbles = math.ceil(math.log(config['return_stack'],2)/4);
    outformat = '%%0%dX %%03X %%02X %%02X : %%0%dX %%0%dX' % (n_PC_nibbles,n_R_nibbles,n_Rp_nibbles);
    fp.write('always @ (posedge i_clk)\n');
    fp.write('  $display("%s",s_PC,s_opcode,s_N,s_T,s_R,s_Rw_ptr);\n' % outformat);
