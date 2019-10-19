//
// PERIPHERAL:  adder_16bit
//

always @ (posedge @UC_CLK@)
  if (s__adder_16bit_in_op == 1'b0)
    { s__adder_16bit_out_MSB, s__adder_16bit_out_LSB }
      <= { s__adder_16bit_in_MSB1, s__adder_16bit_in_LSB1 }
       + { s__adder_16bit_in_MSB2, s__adder_16bit_in_LSB2 };
  else
    { s__adder_16bit_out_MSB, s__adder_16bit_out_LSB }
      <= { s__adder_16bit_in_MSB1, s__adder_16bit_in_LSB1 }
       - { s__adder_16bit_in_MSB2, s__adder_16bit_in_LSB2 };
