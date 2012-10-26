################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Verilog generation functions.
#
################################################################################

import math
import re

from ssbccUtil import *;

################################################################################
#
# Generate input and output core names.
#
################################################################################

def genCoreName():
  return 'core.v';

def genOutName(rootName):
  if re.match('.*\.v$',rootName):
    return rootName;
  else:
    return ("%s.v" % rootName);

################################################################################
#
# Generate the code to run the INPORT selection, the associated output
# strobes,and the set-reset latches.
#
################################################################################

def genFunctions(fp,config):
  if ('clog2' in config.functions) and config.Get('define_clog2'):
    fp.write("""
// Use constant function instead of builtin $clog2.
function integer clog2;
  input integer value;
  integer temp;
  begin
    temp = value - 1;
    for (clog2=0; temp>0; clog2=clog2+1)
      temp = temp >> 1;
  end
endfunction
""");
  if 'display_trace' in config.functions:
    fp.write("""
// Display micro controller PC, opcode, and stacks.
localparam L__TRACE_SIZE        = C_PC_WIDTH            // pc width
                                + 9                     // opcode width
                                + C_DATA_PTR_WIDTH      // data stack pointer width
                                + 1                     // s_N_valid
                                + 8                     // s_N
                                + 1                     // s_T_valid
                                + 8                     // s_T
                                + 1                     // s_R_valid
                                + C_RETURN_WIDTH        // s_R
                                + C_RETURN_PTR_WIDTH    // return stack pointer width
                                ;
task display_trace;
  input                     [L__TRACE_SIZE-1:0] s_raw;
  reg                  [C_PC_WIDTH-1:0] s_PC;
  reg                             [8:0] s_opcode;
  reg            [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr;
  reg                                   s_N_valid;
  reg                             [7:0] s_N;
  reg                                   s_T_valid;
  reg                             [7:0] s_T;
  reg                                   s_R_valid;
  reg              [C_RETURN_WIDTH-1:0] s_R;
  reg          [C_RETURN_PTR_WIDTH-1:0] s_Rw_ptr;
  reg                         [7*8-1:0] s_opcode_name;
  begin
    { s_PC, s_opcode, s_Np_stack_ptr, s_N_valid, s_N, s_T_valid, s_T, s_R_valid, s_R, s_Rw_ptr } = s_raw;
    casez (s_opcode)
      9'b00_0000_000 : s_opcode_name = "nop    ";
      9'b00_0000_001 : s_opcode_name = "<<0    ";
      9'b00_0000_010 : s_opcode_name = "<<1    ";
      9'b00_0000_011 : s_opcode_name = "<<msb  ";
      9'b00_0000_100 : s_opcode_name = "0>>    ";
      9'b00_0000_101 : s_opcode_name = "1>>    ";
      9'b00_0000_110 : s_opcode_name = "msb>>  ";
      9'b00_0000_111 : s_opcode_name = "lsb>>  ";
      9'b00_0001_000 : s_opcode_name = "dup    ";
      9'b00_0001_001 : s_opcode_name = "r@     ";
      9'b00_0001_010 : s_opcode_name = "over   ";
      9'b00_0010_010 : s_opcode_name = "swap   ";
      9'b00_0011_000 : s_opcode_name = "+      ";
      9'b00_0011_100 : s_opcode_name = "-      ";
      9'b00_0100_000 : s_opcode_name = "0=     ";
      9'b00_0100_001 : s_opcode_name = "0<>    ";
      9'b00_0100_010 : s_opcode_name = "-1=    ";
      9'b00_0100_011 : s_opcode_name = "-1<>   ";
      9'b00_0101_000 : s_opcode_name = "return ";
      9'b00_0110_000 : s_opcode_name = "inport ";
      9'b00_0111_000 : s_opcode_name = "outport";
      9'b00_1000_000 : s_opcode_name = ">r     ";
      9'b00_1001_001 : s_opcode_name = "r>     ";
      9'b00_1010_000 : s_opcode_name = "&      ";
      9'b00_1010_001 : s_opcode_name = "or     ";
      9'b00_1010_010 : s_opcode_name = "^      ";
      9'b00_1010_011 : s_opcode_name = "nip    ";
      9'b00_1010_100 : s_opcode_name = "drop   ";
      9'b00_1011_000 : s_opcode_name = "1+     ";
      9'b00_1011_100 : s_opcode_name = "1-     ";
      9'b00_1100_000 : s_opcode_name = "store  ";
      9'b00_1101_000 : s_opcode_name = "fetch  ";
      9'b00_1110_000 : s_opcode_name = "store+ ";
      9'b00_1110_100 : s_opcode_name = "store- ";
      9'b00_1111_000 : s_opcode_name = "fetch+ ";
      9'b00_1111_100 : s_opcode_name = "fetch- ";
      9'b0_100_????? : s_opcode_name = "jump   ";
      9'b0_110_????? : s_opcode_name = "call   ";
      9'b0_101_????? : s_opcode_name = "jumpc  ";
      9'b0_111_????? : s_opcode_name = "callc  ";
      9'b1_????_???? : s_opcode_name = "push   ";
             default : s_opcode_name = "INVALID";
    endcase
    $write("%X %X %s : %X", s_PC, s_opcode, s_opcode_name, s_Np_stack_ptr);
    if (s_N_valid) $write(" %x",s_N); else $write(" XX");
    if (s_T_valid) $write(" %x",s_T); else $write(" XX");
    if (s_R_valid) $write(" : %x",s_R); else $write(" : %s",{((C_RETURN_WIDTH+3)/4){8'h58}});
    $write(" %X\\n",s_Rw_ptr);
  end
endtask
""");

