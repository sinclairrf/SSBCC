################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Add a code trace peripheral to the 9x8 core.
#
# Note:  This is used to generate human readable printout and to monitor the
#        stack pointers to ensure they're valid.
# Note:  The PC and opcode are delayed so that they are aligned with the
#        resulting modifications to the data and result stacks.
#
################################################################################

import math

class trace:

  def __init__(self,config,params):
    pass;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    n_PC_nibbles = math.ceil(math.log(config['nInstructions'],2)/4);
    n_Np_nibbles = math.ceil(math.log(config['data_stack'],2)/4);
    n_R_nibbles  = max(n_PC_nibbles,2);
    n_Rp_nibbles = math.ceil(math.log(config['return_stack'],2)/4);
    outformat = '%%0%dX %%03X %%s : %%0%dX %%02X %%02X : %%0%dX %%0%dX' % (n_PC_nibbles,n_Np_nibbles,n_R_nibbles,n_Rp_nibbles);
    fp.write('// Trace peripheral\n');
    fp.write('generate\n');
    fp.write('reg [C_PC_WIDTH-1:0] s_PC_s[1:0];\n');
    fp.write('reg            [8:0] s_opcode_s = 9\'h000;\n');
    fp.write('reg        [7*8-1:0] s_opcode_name;\n');
    fp.write('initial begin\n');
    fp.write('  s_PC_s[0] = {(C_PC_WIDTH){1\'b0}};\n');
    fp.write('  s_PC_s[1] = {(C_PC_WIDTH){1\'b0}};\n');
    fp.write('end\n');
    fp.write('always @ (posedge i_clk) begin\n');
    fp.write('  s_PC_s[0] <= s_PC;\n');
    fp.write('  s_PC_s[1] <= s_PC_s[0];\n');
    fp.write('  s_opcode_s <= s_opcode;\n');
    fp.write('  casez (s_opcode_s)\n');
    fp.write('    9\'b00_0000_000 : s_opcode_name = "nop    ";\n');
    fp.write('    9\'b00_0000_001 : s_opcode_name = "<<0    ";\n');
    fp.write('    9\'b00_0000_010 : s_opcode_name = "<<1    ";\n');
    fp.write('    9\'b00_0000_011 : s_opcode_name = "<<msb  ";\n');
    fp.write('    9\'b00_0000_100 : s_opcode_name = "0>>    ";\n');
    fp.write('    9\'b00_0000_101 : s_opcode_name = "1>>    ";\n');
    fp.write('    9\'b00_0000_110 : s_opcode_name = "msb>>  ";\n');
    fp.write('    9\'b00_0000_111 : s_opcode_name = "lsb>>  ";\n');
    fp.write('    9\'b00_0001_000 : s_opcode_name = "dup    ";\n');
    fp.write('    9\'b00_0001_001 : s_opcode_name = "r@     ";\n');
    fp.write('    9\'b00_0001_010 : s_opcode_name = "over   ";\n');
    fp.write('    9\'b00_0010_010 : s_opcode_name = "swap   ";\n');
    fp.write('    9\'b00_0011_000 : s_opcode_name = "+      ";\n');
    fp.write('    9\'b00_0011_100 : s_opcode_name = "-      ";\n');
    fp.write('    9\'b00_0100_000 : s_opcode_name = "0=     ";\n');
    fp.write('    9\'b00_0100_001 : s_opcode_name = "0<>    ";\n');
    fp.write('    9\'b00_0100_010 : s_opcode_name = "-1=    ";\n');
    fp.write('    9\'b00_0100_011 : s_opcode_name = "-1<>   ";\n');
    fp.write('    9\'b00_0101_000 : s_opcode_name = "return ";\n');
    fp.write('    9\'b00_0110_000 : s_opcode_name = "inport ";\n');
    fp.write('    9\'b00_0111_000 : s_opcode_name = "outport";\n');
    fp.write('    9\'b00_1000_000 : s_opcode_name = ">r     ";\n');
    fp.write('    9\'b00_1001_001 : s_opcode_name = "r>     ";\n');
    fp.write('    9\'b00_1010_000 : s_opcode_name = "&      ";\n');
    fp.write('    9\'b00_1010_001 : s_opcode_name = "or     ";\n');
    fp.write('    9\'b00_1010_010 : s_opcode_name = "^      ";\n');
    fp.write('    9\'b00_1010_011 : s_opcode_name = "nip    ";\n');
    fp.write('    9\'b00_1010_100 : s_opcode_name = "drop   ";\n');
    fp.write('    9\'b00_1011_000 : s_opcode_name = "1+     ";\n');
    fp.write('    9\'b00_1011_100 : s_opcode_name = "1-     ";\n');
    fp.write('    9\'b00_1100_000 : s_opcode_name = "store  ";\n');
    fp.write('    9\'b00_1101_000 : s_opcode_name = "fetch  ";\n');
    fp.write('    9\'b00_1110_000 : s_opcode_name = "store+ ";\n');
    fp.write('    9\'b00_1110_100 : s_opcode_name = "store- ";\n');
    fp.write('    9\'b00_1111_000 : s_opcode_name = "fetch+ ";\n');
    fp.write('    9\'b00_1111_100 : s_opcode_name = "fetch- ";\n');
    fp.write('    9\'b0_100_????? : s_opcode_name = "jump   ";\n');
    fp.write('    9\'b0_110_????? : s_opcode_name = "call   ";\n');
    fp.write('    9\'b0_101_????? : s_opcode_name = "jumpc  ";\n');
    fp.write('    9\'b0_111_????? : s_opcode_name = "callc  ";\n');
    fp.write('    9\'b1_????_???? : s_opcode_name = "push   ";\n');
    fp.write( '           default : s_opcode_name = "INVALID";\n');
    fp.write('  endcase\n');
    fp.write('  $display("%s",s_PC_s[1],s_opcode_s,s_opcode_name,s_Np_stack_ptr,s_N,s_T,s_R,s_Rw_ptr);\n' % outformat);
    fp.write('end\n');
    fp.write('endgenerate\n');
