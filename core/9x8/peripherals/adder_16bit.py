################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Generate a 16-bit adder peripheral to the core.
#
# The core has the following inputs from the adder:
#   port                description
#   I_ADDER_16BIT_MSB   MSB of the sum/difference
#   I_ADDER_16BIT_LSB   LSB of the sum/difference
#
# The core has the following outputs to the adder:
#   port                description
#   O_ADDER_16BIT_MSB1  MSB of first argument
#   O_ADDER_16BIT_LSB1  LSB of first argument
#   O_ADDER_16BIT_MSB2  MSB of second argument
#   O_ADDER_16BIT_LSB2  LSB of second argument
#   O_ADDER_16BIT_OP    0 ==> add, 1 ==> subtract
#
################################################################################

class adder_16bit:

  def __init__(self,config,params):
    # List the signals to be declared for the peripheral.
    config['signals'].append(('s_adder_16bit_out_MSB',8,));
    config['signals'].append(('s_adder_16bit_out_LSB',8,));
    config['signals'].append(('s_adder_16bit_in_MSB1',8,));
    config['signals'].append(('s_adder_16bit_in_LSB1',8,));
    config['signals'].append(('s_adder_16bit_in_MSB2',8,));
    config['signals'].append(('s_adder_16bit_in_LSB2',8,));
    config['signals'].append(('s_adder_16bit_in_op',1,));
    # List the input ports to the core.
    config['inports'].append( ('I_ADDER_16BIT_MSB',(('s_adder_16bit_out_MSB',8,'data',),),) );
    config['inports'].append( ('I_ADDER_16BIT_LSB',(('s_adder_16bit_out_LSB',8,'data',),),) );
    # List the output ports to the core.
    config['outports'].append( ('O_ADDER_16BIT_MSB1', (('s_adder_16bit_in_MSB1',8,'data',),),) );
    config['outports'].append( ('O_ADDER_16BIT_LSB1', (('s_adder_16bit_in_LSB1',8,'data',),),) );
    config['outports'].append( ('O_ADDER_16BIT_MSB2', (('s_adder_16bit_in_MSB2',8,'data',),),) );
    config['outports'].append( ('O_ADDER_16BIT_LSB2', (('s_adder_16bit_in_LSB2',8,'data',),),) );
    config['outports'].append( ('O_ADDER_16BIT_OP', (('s_adder_16bit_in_op',1,'data',),),) );

  def GenAssembly(self,config):
    fp = fopen('adder_16bit.s');
    fp.write('; Copyright 2012, Sinclair R.F., Inc.\n');
    fp.write('; adder_16bit.s\n');
    fp.write('; library to facilitate using the 16-bit adder peripheral\n');
    fp.write('\n');
    fp.write('; ( u_1_LSB u_1_MSB u_2_LSB u_2_MSB - (u_1+u_2)_LSB (u_1+u_2)_MSB )\n');
    fp.write('.function adder_16bit_add\n');
    fp.write('  .outport(O_ADDER_16BIT_MSB2) .outport(O_ADDER_16BIT_LSB2)\n');
    fp.write('  .outport(O_ADDER_16BIT_MSB1) .outport(O_ADDER_16BIT_LSB1)\n');
    fp.write('  0 .outport(O_ADDER_16BIT_OP)\n');
    fp.write('  .inport(I_ADDER_16BIT_LSB) .inport(I_ADDER_16BIT_MSB)\n');
    fp.write('.return\n');
    fp.write('\n');
    fp.write('; ( u_1_LSB u_1_MSB u_2_LSB u_2_MSB - (u_1-u_2)_LSB (u_1-u_2)_MSB )\n');
    fp.write('.function adder_16bit_sub\n');
    fp.write('  .outport(O_ADDER_16BIT_MSB2) .outport(O_ADDER_16BIT_LSB2)\n');
    fp.write('  .outport(O_ADDER_16BIT_MSB1) .outport(O_ADDER_16BIT_LSB1)\n');
    fp.write('  1 .outport(O_ADDER_16BIT_OP)\n');
    fp.write('  .inport(I_ADDER_16BIT_LSB) .inport(I_ADDER_16BIT_MSB)\n');
    fp.write('.return\n');

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp,config):
    fp.write('always @ (posedge i_clk)\n');
    fp.write('  if (s_adder_16bit_in_op == 1\'b0)\n');
    fp.write('    { s_adder_16bit_out_MSB, s_adder_16bit_out_MSB }\n');
    fp.write('      <= { s_adder_16bit_in_MSB1, s_adder_16bit_in_LSB1 }\n');
    fp.write('       + { s_adder_16bit_in_MSB2, s_adder_16bit_in_LSB2 };\n');
    fp.write('  else\n');
    fp.write('    { s_adder_16bit_out_MSB, s_adder_16bit_out_MSB }\n');
    fp.write('      <= { s_adder_16bit_in_MSB1, s_adder_16bit_in_LSB1 }\n');
    fp.write('       - { s_adder_16bit_in_MSB2, s_adder_16bit_in_LSB2 };\n');