def genInports(fp,config):
  if not config.inports:
    fp.write('// no input ports\n');
    return
  haveBitInportSignals = False;
  for ix in range(config.NInports()):
    thisPort = config.inports[ix][1:];
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalType = signal[2];
      if signalType in ('data','set-reset',):
        haveBitInportSignals = True;
  if haveBitInportSignals:
    fp.write('always @ (*)\n');
    fp.write('  case (s_T)\n');
  for ix in range(config.NInports()):
    thisPort = config.inports[ix][1:];
    nBits = 0;
    bitString = '';
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalSize = signal[1];
      signalType = signal[2];
      if signalType == 'data':
        nBits = nBits + signalSize;
        if len(bitString)>0:
          bitString += ', ';
        bitString = bitString + signalName;
      if signalType == 'set-reset':
        fp.write('      8\'h%02X : s_T_inport = (%s || s_SETRESET_%s) ? 8\'hFF : 8\'h00;\n' % (ix, signalName, signalName));
    if nBits == 0:
      pass;
    elif nBits < 8:
      fp.write('      8\'h%02X : s_T_inport = { %d\'h0, %s };\n' % (ix,8-nBits,bitString));
    elif nBits == 8:
      fp.write('      8\'h%02X : s_T_inport = %s;\n' % (ix,bitString));
    else:
      raise Exception('Program Bug -- this condition should have been caught elsewhere');
  if haveBitInportSignals:
    fp.write('    default : s_T_inport = 8\'h00;\n');
    fp.write('  endcase\n');
    fp.write('\n');
  # Generate all the INPORT strobes.
  for ix in range(config.NInports()):
    thisPort = config.inports[ix][1:];
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalType = signal[2];
      if signalType == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % signalName);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('  else if (s_inport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (signalName,ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('\n');
  # Generate all the INPORT "set-reset"s.
  for ix in range(config.NInports()):
    thisPort = config.inports[ix][1:];
    if thisPort[0][2] == 'set-reset':
      signalName = thisPort[0][0];
      fp.write('initial s_SETRESET_%s = 1\'b0;\n' % signalName);
      fp.write('always @(posedge i_clk)\n');
      fp.write('  if (i_rst)\n');
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % signalName);
      fp.write('  else if (s_inport && (s_T == 8\'h%02X))\n' % ix);
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % signalName);
      fp.write('  else if (%s)\n' % signalName);
      fp.write('    s_SETRESET_%s <= 1\'b1;\n' % signalName);
      fp.write('  else\n');
      fp.write('    s_SETRESET_%s <= s_SETRESET_%s;\n' % (signalName,signalName));

def genLocalParam(fp,config):
  fp.write('localparam C_PC_WIDTH                              = %4d;\n' % CeilLog2(config.Get('nInstructions')['length']));
  fp.write('localparam C_RETURN_PTR_WIDTH                      = %4d;\n' % CeilLog2(config.Get('return_stack')));
  fp.write('localparam C_DATA_PTR_WIDTH                        = %4d;\n' % CeilLog2(config.Get('data_stack')));
  fp.write('localparam C_RETURN_WIDTH                          = (C_PC_WIDTH <= 8) ? 8 : C_PC_WIDTH;\n');

