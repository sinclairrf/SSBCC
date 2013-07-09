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
    display_opcode      human-readable version of the opcode suitable for
                        waveform viewers
    display_trace       when the trace or monitor_stack peripherals are included
  """
  if 'display_opcode' in config.functions:
    displayOpcodePath = os.path.join(config.Get('corepath'),'display_opcode.v');
    fpDisplayOpcode = open(displayOpcodePath,'r');
    if not fpDisplayOpcode:
      raise Exception('Program Bug -- "%s" not found' % displayOpcodePath);
    body = fpDisplayOpcode.read();
    fpDisplayOpcode.close();
    fp.write(body);
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
  (thisPacked,thisPacking) = config.GetPackedAndPacking('DATA_STACK');
  if thisPacked['packing'][0]['name'] == 'DATA_STACK':
    thisPacked['memName'] = 's_data_stack';
    fp.write('reg [%d:0] %s[%d:0];\n' % (thisPacked['width']-1,thisPacked['memName'],thisPacked['length']-1,));
  # Declare return stack RAM if it isn't combined into another memory.
  (thisPacked,thisPacking) = config.GetPackedAndPacking('RETURN_STACK');
  if thisPacked['packing'][0]['name'] == 'RETURN_STACK':
    thisPacked['memName'] = 's_R_stack';
    fp.write('reg [%d:0] %s[%d:0];\n' % (thisPacked['width']-1,thisPacked['memName'],thisPacked['length']-1,));
  # Count the number of memories and then declare them.
  packedMemories = [thisPacked for thisPacked in packed if 'ixMemory' in thisPacked];
  nMemories = len(packedMemories);
  for thisPacked in packedMemories:
    if nMemories == 1:
      thisMemName = 's_mem';
    else:
      memNameFormat = 's_mem%%0%dx' % ((CeilLog2(nMemories)+3)/4);
      thisMemName = memNameFormat % thisPacked['ixMemory'];
    fp.write('reg [%d:0] %s[%d:0];\n' % (thisPacked['width']-1,thisMemName,thisPacked['length']-1,));
    thisPacked['memName'] = thisMemName;
  # Vertical separation between declarations and first initialization.
  fp.write('\n');
  # Initialize the instruction memory.
  fp.write('initial begin\n');
  ixRecordedBody = 0;
  for thisPacked in packed:
    if 'INSTRUCTION' in [e['name'] for e in thisPacked['packing']]:
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
    offset0 = instructionMemory['blockSize']*(instructionMemory['nBlocks']-1);
    for thisPacking in thisPacked['packing'][1:]:
      thisPacking['offset'] = thisPacking['offset'] - offset0;
    genMemories_init(fp,config,thisPacked,memName);
  fp.write('end\n\n');
  # Initialize the data stack.
  for thisPacked in [p for p in packed if p['packing'][0]['name'] == 'DATA_STACK']:
    fp.write('initial begin\n');
    genMemories_init(fp,config,thisPacked);
    fp.write('end\n\n');
    break;
  # Initialize the return stack.
  for thisPacked in [p for p in packed if p['packing'][0]['name'] == 'RETURN_STACK']:
    fp.write('initial begin\n');
    genMemories_init(fp,config,thisPacked);
    fp.write('end\n\n');
    break;
  # Initialize the memories
  for thisPacked in [p for p in packed if 'ixMemory' in p]:
    fp.write('initial begin\n');
    genMemories_init(fp,config,thisPacked);
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
  fp.write('//\n// data stack read and write logic\n//\n\n');
  (thisPacked,thisPacking) = config.GetPackedAndPacking('DATA_STACK');
  genMemories_stack(fp,thisPacked,thisPacking,'s_N','s_Np','s_stack == C_STACK_INC');
  #
  # Generate the return_stack read and write logic.
  #
  fp.write('//\n// return stack read and write logic\n//\n\n');
  (thisPacked,thisPacking) = config.GetPackedAndPacking('RETURN_STACK');
  genMemories_stack(fp,thisPacked,thisPacking,'s_R_pre','s_R','s_return == C_RETURN_INC');
  #
  # Coalesce the memory bank indices and the corresponding memory names, offsets, lengths, etc.
  #
  lclMemName = [];
  lclMemParam = [];
  for ixBank in range(4):
    memParam = config.GetMemoryByBank(ixBank);
    if not memParam:
      continue;
    lclMemName.append(memParam['name']);
    lclMemParam.append(dict(bank=memParam['bank'],type=memParam['type']));
  for ixCombine in range(len(packed)):
    thisPacked = packed[ixCombine];
    thisMemWidth = thisPacked['width'];
    for thisPacking in thisPacked['packing']:
      thisName = thisPacking['name'];
      if thisName in ('INSTRUCTION','DATA_STACK','RETURN_STACK',):
        continue;
      if thisName not in lclMemName:
        print 'WARNING:  Memory "%s" not used in program' % thisName;
        continue;
      ixLclMem = lclMemName.index(thisName);
      thisLclMemParam = lclMemParam[ixLclMem];
      thisLclMemParam['name'] = thisPacking['name'];
      thisLclMemParam['memName'] = thisPacked['memName'];
      thisLclMemParam['nMemAddrBits'] = CeilLog2(thisPacked['length']);
      thisLclMemParam['memArch'] = thisPacked['memArch'];
      thisLclMemParam['lane'] = thisPacking['lane'];
  # Generate the memory read/write logic.
  if config.NMemories() == 0:
    fp.write('// no memories\n');
    fp.write('\n');
  else:
    # Generate the memory read logic.
    fp.write('//\n');
    fp.write('// memory read logic\n');
    fp.write('//\n');
    fp.write('\n');
    for thisPacked in packed:
      if not (('ixMemory' in thisPacked) and (thisPacked['memArch'] == 'sync')):
        continue;
      addrWidth = CeilLog2(thisPacked['length']);
      fp.write('reg [%d:0] %s_reg = %d\'h0;\n' % (thisPacked['width']-1,thisPacked['memName'],thisPacked['width'],));
      fp.write('always @ (s_T)\n');
      if thisPacked['packingMode'] == 'parallel':
        fp.write('    %s_reg = %s[s_T[%d:0]];\n' % (thisPacked['memName'],thisPacked['memName'],addrWidth-1,));
      else:
        fp.write('    %s_reg = %s[%d\'h%x,s_T[%d:0]];\n' % (thisPacked['memName'],thisPacked['memName'],CeilLog2(thisPacked['length'])-addrWidth,addrWidth-1,));
      fp.write('\n');
    fp.write('initial   s_memory = 8\'h00;\n');
    include_s_T = False;
    fp.write('always @ (s_opcode[0+:2]');
    for thisPacked in packed:
      if 'ixMemory' not in thisPacked:
        continue;
      if thisPacked['memArch'] == 'sync':
        fp.write(',%s_reg' % thisPacked['memName']);
      else:
        fp.write(',%s[s_T[%d:0]]' % (thisPacked['memName'],thisLclMemParam['nMemAddrBits']-1,));
        include_s_T = True;
    if include_s_T:
      fp.write(',s_T');
    fp.write(')\n');
    fp.write('  case (s_opcode[0+:2])\n');
    for thisLclMemParam in lclMemParam:
      fp.write('       2\'d%d : s_memory = ' % thisLclMemParam['bank']);
      if thisLclMemParam['memArch'] == 'LUT':
        fp.write('%s[s_T[%d:0]]; // memory %s\n' % (thisLclMemParam['memName'],thisLclMemParam['nMemAddrBits']-1,thisLclMemParam['name'],));
      else:
        fp.write('%s_reg[%d+:8]; // memory %s\n' % (thisLclMemParam['memName'],thisLclMemParam['lane'],thisLclMemParam['name'],));
    fp.write('    default : s_memory = 8\'d0;\n');
    fp.write('  endcase\n');
    fp.write('\n');
    # Generate the memory write logic.
    fp.write('//\n');
    fp.write('// memory write logic\n');
    fp.write('//\n');
    fp.write('\n');
    for thisPacked in packed:
      if not 'ixMemory' in thisPacked:
        continue;
      thisRams = [];
      for thisPacking in thisPacked['packing']:
        memParam = config.GetMemoryByName(thisPacking['name']);
        if not memParam:
          continue;
        if not memParam['type'] == 'RAM':
          continue;
        thisRams.append({ 'bank':memParam['bank'], 'lane':thisPacking['lane'], 'length':thisPacking['length'], 'name':thisPacking['name'] });
      if not thisRams:
        continue;
      nAddrBits = CeilLog2(thisPacked['length']);
      fp.write('always @ (posedge i_clk)');
      if len(thisRams) > 1:
        fp.write(' begin');
      fp.write('\n');
      if thisPacked['memArch'] == 'LUT':
        fp.write('  if (s_mem_wr && (s_opcode[0+:2] == 2\'d%d))\n' % thisRams[0]['bank']);
        fp.write('    %s[s_T[%d:0]] <= s_N; // memory %s\n' % (thisPacked['memName'],nAddrBits-1,thisRams[0]['name']));
      else:
        for ram in thisRams:
          fp.write('  if (s_mem_wr && (s_opcode[0+:2] == 2\'d%d))\n' % ram['bank']);
          fp.write('    %s[s_T[%d:0]][%d+:8] <= s_N; // memory %s\n' % (thisPacked['memName'],nAddrBits-1,ram['lane'],ram['name'],));
      if len(thisRams) > 1:
        fp.write('end\n');
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
  sigWidth = thisPacking['nbits'];
  nbitsRatio = CeilLog2(ratio);
  notUsedWidth = ratio*memWidth - sigWidth;
  isLUT = (thisPacked['memArch'] == 'LUT');
  if not isLUT and thisPacking['length'] != thisPacked['length']:
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
      fp.write('always @ (%s[%s],%s)\n' % (memName,thisAddr,thisAddr,));
      fp.write('  %s = %s[%s];\n' % (thisSignal,memName,thisAddr,));

def genMemories_stack(fp,packed,packing,inSignalName,outSignalName,muxTest):
  isLUT = (packed['memArch'] == 'LUT');
  nbits = packing['nbits'];                             # number of bits in the signal
  width = packing['width'];                             # width of the memory
  totalWidth = packing['ratio'] * packed['width'];      # width of the [multi-]word memory access
  isSync = (packed['memArch'] == 'sync');
  # Generate the core.
  fp.write('reg [%d:0] %s_reg = %d\'d0;\n' % (nbits-1,outSignalName,nbits,));
  if totalWidth == nbits+1:
    fp.write('reg not_used_%s_reg = 1\'b0;\n' % outSignalName);
  elif totalWidth > nbits+1:
    fp.write('reg [%d:0] not_used_%s_reg = %d\'d0;\n' % (totalWidth-nbits-1,outSignalName,totalWidth-nbits,));
  fp.write('always @ (posedge i_clk) begin\n');
  fp.write('  if (%s) begin\n' % muxTest);
  genMemories_assign(fp,'write',packed,packing,outSignalName+'_stack_ptr_next',inSignalName);
  fp.write('  end\n');
  if isSync:
    genMemories_assign(fp,'read',packed,packing,outSignalName+'_stack_ptr_next',outSignalName+'_reg');
  fp.write('end\n');
  if isLUT:
    if totalWidth == nbits+1:
      fp.write('wire not_used_%s_reg;\n' % outSignalName);
    elif totalWidth > nbits+1:
      fp.write('wire [%d:0] not_used_%s_reg;\n' % (totalWidth-nbits-1,outSignalName,));
    genMemories_assign(fp,'read',packed,packing,outSignalName+'_stack_ptr',outSignalName);
  else:
    fp.write('initial %s = %d\'d0;\n' % (outSignalName,nbits,));
    fp.write('always @ (%s_reg)\n' % outSignalName);
    fp.write('  %s = %s_reg;\n' % (outSignalName,outSignalName,));
  fp.write('\n');

def genMemories_init(fp,config,packed,memName=None):
  """
  Utility function for genMemories.\n
  Generate the logic to initialize memories based on the memory width and the
  initialization output from the assembler.
  """
  if memName == None:
    memName = packed['memName'];
  width = packed['width'];
  nbits = CeilLog2(packed['length']);
  if packed['packingMode'] == 'sequential':
    if width == 8:
      formatd = '  %s[\'h%%0%dX] = 8\'h%%s;' % (memName,(nbits+3)/4,);
    else:
      formatd = '  %s[\'h%%0%dX] = { %d\'d0, 8\'h%%s };' % (memName,(nbits+3)/4,width-8,);
    formate = '  %s[\'h%%0%dX] = %d\'h%s;\n' % (memName,(nbits+3)/4,width,'0'*((width+3)/4),);
    for thisPacked in packed['packing']:
      name = thisPacked['name'];
      if name == 'INSTRUCTION':
        continue;
      offset = thisPacked['offset'];
      length = thisPacked['length'];
      occupy = thisPacked['occupy'];
      # DATA_STACK and RETURN_STACK
      if name in ('DATA_STACK','RETURN_STACK',):
        if len(packed['packing']) > 1:
          fp.write('  // %s\n' % name);
        for ix in range(offset,offset+length):
          fp.write(formate % ix);
  else:
    length = packed['length'];
    nMemories = len(packed['packing']);
    # Compute the contents of each 8-bit column of the initialization and the associated comment.
    fill = list();
    comments = list();
    for thisPacked in packed['packing']:
      fill.append(list());
      thisFill = fill[-1];
      comments.append(list());
      thisComments = comments[-1];
      thisMemName = thisPacked['name'];
      memParam = config.GetMemoryByName(thisMemName);
      if not memParam:
        raise Exception('Program bug -- memory "%s" not found' % thisMemName);
      curOffset = 0;
      if memParam['body'] != None:
        for line in memParam['body']:
          if line[0] == '-':
            varName = line[2:-1];
            continue;
          thisFill.append(line[0:2]);
          thisComments.append(varName if varName != None else '...');
          varName = None;
          curOffset = curOffset + 1;
      if (curOffset > length):
        raise Exception('Program Bug -- memory body longer than allocated memory space');
      for ix in range(curOffset,length):
        thisFill.append('00');
        thisComments.append('');
    # Ensure the initialization lengths are consistent.
    lengths = [len(thisFill) for thisFill in fill];
    if any(thisLength!=max(lengths) for thisLength in lengths):
      raise Exception('Program Bug -- generated memory lengths not consistent');
    # Write the memory initialization.
    formatd = '  %s[\'h%%0%0dX] = {' % (memName,(nbits+3)/4,);
    formatd += ' 8\'h%s,' * (nMemories-1);
    formatd += ' 8\'h%s };';
    formatc = list();
    for thisComments in comments:
      formatc.append('%%-%ds' % max(len(c) for c in thisComments));
    fp.write('  // memory "%s"\n' % memName);
    for ix in range(length):
      fp.write(formatd % ((ix,)+tuple([thisFill[ix] for thisFill in fill])));
      cs = [thisComment[ix] for thisComment in comments];
      if any(len(c)>0 for c in cs):
        fp.write(' // ');
        for jx in range(nMemories):
          if any(len(c)>0 for c in cs[jx:]):
            if jx > 0:
              fp.write(', ');
            fp.write(formatc[jx] % cs[jx]);
      fp.write('\n');

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
