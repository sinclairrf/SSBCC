################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Verilog generation functions.
#
################################################################################

from ssbccUtil import *;

# TODO -- accommodate m*n architecture statements
def genMemory(fp,memories):
  for ixBank in range(4):
    if ixBank not in memories['bank']:
      continue;
    ixMem = memories['bank'].index(ixBank);
    memName = 's_mem%d' % ixBank;
    memLength = eval(memories['arch'][ixMem]);
    nMemLengthBits = CeilLog2(memLength);
    fp.write('reg [7:0] %s[%d:0];\n' % (memName,memLength-1));
    fp.write('initial begin\n');
    ixAddr = 0;
    name = None;
    for line in memories['body'][ixMem]:
      if line[0] == '-':
        name = line[2:-1];
        continue;
      fp.write('  %s[\'h%X] = 8\'h%s;' % (memName,ixAddr,line[0:2]));
      if name:
        fp.write(' // %s' % name);
        name = None;
      fp.write('\n');
      ixAddr = ixAddr + 1;
    while ixAddr < memLength:
      fp.write('  %s[\'h%X] = 8\'h00;\n' % (memName,ixAddr));
      ixAddr = ixAddr + 1;
    fp.write('end\n');
    if memories['type'][ixMem] == 'RAM':
      fp.write('always @ (posedge i_clk)\n');
      fp.write('  if (s_mem_wr && (s_opcode[0+:2] == 2\'d%d))\n' % ixBank);
      if nMemLengthBits < 8:
        fp.write('    %s[s_T[0+:%d]] <= s_N;\n' % (memName,nMemLengthBits));
      else:
        fp.write('    %s[s_T] <= s_N;\n' % memName);
    if nMemLengthBits < 8:
      fp.write('wire [7:0] s_mem%d_out = %s[s_T[0+:%d]];\n' %
      (ixBank,memName,nMemLengthBits));
    else:
      fp.write('wire [7:0] s_mem%d_out = %s[s_T];\n' % (ixBank,memName));
    fp.write('\n');
  if len(memories['list']) == 1:
    fp.write('wire [7:0] s_memory = s_mem%d_out;\n' % memories['bank'][0]);
  else:
    fp.write('reg [7:0] s_memory = 8\'h00;\n');
    fp.write('always @ (*)\n');
    fp.write('  case (s_opcode[0+:2])\n');
    for ixBank in range(4):
      if ixBank in memories['bank']:
        fp.write('    2\'d%d : s_memory <= s_mem%d_out;\n' % (ixBank,ixBank));
    fp.write('    default : s_memory <= 8\'h00;\n');
    fp.write('  endcase\n');