def genMemories(fp,config,programBody):
  mems = config.config['combine']['mems'];
  args = config.config['combine']['args'];
  packed = config.config['combine']['packed'];
  # Declare instruction ROM(s).
  instructionMemory = config.Get('nInstructions');
  instructionAddrWidth = (instructionMemory['nbits_blockSize']+3)/4;
  instructionNameIndexWidth = (instructionMemory['nbits_nBlocks']+3)/4;
  for ixBlock in range(instructionMemory['nBlocks']):
    if instructionMemory['nBlocks'] == 1:
      memName = 's_opcodeMemory';
    else:
      instructionMemNameFormat = 's_opcodeMemory_%%0%dX' % instructionNameIndexWidth;
      memName = instructionMemNameFormat % ixBlock;
    fp.write('reg [8:0] %s[%d:0];\n' % (memName,instructionMemory['blockSize']-1,));
  # Declare data stack RAM if it isn't combined into another memory.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'DATA_STACK':
      memName = 's_data_stack';
      data_stack_length = packed[ixCombine]['length'];
      fp.write('reg [7:0] %s[%d:0];\n' % (memName,packed[ixCombine]['length']-1,));
      packed[ixCombine]['memName'] = memName;
      break;
  # Declare return stack RAM.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'RETURN_STACK':
      memName = 's_R_stack';
      return_stack_args = args[ixCombine][0];
      fp.write('reg [%d:0] %s[%d:0];\n' % (return_stack_args['rsArch']-1,memName,packed[ixCombine]['length']-1,));
      packed[ixCombine]['memName'] = memName;
      break;
  # Count the number of memories and then declare them.
  nMemories = 0;
  for thisMem in mems:
    if thisMem[0] == 'MEMORY':
      nMemories = nMemories + 1;
  if nMemories > 0:
    memNameFormat = 's_mem%%0%dx' % ((CeilLog2(nMemories)+3)/4);
    for ixCombine in range(len(mems)):
      if mems[ixCombine][0] == 'MEMORY':
        if nMemories == 1:
          thisMemName = 's_mem';
        else:
          thisMemName = memNameFormat % packed[ixCombine]['ixMemory'];
        packed[ixCombine]['memName'] = thisMemName;
        fp.write('reg [7:0] %s[%d:0];\n' % (thisMemName,packed[ixCombine]['length']-1,));
  fp.write('\n');
  # Initialize the instruction memory.
  fp.write('initial begin\n');
  ixRecordedBody = 0;
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'INSTRUCTION':
      thisPacked = packed[ixCombine];
      break;
  ixInstruction = 0;
  instructionBodyLength = thisPacked['packing'][0]['length'];
  for ixBlock in range(instructionMemory['nBlocks']):
    if instructionMemory['nBlocks'] == 1:
      memName = 's_opcodeMemory';
    else:
      memName = ('s_opcodeMemory_%%0%dX' % instructionNameIndexWidth) % ixBlock;
    thisPacked['memName'] = memName;
    formatp = '  %s[\'h%%0%dX] = { 1\'b1, %%s };\n' % (memName,instructionAddrWidth,);
    formatn = '  %s[\'h%%0%dX] = 9\'h%%s; // %%s\n' % (memName,instructionAddrWidth,);
    formate = '  %s[\'h%%0%dX] = 9\'h000;\n' % (memName,instructionAddrWidth,);
    for ixMem in range(instructionMemory['blockSize']):
      if ixRecordedBody < len(programBody):
        for ixRecordedBody in range(ixRecordedBody,len(programBody)):
          if programBody[ixRecordedBody][0] == '-':
            fp.write('  // %s\n' % programBody[ixRecordedBody][2:]);
          else:
            if programBody[ixRecordedBody][0] == 'p':
              fp.write(formatp % (ixMem,programBody[ixRecordedBody][2:]));
            else:
              fp.write(formatn % (ixMem,programBody[ixRecordedBody][0:3],programBody[ixRecordedBody][4:]));
            break;
        ixRecordedBody = ixRecordedBody + 1;
      elif ixInstruction < instructionBodyLength:
        fp.write(formate % ixMem);
      else:
        break;
      ixInstruction = ixInstruction + 1;
  if len(thisPacked['packing']) > 1:
    fp.write('  //\n  // %s\n  //\n' % mems[ixCombine][1]);
    offset0 = instructionMemory['blockSize']*(instructionMemory['nBlocks']-1);
    for ixPacking in range(1,len(thisPacked['packing'])):
      thisPacking = thisPacked['packing'][ixPacking];
      thisPacking['offset'] = thisPacking['offset'] - offset0;
    genMemories_init(fp,config,thisPacked['packing'][1:],memName,width=9);
  fp.write('end\n\n');
  # Initialize the data stack.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'DATA_STACK':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName);
      fp.write('end\n\n');
      break;
  # Initialize the return stack.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'RETURN_STACK':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      rsArch = args[ixCombine][0]['rsArch'];
      if rsArch < 8:
        width = 8;
      else:
        width = rsArch;
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName,width=width);
      fp.write('end\n\n');
      break;
  # Initialize the memories
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'MEMORY':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName);
      fp.write('end\n\n');
  # Generate the opcode read logic.
  fp.write('//\n');
  fp.write('// opcode read logic\n');
  fp.write('//\n');
  fp.write('\n');
  fp.write('initial s_opcode = 9\'h000;\n');
  fp.write('always @ (posedge i_clk)\n');
  fp.write('  if (i_rst)\n');
  fp.write('    s_opcode <= 9\'h000;\n');
  if instructionMemory['nBlocks'] == 1:
    fp.write('  else\n');
    fp.write('    s_opcode <= s_opcodeMemory[s_PC];\n');
  else:
    fp.write('  else case (s_PC[%d+:%d])\n' % (instructionMemory['nbits_blockSize'],instructionMemory['nbits_nBlocks'],));
    for ixBlock in range(instructionMemory['nBlocks']):
      memName = instructionMemNameFormat % ixBlock;
      thisLine = '%d\'h%X : s_opcode <= %s[s_PC[0+:%d]];\n' % (instructionMemory['nbits_nBlocks'],ixBlock,memName,instructionMemory['nbits_blockSize'],);
      while thisLine.index(':') < 12:
        thisLine = ' ' + thisLine;
      fp.write(thisLine);
    fp.write('    default : s_opcode <= 9\'h000;\n');
    fp.write('  endcase\n');
  fp.write('\n');
  # Generate the data_stack read and write logic.
  fp.write('//\n');
  fp.write('// data stack read and write logic\n');
  fp.write('//\n');
  fp.write('\n');
  for ixCombine in range(len(mems)):
    if 'DATA_STACK' in mems[ixCombine]:
      isLUT = (len(mems[ixCombine]) == 1);
      if mems[ixCombine][0] == 'INSTRUCTION':
        bitwidth = 9;
      elif mems[ixCombine][0] == 'RETURN_STACK':
        bitwidth = args[ixCombine][0]['rsArch'];
      else:
        bitwidth = 8;
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      if isLUT:
        s_Np_stack = 's_Np_stack';
      else:
        s_Np_stack = 's_Np_stack_reg';
      if bitwidth == 8:
        s_N = 's_N';
      else:
        s_N = '{ %d\'h0, s_N }' % (bitwidth-8,);
        s_Np_stack = '{ not_used_s_Np_stack, %s }' % (s_Np_stack,);
      ptrString = 's_Np_stack_ptr';
      ptrStringTop = 's_Np_stack_ptr_next';
      if len(thisPacked['packing']) != 1:
        for ixPacked in range(len(thisPacked['packing'])):
          thisPacking = thisPacked['packing'][ixPacked];
          if thisPacking['name'] != '_data_stack':
            continue;
          nbitsThis = CeilLog2(thisPacking['length']);
          nbitsTop = CeilLog2(thisPacked['length']) - nbitsThis;
          ptrStringFormat = ('{ %d\'h%%0%dX, %%%%s }' % (nbitsTop,(nbitsTop+3)/4,)) % (thisPacking['offset']/2**nbitsThis,);
          ptrString = ptrStringFormat % (ptrString,);
          ptrStringTop = ptrStringFormat % (ptrStringTop,);
      if not isLUT:
        fp.write('reg [7:0] s_Np_stack_reg = 8\'d0;\n');
      if bitwidth == 9:
        fp.write('reg not_used_s_Np_stack = 1\'b0;\n');
      elif bitwidth > 9:
        fp.write('reg [%d:0] not_used_s_Np_stack = %d\'d0;\n' % (bitwidth-9,bitwidth-8,));
      fp.write('always @ (posedge i_clk) begin\n');
      fp.write('  if (s_stack == C_STACK_INC)\n');
      if isLUT:
        fp.write('    %s[%s] <= %s;\n' % (memName,ptrStringTop,s_N,));
      else:
        fp.write('    %s[%s] = %s; // coerce write-first\n' % (memName,ptrStringTop,s_N,));
        fp.write('  %s <= %s[%s];\n' % (s_Np_stack,memName,ptrStringTop,));
      fp.write('end\n');
      if isLUT:
        fp.write('assign s_Np_stack = %s[%s];\n' % (memName,ptrString,));
      else:
        fp.write('assign s_Np_stack = s_Np_stack_reg;\n');
      fp.write('\n');
      break;
  else:
    raise Exception('Program bug');
  # Generate the return_stack read and write logic.
  fp.write('//\n');
  fp.write('// return stack read and write logic\n');
  fp.write('//\n');
  fp.write('\n');
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'RETURN_STACK':
      isLUT = (len(mems[ixCombine]) == 1);
      bitwidth = args[ixCombine][0]['rsArch'];
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      minBitWidth = CeilLog2(config.Get('nInstructions')['length']);
      thisBitWidth = args[ixCombine][0]['rsArch'];
      if thisBitWidth < minBitWidth:
        raise Exception('Program bug');
      s_R_write = 's_R_pre';
      if isLUT:
        s_R_read = 's_R';
      else:
        s_R_read = 's_R_reg';
      if thisBitWidth > minBitWidth:
        s_R_write = '{ %d\'h0, %s }' % (thisBitWidth-minBitWidth,s_R_write,);
        s_R_read = '{ not_used_s_R, %s }' % (s_R_read,);
      ptrString = 's_R_stack_ptr';
      ptrStringNext = 's_R_stack_ptr_next';
      if len(thisPacked['packing']) != 1:
        for ixPacked in range(len(thisPacked['packing'])):
          thisPacking = thisPacked['packing'][ixPacked];
          if thisPacking['name'] != '_return_stack':
            continue;
          nbitsThis = CeilLog2(thisPacking['length']);
          nbitsTop = CeilLog2(thisPacking['length']) - nbitsThis;
          ptrStringFormat = ('{ %d\'h%%0%dX, %%%%s }' % (nbitsTop,(nbitsTop+3)/4,)) % (thisPacking['offset']/2**nbitsThis,);
          ptrString = ptrStringFormat % ptrString;
          ptrStringNext = ptrStringFormat % ptrStringNext;
      if not isLUT:
        fp.write('reg [%d:0] s_R_reg = %d\'d0;\n' % (thisBitWidth-1,thisBitWidth,));
      if not isLUT and thisBitWidth == minBitWidth+1:
        fp.write('reg not_used_s_R = 1\'b0;\n');
      if not isLUT and thisBitWidth > minBitWidth+1:
        fp.write('reg [%d:0] not_used_s_R = %d\'d0;\n' % (thisBitWidth-minBitWidth-1,thisBitWidth-minBitWidth,));
      fp.write('always @ (posedge i_clk) begin\n');
      fp.write('  if (s_return == C_RETURN_INC)\n');
      if isLUT:
        fp.write('    %s[%s] <= %s;\n' % (memName,ptrStringNext,s_R_write,));
      else:
        fp.write('    %s[%s] = %s; // coerce write-through\n' % (memName,ptrStringNext,s_R_write,));
        fp.write('  %s <= %s[%s];\n' % (s_R_read,memName,ptrStringNext,));
      fp.write('end\n');
      if isLUT and thisBitWidth == minBitWidth+1:
        fp.write('wire not_used_s_R;\n');
      if isLUT and thisBitWidth > minBitWidth+1:
        fp.write('wire [%d:0] not_used_s_R;\n' % (thisBitWidth-minBitWidth-1,thisBitWidth-minBitWidth,));
      if isLUT:
        fp.write('assign %s = %s[%s];\n' % (s_R_read,memName,ptrString,));
      else:
        fp.write('assign s_R = s_R_reg;\n');
      fp.write('\n');
      break;
  else:
    raise Exception('Program bug');
  # Coalesce the memory bank indices and the corresponding memory names, offsets, lengths, etc.
  lclMemName = [];
  lclMemParam = [];
  for ixBank in range(4):
    memParam = config.GetMemoryByBank(ixBank);
    if memParam:
      lclMemName.append(memParam['name']);
      lclMemParam.append(dict(bank=memParam['bank'],type=memParam['type']));
  maxMemWidth = 0;
  for ixCombine in range(len(packed)):
    if mems[ixCombine][0] == 'INSTRUCTION':
      thisMemWidth = 9;
    elif mems[ixCombine][0] == 'RETURN_STACK':
      thisMemWidth = args[ixCombine][0]['rsArch'];
    else:
      thisMemWidth = 8;
    thisPacking = packed[ixCombine]['packing'];
    for ix in range(len(thisPacking)):
      thisPacked = thisPacking[ix];
      thisName = thisPacked['name'];
      if thisName[0] == '_':
        continue;
      if thisName not in lclMemName:
        print 'WARNING:  Memory "%s" not used in program' % thisName;
        continue;
      if thisMemWidth > maxMemWidth:
        maxMemWidth = thisMemWidth;
      ixLclMem = lclMemName.index(thisName);
      thisLclMemParam = lclMemParam[ixLclMem];
      thisLclMemParam['name'] = thisPacked['name'];
      thisLclMemParam['memName'] = packed[ixCombine]['memName'];
      thisLclMemParam['memWidth'] = thisMemWidth;
      thisLclMemParam['nMemAddrBits'] = CeilLog2(packed[ixCombine]['length']);
      thisLclMemParam['offset'] = thisPacked['offset'];
      thisLclMemParam['nAddrBits'] = CeilLog2(thisPacked['length']);
      if thisLclMemParam['nAddrBits'] < 8:
        addrString = 's_T[%d:0]' % (thisLclMemParam['nAddrBits']-1,);
      else:
        addrString = 's_T';
      if thisLclMemParam['nAddrBits'] < thisLclMemParam['nMemAddrBits']:
        nbits = thisLclMemParam['nMemAddrBits'] - thisLclMemParam['nAddrBits'];
        offset = thisLclMemParam['offset']/2**thisLclMemParam['nAddrBits'];
        addrString = ('{ %d\'h%%0%dX, %s }' % (nbits,(nbits+3)/4,addrString,)) % offset;
      thisLclMemParam['addrString'] = addrString;
  # Generate the memory read logic.
  fp.write('//\n');
  fp.write('// memory read logic\n');
  fp.write('//\n');
  fp.write('\n');
  if config.NMemories() > 0:
    fp.write('initial   s_memory = 8\'h00;\n');
    if maxMemWidth == 9:
      fp.write('reg       not_used_s_memory = 1\'b0;\n');
    elif maxMemWidth > 9:
      fp.write('reg [%d:0] not_used_s_memory = %d\'d0;\n' % (maxMemWidth-9,maxMemWidth-8,));
    if maxMemWidth == 8:
      memTarget = 's_memory';
    else:
      memTarget = '{ not_used_s_memory, s_memory }';
    fp.write('always @ (*)\n');
    fp.write('  case (s_opcode[0+:2])\n');
    for ixMem in range(len(lclMemParam)):
      thisParam = lclMemParam[ixMem];
      thisBank = thisParam['bank'];
      memSource = '%s[%s]' % (thisParam['memName'],thisParam['addrString'],);
      if thisParam['memWidth'] < maxMemWidth:
        memSource = '{ %d\'d0, %s }' % (maxMemWidth-thisParam['memWidth'],memSource,);
      fp.write('       2\'d%d : %s = %s; // memory "%s"\n' % (thisBank,memTarget,memSource,thisParam['name'],));
    fp.write('    default : %s = %d\'d0;\n' % (memTarget,maxMemWidth,));
    fp.write('  endcase\n');
  fp.write('\n');
  # Generate the memory write logic.
  if config.NMemories() > 0:
    fp.write('//\n');
    fp.write('// memory write logic\n');
    fp.write('//\n');
    fp.write('\n');
    for ixCombine in range(len(mems)):
      if 'MEMORY' in mems[ixCombine]:
        memlist = args[ixCombine][mems[ixCombine].index('MEMORY')]['memlist'];
        memName = packed[ixCombine]['memName'];
        memAddrWidth = CeilLog2(packed[ixCombine]['length']);
        thisRams = [];
        for ramName in memlist:
          memParam = config.GetMemoryByName(ramName);
          if memParam['type'] == 'RAM':
            thisRams.append(memParam);
        if not thisRams:
          continue;
        if len(thisRams) == 1:
          ramName = thisRams[0]['name'];
          if ramName not in lclMemName:
            raise Exception('Program bug');
          thisMemParam = lclMemParam[lclMemName.index(ramName)];
          addrName = thisMemParam['addrString'];
          conditionalString = 's_opcode[0+:2] == 2\'d%d' % thisMemParam['bank'];
        else:
          addrName = '%s_addr' % memName;
          for ixRam in range(len(thisRams)):
            ramName = thisRams[ixRam]['name'];
            if ramName not in lclMemName:
              raise Exception('Program bug');
            thisMemParam = lclMemParam[lclMemName.index(ramName)];
            if ixRam == 0:
              fp.write('reg [%d:0] %s = %d\'d0;\n' % (thisMemParam['nMemAddrBits']-1,addrName,thisMemParam['nMemAddrBits'],));
              fp.write('always @ (*)\n');
              fp.write('  case (s_opcode[0+:2])\n');
            assignmentString = '%s = %s' % (addrName,thisMemParam['addrString'],);
            if ixRam < len(thisRams)-1:
              fp.write('       2\'%d : %s; // memory "%s"\n' % (thisMemParam['bank'],assignmentString,thisMemParam['name'],));
            else:
              fp.write('    default: %s; // memory "%s"\n' % (assignmentString,thisMemParam['name'],));
              fp.write('  endcase\n');
          conditionalString = '';
          for ixRam in range(len(thisRams)):
            ramName = thisRams[ixRam]['name'];
            thisMemParam = lclMemParam[lclMemName.index(ramName)];
            if len(conditionalString) > 0:
              conditionalString = conditionalString + ' || ';
            conditionalString = conditionalString + ('(s_opcode[0+:2] == 2\'d%d)' % thisMemParam['bank']);
        if thisMemParam['memWidth'] == 8:
          sourceString = 's_T';
        elif thisMemParam['memWidth'] == 9:
          sourceString = '{ 1\'b0, s_T }';
        else:
          sourceString = '{ %d\'d0, s_T }' % (thisMemParam['memWidth']-8,);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (s_mem_wr && (%s))\n' % conditionalString);
        fp.write('    %s[%s] <= %s;\n' % (memName,addrName,sourceString));
        fp.write('\n');

