################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Verilog generation functions.
#
################################################################################

import math
import os
import re

from ssbccUtil import *;

################################################################################
#
# Generate input and output core names.
#
################################################################################

def genCoreName():
  """
  Return the name of the file to use for the processor core.
  """
  return 'core.v';

def genOutName(rootName):
  """
  Return the name for the output micro controller module.
  """
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
  """
  Output the optional bodies for the following functions and tasks:
    clog2               when $clog2 isn't available by commanding "--define_clog2"
                        on the ssbcc command line
    display_trace       when the trace or monitor_stack peripherals are included
  """
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
    displayTracePath = os.path.join(config.Get('corepath'),'display_trace.v');
    fpDisplayTrace = open(displayTracePath,'r');
    if not fpDisplayTrace:
      raise Exception('Program Bug -- "%s" not found' % displayTracePath);
    body = fpDisplayTrace.read();
    fpDisplayTrace.close();
    fp.write(body);

def genInports(fp,config):
  """
  Generate the logic for the input signals.
  """
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
  """
  Generate the localparams for implementation-specific constants.
  """
  fp.write('localparam C_PC_WIDTH                              = %4d;\n' % CeilLog2(config.Get('nInstructions')['length']));
  fp.write('localparam C_RETURN_PTR_WIDTH                      = %4d;\n' % CeilLog2(config.Get('return_stack')));
  fp.write('localparam C_DATA_PTR_WIDTH                        = %4d;\n' % CeilLog2(config.Get('data_stack')));
  fp.write('localparam C_RETURN_WIDTH                          = (C_PC_WIDTH <= 8) ? 8 : C_PC_WIDTH;\n');

