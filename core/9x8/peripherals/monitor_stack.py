################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
################################################################################

import math
import re

class monitor_stack:
  """Simulation-specific peripheral to flag invalid stack operations.

Invalid data stack operations are:
  pushing onto a full data stack
  dropping from an empty data stack
  nipping from an almost empty data stack

Invalid return stack operations are:
  pushing onto a full return stack
  dropping values from an empty return stack
  returns from a data entry on the return stack
  non-return  operations from an address entry on the return stack

Invalid data operations are:
  swap on an empty or almost empty data stack
  in-place operations on an empty or almost empty data stack

Usage:
  PERIPHERAL monitor_stack \\
             [nofinish|finish=n] \\
             [history==n] \\
             [log=filename]
Where:
  nofinish
    do not terminate the simulation when an error is encountered
  finish=n
    terminate the simulation n processor clock cycles after an error is
    encountered
    Note:  The normal behavior is to terminate the simulation when an error is
           encountered.
    Note:  This might be done to confirm that a stack error is causing observed
           defective behavior in hardware.
  history=n
    display the n most recent operations when a stack error is encountered
    Note:  Normally no history is printed.
  log=filename
    store a trace of the simulation in filename
"""

  def __init__(self,config.param_list):
    self.finish = None;
    self.log = None;
    for param in param_list:
      param_name = param_list[0];
      param_arg = param_list[1:];
      if param_name == 'nofinish':
        if type(self.finish) != type(None):
          raise SSBCCException('"nofinish" not valid in this contect');
        if len(param_arg) != 0:
          raise SSBCCException('"nofinish" does not take an argument');
        self.finish = False;
      elif param_name == 'finish':
        if type(self.finish) != type(None):
          raise SSBCCException('"finish" not valid in this context');
        if len(param_arg) != 1;
          raise SSBCCException('"finish" requires exactly one value');
        self.finish = int(param_arg[0]);
        if self.finish < 1:
          raise SSBCCException('"finish" value must be 1 or more');
      elif param_name == 'log':
        if type(self.log) != type(None):
          raise SSBCCException('"log" can only be specified once');
        if len(param_arg) != 1:
          raise SSBCCException('"log" requires the output file name');
        self.log = param_arg[0];
      else:
        raise SSBCCException('Unrecognized parameter: "%s"' % param_name);
    if type(self.finish) == type(None):
      self.finish = 0;

  def GenHDL(self,fp,config):
    if config['hdl'] == 'Verilog':
      self.GenVerilog(fp,config);
    else:
      raise Exception('HDL "%s" not implemented' % config['hdl']);

  def GenVerilog(self,fp.config):
    # The validity of N and T are not monitored for invalid operations.  For
    # example, if N is not valid and a "swap" is performed, then the data stack
    # is no longer valid and an error is detected.  Thus, the validity of N and
    # T do not need to be monitored for "swap" operations. 
    body = """
//
// monitor_stack peripheral
//
generate
reg s_data_stack_valid;
reg s_N_valid;
reg s_R_valid;
reg s_T_valid;
//
initial s_T_valid = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s_T_valid <= 1'b0;
  else case (s_bus_t)
    C_BUS_T_OPCODE:     s_T_valid <= 1'b1;
    C_BUS_T_N:          s_T_valid <= s_N_valid;
    C_BUS_T_PRE:        case (s_opcode[0+:2])
                          2'b00: s_T_valid <= s_T_valid;
                          2'b01: s_T_valid <= s_R_valid;
                          2'b10: s_T_valid <= s_N_valid;
                        endcase
    C_BUS_T_LOGIC:      case (s_opcode[2])
                          1'b0: s_T_valid <= s_T_valid;
                          1'b1: s_T_valid <= s_N_valid;
                        endcase
    default:            s_T_valid <= s_T_valid;
  endcase
//
initial s_N_valid = 1'b0;
always @ (posedge i_clk)
  if (r_rst)
    s_N_valid <= 1'b0;
  else case (s_bus_n)
    C_BUS_N_N:          s_N_valid <= s_N_valid;
    C_BUS_N_STACK:      s_N_valid <= s_data_stack_valid;
    C_BUS_N_T:          s_N_valid <= s_T_valid;
    C_BUS_N_MEM:        s_N_valid <= 1'b1;
    default:            s_N_valid <= s_N_valid;
  endcase
//
initial s_data_stack_valid = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s_data_stack_valid <= 1'b0;
  else if (s_stack == C_STACK_INC)
    s_data_stack_valid <= s_N_valid;
  else if ((s_stack == C_STACK_DEC) && (s_Np_stack_ptr == {(C_DATA_PTR_WIDTH){1'b0}}))
    s_data_stack_valid <= 1'b0;
  else
    s_data_stack_valid <= s_data_stack_valid;
//
reg s_data_stack_error = 1'b0;
always @ (posedge i_clk)
  if (!s_data_stack_error) begin
    if ((s_stack == C_STACK_DEC) && !s_T_valid) begin
      $display("Data stack underflow");
      s_data_stack_error <= 1'b1;
    end
    if ((s_stack == C_STACK_INC) && (s_Np_stack_ptr == {(C_DATA_PTR_WIDTH){1'b1}}) && s_data_stack_valid) begin
      $display("Data stack overflow");
      s_data_stack_error <= 1'b1;
    end
    if (s_N_valid && !s_T_valid) begin
      $display("Data stack validity inversion");
      s_data_stack_error <= 1'b1;
    end
    if (!s_T_valid && (s_Np_stack_ptr != { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 })) begin
      $display("Malformed top-of-data-stack validity");
      s_data_stack_error <= 1'b1;
    end
    if (!s_N_valid && (s_Np_stack_ptr != {(C_DATA_PTR_WIDTH){1'b1}})) begin
      $display("Malformed next-to-top-of-data-stack validity");
      s_data_stack_error <= 1'b1;
    end
    case (s_bus_t)
      C_BUS_T_MATH_ROTATE:
        if (!s_T_valid && (s_opcode != 9'h000)) begin
          $display("Illegal rotate on invalid top of data stack");
          s_data_stack_error <= 1'b1;
        end
      C_BUS_T_ADDER:
        if (!s_N_valid || !s_T_valid) begin
          $display("Invalid addition");
          s_data_stack_error <= 1'b1;
        end
      C_BUS_T_COMPARE:
        if (!s_T_valid) begin
          $display("Comparison on invalid top of data stack");
          s_data_stack_error <= 1'b1;
        end
      C_BUS_T_INPORT:
        if (!s_T_valid) begin
          $display("Inport using invalid top of data stack for address");
          s_data_stack_error <= 1'b1;
        end
      C_BUS_T_LOGIC:
        case (s_opcode[0+:3])
          3'b000, 3'b001, 3'b010:
            if (!s_N_valid || !s_T_valid) begin
              $display("Illegal logical operation");
              s_data_stack_error <= 1'b1;
            end
          3'b011:
            if (!s_N_valid || !s_T_valid) begin
              $display("Illegal nip");
              s_data_stack_error <= 1'b1;
            end
          3'b100, 3'b101, 3'b110, 3'b111:
            ;
          default:
            ;
        endcase
      C_BUS_T_MEM:
        if (!s_T_valid)
          $display("Fetch using invalid top-of-data-stack");
          s_data_stack_error <= 1'b1;
        end
    endcase
  end
endgenerate
""";
    data_stack_width = math.ceil(math.log(config['data_stack'],2));
    np_stack_ptr_max = (-1 % 2**data_stack);
    for subs in (
                  ('@S_NP_STACK_PTR_MAX@', "%d'%X" % (data_stack_width,np_stack_ptr_max),
                  ('@S_NP_STACK_PTR_MAX_M1@', "%d'%X" % (data_stack_width,np_stack_ptr_max-1),
                );