# TODO -- accommodate width=16, ...
def genMemories_init(fp,config,packing,memName,width=8):
  nbits = CeilLog2(packing[-1]['offset'] + packing[-1]['occupy']);
  if width == 8:
    formatd = '  %s[\'h%%0%dX] = 8\'h%%s;' % (memName,(nbits+3)/4,);
  else:
    formatd = '  %s[\'h%%0%dX] = { %d\'d0, 8\'h%%s };' % (memName,(nbits+3)/4,width-8,);
  formate = '  %s[\'h%%0%dX] = %d\'h%s;\n' % (memName,(nbits+3)/4,width,'0'*((width+3)/4),);
  for thisPacked in packing:
    name = thisPacked['name'];
    offset = thisPacked['offset'];
    length = thisPacked['length'];
    occupy = thisPacked['occupy'];
    # DATA_STACK and RETURN_STACK
    if name == '_data_stack' or name == '_return_stack':
      if len(packing) > 1:
        if name == '_data_stack':
          fp.write('  // DATA_STACK\n');
        else:
          fp.write('  // RETURN_STACK\n');
      for ix in range(offset,offset+length):
        fp.write(formate % ix);
    # MEMORIES
    else:
      fp.write('  // memory "%s"\n' % name);
      memParam = config.GetMemoryByName(name);
      if not memParam:
        raise Exception('Program bug');
      curOffset = offset;
      if memParam['body'] != None:
        for line in memParam['body']:
          if line[0] == '-':
            name = line[2:-1];
            continue;
          fp.write(formatd % (curOffset,line[0:2],));
          if name:
            fp.write(' // %s' % name);
            name = None;
          fp.write('\n');
          curOffset = curOffset + 1;
      for ix in range(curOffset,offset+length):
        fp.write(formate % ix);
    # initialize unused memory
    if length < occupy:
      fp.write('  // unusable values to align memory blocks\n');
      for ix in range(offset+length,offset+occupy):
        fp.write(formate % ix);

