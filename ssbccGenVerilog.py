################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Verilog generation functions.
#
################################################################################

import re

from ssbccUtil import *;

def genInports(fp,inport):
  if not inport['config']:
    fp.write('// no input ports\n');
    return
  for ix in range(len(inport['config'])):
    if inport['config'][ix][0] == 'set-reset':
      fp.write('reg s_SETRESET_%s;\n' % inport['name'][ix][0]);
  if inport['haveBitSignals']:
    fp.write('always @ (*)\n');
    fp.write('  case (s_T)\n');
    for ix in range(len(inport['config'])):
      configs = inport['config'][ix];
      names = inport['name'][ix];
      if configs[0] == 'set-reset':
        fp.write('      8\'h%02X : s_T_inport = (%s || s_SETRESET_%s) ? 8\'hFF : 8\'h00;\n' % (ix, names[0], names[0]));
      else:
        bitsString = '';
        nBits = 0;
        for jx in range(len(configs)):
          if re.match(r'\d+-bit',configs[jx]):
            a = re.findall(r'(\d+)',configs[jx]);
            portLength = int(a[0]);
            if len(bitsString) != 0:
              bitsString = bitsString + ', ';
            bitsString = bitsString + inport['name'][ix][jx];
            nBits = nBits + portLength;
        if nBits == 0:
          pass;
        elif nBits < 8:
          fp.write('      8\'h%02X : s_T_inport = { %d\'h0, %s };\n' % (ix,8-nBits,bitsString));
        elif nBits == 8:
          fp.write('      8\'h%02X : s_T_inport = %s;\n' % (ix,bitsString));
        else:
          raise SSBCCException('Too many bits in %s' % (inport['id'][ix]));
    fp.write('    default : s_T_inport = 8\'h00;\n');
    fp.write('  endcase\n');
    fp.write('\n');
  for ix in range(len(inport['config'])):
    configs = inport['config'][ix];
    names = inport['name'][ix];
    for jx in range(len(configs)):
      if re.match(r'\d+-bit',configs[jx]):
        pass;
      elif configs[jx] == 'set-reset':
        pass;
      elif configs[jx] == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % names[jx]);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % names[jx]);
        fp.write('  else if (s_inport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (names[jx],ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % names[jx]);
        fp.write('\n');
      else:
        raise SSBCCException('Unrecognized INPORT type: "%s"' % configs[jx]);
  for ix in range(len(inport['config'])):
    if inport['config'][ix][0] == 'set-reset':
      name = inport['name'][ix][0];
      fp.write('initial s_SETRESET_%s = 1\'b0;\n' % name);
      fp.write('always @(posedge i_clk)\n');
      fp.write('  if (i_rst)\n');
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % name);
      fp.write('  else if (s_inport && (s_T == 8\'h%02X))\n' % ix);
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % name);
      fp.write('  else if (%s)\n' % name);
      fp.write('    s_SETRESET_%s <= 1\'b1;\n' % name);
      fp.write('  else\n');
      fp.write('    s_SETRESET_%s <= s_SETRESET_%s;\n' % (name,name));

def genInstructions(fp,programBody,config):
  nInstructions = config['nInstructions'];
  fp.write('reg [8:0] s_opcodeMemory[%d:0];\n' % (nInstructions-1));
  fp.write('initial begin\n');
  programBodyIx = 0;
  for ix in range(len(programBody)):
    if programBody[ix][0] == '-':
      fp.write('  // %s\n' % programBody[ix][2:]);
    else:
      if programBody[ix][0] == 'p':
        fp.write('  s_opcodeMemory[\'h%X] = { 1\'b1, %s[0+:8] };\n' % (programBodyIx,programBody[ix][2:]));
      else:
        fp.write('  s_opcodeMemory[\'h%X] = 9\'h%s; // %s\n' % (programBodyIx,programBody[ix][0:3],programBody[ix][4:]));
      programBodyIx = programBodyIx + 1;
  for ix in range(programBodyIx,nInstructions):
    fp.write('  s_opcodeMemory[\'h%X] = 9\'h000;\n' % ix);
  fp.write('end\n');