def genMemories(fp,config,programBody):
  """
  Generate the memories for the instructions, data stack, return stack, and the
  memories and the operations to access these memories.  Initialize the
  instruction memory.
  """
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
    for ixCombine in range(len(mems)):
      if 'INSTRUCTION' in mems[ixCombine]:
        instruction_mem_width = packed[ixCombine]['width'];
        break;
    else:
      raise Exception('Program bug');
    fp.write('reg [%d:0] %s[%d:0];\n' % (instruction_mem_width-1,memName,instructionMemory['blockSize']-1,));
  # Declare data stack RAM if it isn't combined into another memory.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'DATA_STACK':
      memName = 's_data_stack';
      memWidth = packed[ixCombine]['width'];
      fp.write('reg [%d:0] %s[%d:0];\n' % (memWidth-1,memName,packed[ixCombine]['length']-1,));
      packed[ixCombine]['memName'] = memName;
      break;
  # Declare return stack RAM.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'RETURN_STACK':
      memName = 's_R_stack';
      memWidth = packed[ixCombine]['width'];
      return_stack_args = args[ixCombine][0];
      fp.write('reg [%d:0] %s[%d:0];\n' % (memWidth-1,memName,packed[ixCombine]['length']-1,));
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
        memWidth = packed[ixCombine]['width'];
        fp.write('reg [%d:0] %s[%d:0];\n' % (memWidth-1,thisMemName,packed[ixCombine]['length']-1,));
        packed[ixCombine]['memName'] = thisMemName;
  fp.write('\n');
  # Initialize the instruction memory.
  fp.write('initial begin\n');
  ixRecordedBody = 0;
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'INSTRUCTION':
      thisPacked = packed[ixCombine];
      break;
  width = thisPacked['width'];
  ixInstruction = 0;
  instructionBodyLength = thisPacked['packing'][0]['length'];
  for ixBlock in range(instructionMemory['nBlocks']):
    if instructionMemory['nBlocks'] == 1:
      memName = 's_opcodeMemory';
    else:
      memName = ('s_opcodeMemory_%%0%dX' % instructionNameIndexWidth) % ixBlock;
    thisPacked['memName'] = memName;
    if width == 9:
      formatp = '  %s[\'h%%0%dX] = { 1\'b1, %%s };' % (memName,instructionAddrWidth,);
      formatn = '  %s[\'h%%0%dX] = 9\'h%%s; // %%s\n' % (memName,instructionAddrWidth,);
      formate = '  %s[\'h%%0%dX] = 9\'h000;\n' % (memName,instructionAddrWidth,);
    else:
      formatp = '  %s[\'h%%0%dX] = { %d\'d0, 1\'b1, %%s };' % (memName,instructionAddrWidth,width-9,);
      formatn = '  %s[\'h%%0%dX] = { %d\'d0, 9\'h%%s }; // %%s\n' % (memName,instructionAddrWidth,width-9,);
      formate = '  %s[\'h%%0%dX] = { %d\'d0, 9\'h000 };\n' % (memName,instructionAddrWidth,width-9,);
    for ixMem in range(instructionMemory['blockSize']):
      if ixRecordedBody < len(programBody):
        for ixRecordedBody in range(ixRecordedBody,len(programBody)):
          if programBody[ixRecordedBody][0] == '-':
            fp.write('  // %s\n' % programBody[ixRecordedBody][2:]);
          else:
            if programBody[ixRecordedBody][0] == 'p':
              (parameterString,parameterComment) = re.findall(r'(\S+)(.*)$',programBody[ixRecordedBody][2:])[0];
              fp.write(formatp % (ixMem,parameterString,));
              if len(parameterComment) > 0:
                fp.write(' // %s' % parameterComment[1:]);
              fp.write('\n');
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
    genMemories_init(fp,config,thisPacked['packing'][1:],memName,width);
  fp.write('end\n\n');
  # Initialize the data stack.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'DATA_STACK':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      width = thisPacked['width'];
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName,width);
      fp.write('end\n\n');
      break;
  # Initialize the return stack.
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'RETURN_STACK':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      width = thisPacked['width'];
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName,width);
      fp.write('end\n\n');
      break;
  # Initialize the memories
  for ixCombine in range(len(mems)):
    if mems[ixCombine][0] == 'MEMORY':
      thisPacked = packed[ixCombine];
      memName = thisPacked['memName'];
      width = thisPacked['width'];
      fp.write('initial begin\n');
      genMemories_init(fp,config,thisPacked['packing'],memName,width);
      fp.write('end\n\n');
  # Generate the opcode read logic.
  fp.write('//\n');
  fp.write('// opcode read logic\n');
  fp.write('//\n');
  fp.write('\n');
  fp.write('initial s_opcode = 9\'h000;\n');
  if instruction_mem_width == 10:
    fp.write('reg not_used_s_opcode = 1\'b0;\n');
  elif instruction_mem_width > 10:
    fp.write('reg [%d:0] not_used_s_opcode = %d\'d0;\n' % (instruction_mem_width-10,instruction_mem_width-9,));
  fp.write('always @ (posedge i_clk)\n');
  fp.write('  if (i_rst) begin\n');
  fp.write('    s_opcode <= 9\'h000;\n');
  if instruction_mem_width > 9:
    fp.write('    not_used_s_opcode <= %d\'d0;\n' % (instruction_mem_width-9,));
  if instruction_mem_width == 9:
    instructionReadTarget = 's_opcode';
  else:
    instructionReadTarget = '{ not_used_s_opcode, s_opcode }';
  if instructionMemory['nBlocks'] == 1:
    fp.write('  end else\n');
    fp.write('    %s <= s_opcodeMemory[s_PC];\n' % instructionReadTarget);
  else:
    fp.write('  else case (s_PC[%d+:%d])\n' % (instructionMemory['nbits_blockSize'],instructionMemory['nbits_nBlocks'],));
    for ixBlock in range(instructionMemory['nBlocks']):
      memName = instructionMemNameFormat % ixBlock;
      thisLine = '%d\'h%X : %s <= %s[s_PC[0+:%d]];\n' % (instructionMemory['nbits_nBlocks'],ixBlock,instructionReadTarget,memName,instructionMemory['nbits_blockSize'],);
      while thisLine.index(':') < 12:
        thisLine = ' ' + thisLine;
      fp.write(thisLine);
    fp.write('    default : %s <= %d\'h000;\n' % (instructionReadTarget,instruction_mem_width,));
    fp.write('  endcase\n');
  fp.write('\n');
  #
  # Generate the data_stack read and write logic.
  #
  fp.write('//\n');
  fp.write('// data stack read and write logic\n');
  fp.write('//\n');
  fp.write('\n');
  for ixCombine in range(len(mems)):
    if 'DATA_STACK' in mems[ixCombine]:
      # Get the packing information.
      thisPacked = packed[ixCombine];
      for thisPacking in thisPacked['packing']:
        if thisPacking['name'] == '_data_stack':
          break;
      else:
        raise Exception('Program bug -- "_data_stack" not found');
      break;
  else:
    raise Exception('Program bug -- "DATA_STACK" not found');
  # Get the memory type, memory name, widths, ...
  isLUT = (len(thisPacked['packing']) == 1);
  thisWidth = thisPacking['width'];                             # width of the data stack
  totalWidth = thisPacking['ratio'] * thisPacked['width'];      # width of the [multi-]word memory access
  # Generate the core.
  if not isLUT:
    fp.write('reg [%d:0] s_Np_stack_reg = %d\'d0;\n' % (thisWidth-1,thisWidth,));
    if totalWidth == thisWidth+1:
      fp.write('reg not_used_s_Np_stack_reg = 1\'b0;\n');
    if totalWidth > thisWidth+1:
      fp.write('reg [%d:0] not_used_s_Np_stack_reg = %d\'d0;\n' % (totalWidth-thisWidth-1,totalWidth-thisWidth,));
  fp.write('always @ (posedge i_clk) begin\n');
  fp.write('  if (s_stack == C_STACK_INC) begin\n');
  genMemories_assign(fp,'write',thisPacked,thisPacking,'s_Np_stack_ptr_next','s_N');
  fp.write('  end\n');
  if not isLUT:
    genMemories_assign(fp,'read',thisPacked,thisPacking,'s_Np_stack_ptr_next','s_Np_stack_reg');
  fp.write('end\n');
  if isLUT and totalWidth == thisWidth+1:
    fp.write('wire not_used_s_Np_stack_reg;\n');
  if isLUT and totalWidth > thisWidth+1:
    fp.write('wire [%d:0] not_used_s_Np_stack_reg;\n' % (totalWidth-thisWidth-1,totalWidth-thisWidth,));
  if isLUT:
    genMemories_assign(fp,'read',thisPacked,thisPacking,'s_Np_stack_ptr','s_Np_stack');
  else:
    fp.write('assign s_Np_stack = s_Np_stack_reg;\n');
  fp.write('\n');
  #
  # Generate the return_stack read and write logic.
  #
  fp.write('//\n');
  fp.write('// return stack read and write logic\n');
  fp.write('//\n');
  fp.write('\n');
  for ixCombine in range(len(mems)):
    if 'RETURN_STACK' in mems[ixCombine]:
      # Get the packing information.
      thisPacked = packed[ixCombine];
      for ixPacked in range(len(thisPacked['packing'])):
        thisPacking = thisPacked['packing'][ixPacked];
        if thisPacking['name'] == '_return_stack':
          break;
      else:
        raise Exception('Program bug');
      break;
  else:
    raise Exception('Program bug');
  # Get the memory type, memory name, widths, ...
  isLUT = (len(thisPacked['packing']) == 1);
  thisWidth = thisPacking['width'];                             # width of the data stack
  totalWidth = thisPacking['ratio'] * thisPacked['width'];      # width of the [multi-]word memory access
  # Generate the core.
  if not isLUT:
    fp.write('reg [%d:0] s_R_reg = %d\'d0;\n' % (thisWidth-1,thisWidth,));
    if totalWidth == thisWidth+1:
      fp.write('reg not_used_s_R_reg = 1\'b0;\n');
    if totalWidth > thisWidth+1:
      fp.write('reg [%d:0] not_used_s_R_reg = %d\'d0;\n' % (totalWidth-thisWidth-1,totalWidth-thisWidth,));
  fp.write('always @ (posedge i_clk) begin\n');
  fp.write('  if (s_return == C_RETURN_INC) begin\n');
  genMemories_assign(fp,'write',thisPacked,thisPacking,'s_R_stack_ptr_next','s_R_pre');
  fp.write('  end\n');
  if not isLUT:
    genMemories_assign(fp,'read',thisPacked,thisPacking,'s_R_stack_ptr_next','s_R_reg');
  fp.write('end\n');
  if isLUT and totalWidth == thisWidth+1:
    fp.write('wire not_used_s_R;\n');
  if isLUT and totalWidth > thisWidth+1:
    fp.write('wire [%d:0] not_used_s_R;\n' % (totalWidth-thisWidth-1,totalWidth-thisWidth,));
  if isLUT:
    genMemories_assign(fp,'read',thisPacked,thisPacking,'s_R_stack_ptr','s_R');
  else:
    fp.write('assign s_R = s_R_reg;\n');
  fp.write('\n');
  #
  # Coalesce the memory bank indices and the corresponding memory names, offsets, lengths, etc.
  #
  lclMemName = [];
  lclMemParam = [];
  for ixBank in range(4):
    memParam = config.GetMemoryByBank(ixBank);
    if memParam:
      lclMemName.append(memParam['name']);
      lclMemParam.append(dict(bank=memParam['bank'],type=memParam['type']));
  maxMemWidth = 0;
  for ixCombine in range(len(packed)):
    thisPacked = packed[ixCombine];
    thisMemWidth = thisPacked['width'];
    for thisPacking in thisPacked['packing']:
      thisName = thisPacking['name'];
      if thisName[0] == '_':
        continue;
      if thisName not in lclMemName:
        print 'WARNING:  Memory "%s" not used in program' % thisName;
        continue;
      if thisMemWidth > maxMemWidth:
        maxMemWidth = thisMemWidth;
      ixLclMem = lclMemName.index(thisName);
      thisLclMemParam = lclMemParam[ixLclMem];
      thisLclMemParam['name'] = thisPacking['name'];
      thisLclMemParam['memName'] = thisPacked['memName'];
      thisLclMemParam['memWidth'] = thisPacking['width'];
      thisLclMemParam['nMemAddrBits'] = CeilLog2(thisPacked['length']);
      thisLclMemParam['offset'] = thisPacking['offset'];
      thisLclMemParam['nAddrBits'] = CeilLog2(thisPacking['length']);
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
    fp.write('always @ (s_opcode,s_T)\n');
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
          sourceString = 's_N';
        elif thisMemParam['memWidth'] == 9:
          sourceString = '{ 1\'b0, s_N }';
        else:
          sourceString = '{ %d\'d0, s_N }' % (thisMemParam['memWidth']-8,);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (s_mem_wr && (%s))\n' % conditionalString);
        fp.write('    %s[%s] <= %s;\n' % (memName,addrName,sourceString));
        fp.write('\n');