def genModule(fp,config):
  fp.write('module %s(\n' % config.Get('outCoreName'));
  fp.write('  // synchronous reset and processor clock\n');
  fp.write('  input  wire           i_rst,\n');
  fp.write('  input  wire           i_clk');
  if config.ios:
    wasComment = False;
    for ix in range(len(config.ios)):
      signal = config.ios[ix];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      if wasComment:
        fp.write('\n');
      else:
        fp.write(',\n');
      wasComment = False;
      if signalType == 'comment':
        fp.write('  // %s' % signalName);
        wasComment = True;
      elif signalType == 'input':
        if signalWidth == 1:
          fp.write('  input  wire           %s' % signalName);
        elif signalWidth < 10:
          fp.write('  input  wire     [%d:0] %s' % (signalWidth-1,signalName));
        else:
          fp.write('  input  wire    [%2d:0] %s' % (signalWidth-1,signalName));
      elif signalType == 'output':
        if signalWidth == 1:
          fp.write('  output reg            %s' % signalName);
        elif signalWidth < 10:
          fp.write('  output reg      [%d:0] %s' % (signalWidth-1,signalName));
        else:
          fp.write('  output reg     [%2d:0] %s' % (signalWidth-1,signalName));
      elif signalType == 'inout':
        if signalWidth == 1:
          fp.write('  inout  wire           %s' % signalName);
        elif signalWidth < 10:
          fp.write('  inout  wire     [%d:0] %s' % (signalWidth-1,signalName));
        else:
          fp.write('  inout  wire    [%2d:0] %s' % (signalWidth-1,signalName));
      else:
        raise Exception('Program Bug -- unrecognized ios "%s"' % signalType);
  fp.write('\n');
  fp.write(');\n');
  # Write parameter and localparam statements (with separating blank lines).
  if config.parameters:
    isfirst = True;
    for parameter in config.parameters:
      if parameter[0][0] == 'G':
        if isfirst:
          fp.write('\n');
          isfirst = False;
        fp.write('parameter %s = %s;\n' % (parameter[0],parameter[1]));
    isfirst = True;
    for parameter in config.parameters:
      if parameter[0][0] == 'L':
        if isfirst:
          fp.write('\n');
          isfirst = False;
        fp.write('localparam %s = %s;\n' % (parameter[0],parameter[1]));

