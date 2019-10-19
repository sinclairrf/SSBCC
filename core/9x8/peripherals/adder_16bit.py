################################################################################
#
# Copyright 2012-2013, Sinclair R.F., Inc.
# Copyright 2019, Rodney Sinclair
#
################################################################################

from ssbccPeripheral import SSBCCperipheral

class adder_16bit(SSBCCperipheral):
  """
  The documentation is recorded in the file adder_16bit.md
  """

  def __init__(self,peripheralFile,config,params,loc):
    # Use the externally provided file name for the peripheral
    self.peripheralFile = peripheralFile
    # List the signals to be declared for the peripheral.
    config.AddSignal('s__adder_16bit_out_MSB',8,loc)
    config.AddSignal('s__adder_16bit_out_LSB',8,loc)
    config.AddSignal('s__adder_16bit_in_MSB1',8,loc)
    config.AddSignal('s__adder_16bit_in_LSB1',8,loc)
    config.AddSignal('s__adder_16bit_in_MSB2',8,loc)
    config.AddSignal('s__adder_16bit_in_LSB2',8,loc)
    config.AddSignal('s__adder_16bit_in_op',1,loc)
    # List the input ports to the peripheral.
    config.AddInport(('I_ADDER_16BIT_MSB',
                     ('s__adder_16bit_out_MSB',8,'data',),
                    ),loc)
    config.AddInport(('I_ADDER_16BIT_LSB',
                     ('s__adder_16bit_out_LSB',8,'data',),
                    ),loc)
    # List the output ports from the peripheral.
    config.AddOutport(('O_ADDER_16BIT_MSB1',False,
                       ('s__adder_16bit_in_MSB1',8,'data',),
                     ),loc)
    config.AddOutport(('O_ADDER_16BIT_LSB1',False,
                      ('s__adder_16bit_in_LSB1',8,'data',),
                     ),loc)
    config.AddOutport(('O_ADDER_16BIT_MSB2',False,
                      ('s__adder_16bit_in_MSB2',8,'data',),
                     ),loc)
    config.AddOutport(('O_ADDER_16BIT_LSB2',False,
                      ('s__adder_16bit_in_LSB2',8,'data',),
                     ),loc)
    config.AddOutport(('O_ADDER_16BIT_OP',False,
                      ('s__adder_16bit_in_op',1,'data',),
                     ),loc)

  def GenAssembly(self,config):
    body = self.LoadCore(self.peripheralFile,'.s')
    with open('adder_16bit.s','w') as fp:
      fp.write(body)

  def GenVerilog(self,fp,config):
    body = self.LoadCore(self.peripheralFile,'.v')
    for subpair in (
        ( r'@UC_CLK@', 'i_clk', ),
      ):
      body = re.sub(subpair[0],subpair[1],body)
    body = self.GenVerilogFinal(config,body)
    fp.write(body)