def genLocalParam(fp,config):
  fp.write('localparam C_PC_WIDTH                              = %4d;\n' % CeilLog2(config['nInstructions']));
  fp.write('localparam C_RETURN_PTR_WIDTH                      = %4d;\n' % CeilLog2(config['return_stack']));
  fp.write('localparam C_DATA_PTR_WIDTH                        = %4d;\n' % CeilLog2(config['data_stack']));

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
  if len(memories['list']) == 0:
    fp.write('wire [7:0] s_memory = 8\'h00;\n');
  elif len(memories['list']) == 1:
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

def genModule(fp,outCoreName,inport,outport,parameters):
  fp.write('module %s(\n' % outCoreName);
  fp.write('  // synchronous reset and processor clock\n');
  fp.write('  input  wire           i_rst,\n');
  fp.write('  input  wire           i_clk');
  if inport['config']:
    fp.write(',\n');
    fp.write('  // inports\n');
    for ix in range(len(inport['config'])):
      configs = inport['config'][ix];
      names = inport['name'][ix];
      for jx in range(len(configs)):
        if (ix != 0) or (jx != 0):
          fp.write(',\n');
        if re.match(r'\d+-bit',configs[jx]):
          inport['haveBitSignals'] = True;
          a = re.findall(r'(\d+)',configs[jx]);
          portLength = int(a[0]);
          if portLength == 1:
            fp.write('  input  wire           %s' % names[jx]);
          elif portLength < 10:
            fp.write('  input  wire     [%d:0] %s' % (portLength-1,names[jx]));
          else:
            fp.write('  input  wire    [%d:0] %s' % (portLength-1,names[jx]));
        elif configs[jx] == 'set-reset':
          if len(configs) != 1:
            raise SSBCCException('set-reset cannot be used with other signal types');
          fp.write('  input  wire           %s' % names[jx]);
        elif configs[jx] == 'strobe':
          fp.write('  output reg            %s' % names[jx]);
        else:
          raise SSBCCException('Unrecognized INPORT type: "%s"' % configs[jx]);
  if outport['config']:
    fp.write(',\n');
    fp.write('  // outports\n');
    for ix in range(len(outport['config'])):
      configs = outport['config'][ix];
      names = outport['name'][ix];
      for jx in range(len(configs)):
        if (ix != 0) or (jx != 0):
          fp.write(',\n');
        if re.match(r'\d+-bit',configs[jx]):
          a = re.findall(r'(\d+)',configs[jx]);
          portLength = int(a[0]);
          if portLength == 1:
            fp.write('  output reg            %s' % names[jx]);
          elif portLength < 10:
            fp.write('  output reg      [%d:0] %s' % (portLength-1,names[jx]));
          else:
            fp.write('  output reg     [%d:0] %s' % (portLength-1,names[jx]));
        elif configs[jx] == 'strobe':
          fp.write('  output reg            %s' % names[jx]);
        else:
          raise SSBCCException('Unrecognized INPORT type: "%s"' % configs[jx]);
  fp.write('\n');
  fp.write(');\n');
  if parameters['name']:
    fp.write('\n');
    for ix in range(len(parameters['name'])):
      fp.write('parameter [7:0] %s = 8\'h%02X;\n' % (parameters['name'][ix],int(parameters['default'][ix])));

def genOutports(fp,outport):
  if not outport['config']:
    fp.write('// no output ports\n');
    return;
  for ix in range(len(outport['config'])):
    configs = outport['config'][ix];
    names = outport['name'][ix];
    for jx in range(len(configs)):
      if re.match(r'\d+-bit',configs[jx]):
        a = re.findall(r'(\d+)',configs[jx]);
        portLength = int(a[0]);
        fp.write('initial %s = %d\'h0;\n' % (names[jx],portLength));
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= %d\'h0;\n' % (names[jx],portLength));
        fp.write('  else if (s_outport && (s_T == 8\'h%02X))\n' % ix);
        fp.write('    %s <= s_N[0+:%d];\n' % (names[jx],portLength));
        fp.write('  else\n');
        fp.write('    %s <= %s;\n' % (names[jx],names[jx]));
        fp.write('\n');
      elif configs[jx] == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % names[jx]);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % names[jx]);
        fp.write('  else if (s_outport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (names[jx],ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % names[jx]);
        fp.write('\n');
      else:
        raise SSBCCException('Unrecognized OUTPORT type: "%s"' % configs[jx]);

def genUserHeader(fp,user_header):
  for ix in range(len(user_header)):
    fp.write('// %s\n' % user_header[ix]);