def genOutports(fp,config):
  if not config.outports:
    fp.write('// no output ports\n');
    return;
  for ix in range(config.NOutports()):
    thisPort = config.outports[ix][1:];
    bitWidth = 0;
    bitName = '';
    bitInit = '';
    nComponents = 0;
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      if signalType == 'data':
        bitWidth = bitWidth + signalWidth;
        if len(bitName) > 0:
          bitName += ', ';
        bitName += signalName;
        if len(signal) > 3:
          signalInit = signal[3];
        else:
          signalInit = '%d\'d0' % signalWidth;
        if len(bitInit) > 0:
          bitInit += ', '
        bitInit += signalInit;
        nComponents = nComponents + 1;
        fp.write('initial %s = %s;\n' % (signalName,signalInit,));
    if bitWidth == 0:
      pass;
    else:
      if nComponents == 1:
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= %s;\n' % (bitName,bitInit,));
        fp.write('  else if (s_outport && (s_T == 8\'h%02X))\n' % ix);
        fp.write('    %s <= s_N[0+:%d];\n' % (bitName,bitWidth));
        fp.write('  else\n');
        fp.write('    %s <= %s;\n' % (bitName,bitName));
        fp.write('\n');
      else:
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    { %s } <= { %s };\n' % (bitName,bitInit,));
        fp.write('  else if (s_outport && (s_T == 8\'h%02X))\n' % ix);
        fp.write('    { %s } <= s_N[0+:%d];\n' % (bitName,bitWidth));
        fp.write('  else\n');
        fp.write('    { %s } <= { %s };\n' % (bitName,bitName));
        fp.write('\n');
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalType = signal[2];
      if signalType == 'data':
        pass;
      elif signalType == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % signalName);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('  else if (s_outport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (signalName,ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('\n');
      else:
        raise Exception('Program Bug -- signalType = "%s" shouldn\'t have been encountered' % signalType);

def genSignals(fp,config):
  if not config.signals:
    fp.write('// no additional signals\n');
    return;
  maxLength = 0;
  for ix in range(len(config.signals)):
    thisSignal = config.signals[ix];
    signalName = thisSignal[0];
    if len(signalName) > maxLength:
      maxLength = len(signalName);
  maxLength = maxLength + 12;
  for ix in range(len(config.signals)):
    thisSignal = config.signals[ix];
    signalName = thisSignal[0];
    signalWidth = thisSignal[1];
    if len(thisSignal) < 3:
      signalInit = '%d\'d0' % signalWidth;
    else:
      signalInit = thisSignal[2];
    outString = 'reg ';
    if signalWidth == 1:
      outString += '       ';
    elif signalWidth < 10:
      outString += (' [%d:0] ' % (signalWidth-1));
    else:
      outString += ('[%2d:0] ' % (signalWidth-1));
    outString += signalName;
    if type(signalInit) != type(None):
      outString += ' '*(maxLength-len(outString));
      outString += ' = ' + signalInit;
    outString += ';\n'
    fp.write(outString);

def genUserHeader(fp,user_header):
  for ix in range(len(user_header)):
    fp.write('// %s\n' % user_header[ix]);