def genMemories_assign(fp,mode,thisPacked,thisPacking,addr,sigName):
  """
  Utility function for genMemories.\n
  Generate the logic to perform memory writes, including writes to multiple
  memory locations (for the return stack) and writing zeros to otherwise unused
  bits.
  """
  if mode not in ['write','read']:
    raise Exception('Program Bug: %s' % mode);
  memName = thisPacked['memName'];
  memWidth = thisPacked['width'];
  ratio = thisPacking['ratio']
  sigWidth = thisPacking['width'];
  nbitsRatio = CeilLog2(ratio);
  notUsedWidth = ratio*memWidth - sigWidth;
  isLUT = len(thisPacked['packing']) == 1;
  if not isLUT:
    memAddrWidth = CeilLog2(thisPacked['length']);
    thisAddrWidth = CeilLog2(thisPacking['length']);
    nbitsOffset = memAddrWidth - thisAddrWidth;
    addr = '%d\'h%%0%dx, %s' % (nbitsOffset,(nbitsOffset+3)/4,addr,) % (thisPacking['offset']/2**thisAddrWidth,);
  for ixRatio in range(ratio):
    ix0 = ixRatio*memWidth;
    ix1 = ix0+memWidth;
    if ratio == 1:
      thisAddr = addr;
    else:
      thisAddr = '%s, %d\'h%%0%dx' % (addr,nbitsRatio,(nbitsRatio+3)/4,) % ixRatio;
    if thisAddr.find(',') != -1:
      thisAddr = '{ %s }' % thisAddr;
    if ix1 <= sigWidth:
      thisSignal = '%s[%d:%d]' % (sigName,ix1-1,ix0,);
    elif ix0 <= sigWidth:
      nEmpty = ix1-sigWidth;
      if mode == 'write':
        thisSignal = '{ %d\'d0, %s[%d:%d] }' % (nEmpty,sigName,sigWidth-1,ix0,);
      elif notUsedWidth == 1:
        thisSignal = '{ not_used_%s, %s[%d:%d] }' % (sigName,sigName,sigWidth-1,ix0,);
      else:
        thisSignal = '{ not_used_%s[%d:0], %s[%d:%d] }' % (sigName,ix1-sigWidth-1,sigName,sigWidth-1,ix0,);
    else:
      if mode == 'write':
        thisSignal = '%d\'0' % memWidth;
      else:
        thisSignal = 'not_used_%s[%d:%d]' % (sigName,ix1-sigWidth-1,ix0-sigWidth,);
    if mode == 'write' and isLUT:
      fp.write('    %s[%s] <= %s;\n' % (memName,thisAddr,thisSignal,));
    elif mode == 'write' and not isLUT:
      fp.write('    %s[%s] = %s; // coerce write-through\n' % (memName,thisAddr,thisSignal,));
    elif mode == 'read' and not isLUT:
      fp.write('  %s <= %s[%s];\n' % (thisSignal,memName,thisAddr,));
    elif mode == 'read' and isLUT:
      fp.write('always @ (%s)\n' % thisAddr);
      fp.write('%s <= %s[%s];\n' % (thisSignal,memName,thisAddr,));

