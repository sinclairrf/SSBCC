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

def genInstructions(fp,programBody,config):
  instructionMemory = config.Get('nInstructions');
  addrWidth = (instructionMemory['nbits_blockSize']+3)/4;
  nameIndexWidth = (instructionMemory['nbits_nBlocks']+3)/4;
  ixRecordedBody = 0;
  for ixBlock in range(instructionMemory['nBlocks']):
    if instructionMemory['nBlocks'] == 1:
      memName = 's_opcodeMemory';
    else:
      memNameFormat = 's_opcodeMemory_%%0%dX' % nameIndexWidth;
      memName = memNameFormat % ixBlock;
    formatp = '  %s[\'h%%0%dX] = { 1\'b1, %%s };\n' % (memName,addrWidth,);
    formatn = '  %s[\'h%%0%dX] = 9\'h%%s; // %%s\n' % (memName,addrWidth,);
    formate = '  %s[\'h%%0%dX] = 9\'h000;\n' % (memName,addrWidth,);
    fp.write('reg [8:0] %s[%d:0];\n' % (memName,instructionMemory['blockSize']-1,));
    fp.write('initial begin\n');
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
      else:
        fp.write(formate % ixMem);
    fp.write('end\n');
  fp.write("""
initial s_opcode = 9'h000;
always @ (posedge i_clk)
  if (i_rst)
    s_opcode <= 9'h000;
""");
  if instructionMemory['nBlocks'] == 1:
    fp.write('  else\n');
    fp.write('    s_opcode <= s_opcodeMemory[s_PC];\n');
  else:
    fp.write('  else case (s_PC[%d+:%d])\n' % (instructionMemory['nbits_blockSize'],instructionMemory['nbits_nBlocks'],));
    for ixBlock in range(instructionMemory['nBlocks']):
      memName = memNameFormat % ixBlock;
      thisLine = '%d\'h%s : s_opcode <= %s[s_PC[0+:%d]];\n' % (instructionMemory['nbits_nBlocks'],memName[15:],memName,instructionMemory['nbits_blockSize'],);
      while thisLine.index(':') < 12:
        thisLine = ' ' + thisLine;
      fp.write(thisLine);
    fp.write('    default : s_opcode <= 9\'h000;\n');
    fp.write('  endcase\n');

def genLocalParam(fp,config):
  fp.write('localparam C_PC_WIDTH                              = %4d;\n' % CeilLog2(config.Get('nInstructions')['length']));
  fp.write('localparam C_RETURN_PTR_WIDTH                      = %4d;\n' % CeilLog2(config.Get('return_stack')));
  fp.write('localparam C_DATA_PTR_WIDTH                        = %4d;\n' % CeilLog2(config.Get('data_stack')));
  fp.write('localparam C_RETURN_WIDTH                          = (C_PC_WIDTH <= 8) ? 8 : C_PC_WIDTH;\n');

# TODO -- accommodate m*n architecture statements
def genMemory(fp,config):
  for ixBank in range(4):
    memParam = config.GetMemoryByBank(ixBank);
    if not memParam:
      continue;
    memName = 's_mem%d' % ixBank;
    nMemLengthBits = CeilLog2(memParam['maxLength']);
    fp.write('reg [7:0] %s[%d:0];\n' % (memName,memParam['maxLength']-1));
    fp.write('initial begin\n');
    ixAddr = 0;
    name = None;
    for line in memParam['body']:
      if line[0] == '-':
        name = line[2:-1];
        continue;
      fp.write('  %s[\'h%X] = 8\'h%s;' % (memName,ixAddr,line[0:2]));
      if name:
        fp.write(' // %s' % name);
        name = None;
      fp.write('\n');
      ixAddr = ixAddr + 1;
    while ixAddr < memParam['maxLength']:
      fp.write('  %s[\'h%X] = 8\'h00;\n' % (memName,ixAddr));
      ixAddr = ixAddr + 1;
    fp.write('end\n');
    if memParam['type'] == 'RAM':
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
  if config.NMemories() == 0:
    fp.write('wire [7:0] s_memory = 8\'h00;\n');
  elif config.NMemories() == 1:
    memParam = config.GetMemoryByBank(0);
    fp.write('wire [7:0] s_memory = s_mem%d_out;\n' % memParam['bank']);
  else:
    fp.write('reg [7:0] s_memory = 8\'h00;\n');
    fp.write('always @ (*)\n');
    fp.write('  case (s_opcode[0+:2])\n');
    for ixBank in range(4):
      if config.GetMemoryByBank(ixBank):
        fp.write('    2\'d%d : s_memory = s_mem%d_out;\n' % (ixBank,ixBank));
    fp.write('    default : s_memory = 8\'h00;\n');
    fp.write('  endcase\n');

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