def genMemories_init(fp,config,packing,memName,width=8):
  """
  Utility function for genMemories.\n
  Generate the logic to initialize memories based on the memory width and the
  initializatin output from the assembler.
  """
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
  """
  Generate the body of the module declaration and the parameter and localparam
  declarations.
  """
  # Insert the always-there stuff at the start of the module.
  config.ios.insert(0,('synchronous reset and processor clock',None,'comment',));
  config.ios.insert(1,('i_rst',1,'input',));
  config.ios.insert(2,('i_clk',1,'input',));
  # Starting from the end, determine the termination character for each line of
  # the module declaration
  signalFound = False;
  for ix in range(len(config.ios),0,-1):
    thisIOs = config.ios[ix-1];
    signalType = thisIOs[2];
    if signalType == 'comment' or not signalFound:
      thisIOs = thisIOs + ('\n',);
    else:
      thisIOs = thisIOs + (',\n',);
    if signalType != 'comment':
      signalFound = True;
    config.ios[ix-1] = thisIOs;
  # Write the module declaration.
  fp.write('module %s(\n' % config.Get('outCoreName'));
  if config.ios:
    for ix in range(len(config.ios)):
      signal = config.ios[ix];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      signalLineEnd = signal[3];
      if signalType == 'comment':
        fp.write('  // %s' % signalName);
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
      fp.write(signalLineEnd);
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
  """
  Generate the logic for the output signals.
  """
  if not config.outports:
    fp.write('// no output ports\n');
    return;
  for ix in range(config.NOutports()):
    thisPort = config.outports[ix][1:];
    bitWidth = 0;
    bitName = '';
    bitInit = '';
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      signalInit = '%d\'d0' % signalWidth if len(signal)==3 else signal[3];
      if signalType == 'data':
        if bitWidth > 0:
          bitName += ', ';
          bitInit += ', '
        bitWidth = bitWidth + signalWidth;
        bitName += signalName;
        bitInit += signalInit;
        fp.write('initial %s = %s;\n' % (signalName,signalInit,));
    if bitWidth == 0:
      pass;
    else:
      if ',' in bitName:
        bitName = '{ ' + bitName + ' }';
        bitInit = '{ ' + bitInit + ' }';
      fp.write('always @ (posedge i_clk)\n');
      fp.write('  if (i_rst)\n');
      fp.write('    %s <= %s;\n' % (bitName,bitInit,));
      fp.write('  else if (s_outport && (s_T == 8\'h%02X))\n' % ix);
      fp.write('    %s <= s_N[0+:%d];\n' % (bitName,bitWidth));
      fp.write('  else\n');
      fp.write('    %s <= %s;\n' % (bitName,bitName));
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
        raise Exception('Program Bug -- unrecognized signal type "%s"' % signalType);

def genSignals(fp,config):
  """
  Insert the definitions of additional signals for the module.\n
  These can be signals required communications between the core and peripherals.
  """
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
    signalInit = "%d'd0" % signalWidth if len(thisSignal) < 3 else thisSignal[2];
    outString = 'reg ';
    if signalWidth == 1:
      outString += '       ';
    elif signalWidth < 10:
      outString += (' [%d:0] ' % (signalWidth-1));
    else:
      outString += ('[%2d:0] ' % (signalWidth-1));
    outString += signalName;
    if signalInit != None:
      outString += ' '*(maxLength-len(outString));
      outString += ' = ' + signalInit;
    outString += ';\n'
    fp.write(outString);

def genUserHeader(fp,user_header):
  """
  Copy the user header to the output module.
  """
  for ix in range(len(user_header)):
    fp.write('// %s\n' % user_header[ix]);
