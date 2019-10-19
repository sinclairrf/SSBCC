//
// monitor_stack peripheral
// Copyright 2013-2015, Sinclair R.F., Inc.
// Copyright 2019, Rodney Sinclair
//
// Note: The validity of N and T are not monitored for invalid operations.  For
//       example, if N is not valid and a "swap" is performed, then the data
//       stack is no longer valid and an error is detected.  Thus, the validity
//       of N and T do not need to be monitored for "swap" operations. 

generate

// Detect over-large PC values for non-power-of-2 PC ranges.
reg s__PC_error = 1'b0;
localparam L__INSTRUCTION_MAX = @NINSTRUCTIONS-1@;
always @ (posedge @UC_CLK@)
  if (~&L__INSTRUCTION_MAX[0+:C_PC_WIDTH] && (s_PC > L__INSTRUCTION_MAX[0+:C_PC_WIDTH])) begin
    $display("%t : PC passed instruction space in @CORENAME@", $time);
    s__PC_error <= 1'b1;
  end

//
// track validiuty of the data and return stacks and registers
//

reg s__N_valid;
reg s__R_valid;
reg s__T_valid;
reg s__data_stack_valid;
reg s__return_stack_valid;

// s_T validity tracking
initial s__T_valid = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__T_valid <= 1'b0;
  else if (s_interrupt || s_interrupted)
    s__T_valid <= s__T_valid;
  else case (s_bus_t)
    C_BUS_T_OPCODE:     s__T_valid <= 1'b1;
    C_BUS_T_N:          s__T_valid <= s__N_valid;
    C_BUS_T_PRE:        case (s_opcode[0+:2])
                          2'b00: s__T_valid <= s__T_valid;
                          2'b01: s__T_valid <= s__R_valid;
                          2'b10: s__T_valid <= s__N_valid;
                          default : s__T_valid <= s__T_valid;
                        endcase
    C_BUS_T_LOGIC:      case (s_opcode[2])
                          1'b0: s__T_valid <= s__T_valid;
                          1'b1: s__T_valid <= s__N_valid;
                          default : s__T_valid <= s__T_valid;
                        endcase
    default:            s__T_valid <= s__T_valid;
  endcase

// s_N validity tracking
initial s__N_valid = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__N_valid <= 1'b0;
  else case (s_bus_n)
    C_BUS_N_N:          s__N_valid <= s__N_valid;
    C_BUS_N_STACK:      s__N_valid <= s__data_stack_valid;
    C_BUS_N_T:          s__N_valid <= s__T_valid;
    C_BUS_N_MEM:        s__N_valid <= 1'b1;
    default:            s__N_valid <= s__N_valid;
  endcase

// the data stack is valid if s_N is valid and it remains valid until the data
// stack pointer will decrement below zero
initial s__data_stack_valid = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__data_stack_valid <= 1'b0;
  else if (s_stack == C_STACK_INC)
    s__data_stack_valid <= s__N_valid;
  else if ((s_stack == C_STACK_DEC) && (s_Np_stack_ptr == {(C_DATA_PTR_WIDTH){1'b0}}))
    s__data_stack_valid <= 1'b0;
  else
    s__data_stack_valid <= s__data_stack_valid;

// detect malformed stack conditions (underflows, overflows, inversion, ...)
reg s__data_stack_error = 1'b0;
@OUTPORT_PURE_STROBE@
always @ (posedge @UC_CLK@)
  if (!s__data_stack_error) begin
    if ((s_stack == C_STACK_DEC) && !s__T_valid) begin
      $display("%t : Data stack underflow in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if ((s_stack == C_STACK_INC) && (s_Np_stack_ptr == {(C_DATA_PTR_WIDTH){1'b1}}) && s__data_stack_valid) begin
      $display("%t : Data stack overflow in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if (s__N_valid && !s__T_valid) begin
      $display("%t : Data stack validity inversion in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if (!s__T_valid && (s_Np_stack_ptr != { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 })) begin
      $display("%t : Malformed top-of-data-stack validity in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if (!s__N_valid && (s_Np_stack_ptr[2+:C_DATA_PTR_WIDTH-2] != {(C_DATA_PTR_WIDTH-2){1'b1}})) begin
      $display("%t : Malformed next-to-top-of-data-stack validity in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if (s_interrupt || s_interrupted)
      ; // do nothing
    else case (s_bus_t)
      C_BUS_T_MATH_ROTATE:
        if (!s__T_valid && (s_opcode[0+:3] != 3'h0)) begin
          $display("%t : Illegal rotate on invalid top of data stack in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end
      C_BUS_T_ADDER:
        if ((s_opcode[3+:4] == 4'b0011) && (!s__N_valid || !s__T_valid)) begin
          $display("%t : Invalid addition in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end else if (!s__T_valid) begin
          $display("%t : Invalid increment or decrement in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end
      C_BUS_T_COMPARE:
        if (!s__T_valid) begin
          $display("%t : Comparison on invalid top of data stack in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end
      C_BUS_T_INPORT:
        if (!s__T_valid) begin
          $display("%t : Inport using invalid top of data stack for address in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end
      C_BUS_T_LOGIC:
        case (s_opcode[0+:3])
          3'b000, 3'b001, 3'b010:
            if (!s__N_valid || !s__T_valid) begin
              $display("%t : Illegal logical operation in @CORENAME@", $time);
              s__data_stack_error <= 1'b1;
            end
          3'b011:
            if (!s__N_valid || !s__T_valid) begin
              $display("%t : Illegal nip in @CORENAME@", $time);
              s__data_stack_error <= 1'b1;
            end
          3'b100, 3'b101, 3'b110, 3'b111:
            ;
          default:
            ;
        endcase
      C_BUS_T_MEM:
        if (!s__T_valid) begin
          $display("%t : Fetch using invalid top-of-data-stack in @CORENAME@", $time);
          s__data_stack_error <= 1'b1;
        end
      default:
        ;
    endcase
    if (s_interrupt || s_interrupted)
      ; // do nothing
    else if ((s_opcode == 9'b00_0111_000) && !s__T_valid) begin
      $display("%t : Outport with invalid top-of-data-stack in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
    if ((s_opcode == 9'b00_0111_000) && !s__N_valid && !s__outport_pure_strobe) begin
      $display("%t : Outport with invalid next-to-top-of-data-stack in @CORENAME@", $time);
      s__data_stack_error <= 1'b1;
    end
  end

// s_R validity tracking
initial s__R_valid = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__R_valid <= 1'b0;
  else if (s_return == C_RETURN_INC)
    s__R_valid <= 1'b1;
  else if (s_return == C_RETURN_DEC)
    s__R_valid <= s__return_stack_valid;
  else
    s__R_valid <= s__R_valid;

// the return stack is valid if s_R is valid and it remains valid until the
// return stack pointer will decrement below zero
initial s__return_stack_valid = 1'b0;
always @ (posedge @UC_CLK@)
  if (@UC_RST@)
    s__return_stack_valid <= 1'b0;
  else if (s_return == C_RETURN_INC)
    s__return_stack_valid <= s__R_valid;
  else if (s_return == C_RETURN_DEC)
    if (s_R_stack_ptr == {(C_RETURN_PTR_WIDTH){1'b0}})
      s__return_stack_valid <= 1'b0;
    else
      s__return_stack_valid <= s__return_stack_valid;
  else
    s__return_stack_valid <= s__return_stack_valid;

reg s__return_stack_error = 1'b0;
always @ (posedge @UC_CLK@)
  if (!s__return_stack_error) begin
    if ((s_return == C_RETURN_DEC) && !s__R_valid) begin
      $display("%t : Return stack underflow in @CORENAME@", $time);
      s__return_stack_error <= 1'b1;
    end
    if ((s_return == C_RETURN_INC) && (s_R_stack_ptr == {(C_RETURN_PTR_WIDTH){1'b1}}) && s__return_stack_valid) begin
      $display("%t : Return stack overflow in @CORENAME@", $time);
      s__return_stack_error <= 1'b1;
    end
  end

reg s__R_is_address = 1'b0;
reg [2**C_RETURN_PTR_WIDTH-1:0] s__return_is_address = {(2**C_RETURN_PTR_WIDTH){1'b0}};
always @ (posedge @UC_CLK@)
  if (@UC_RST@) begin
    s__R_is_address <= 1'b0;
    s__return_is_address <= {(2**C_RETURN_PTR_WIDTH){1'b0}};
  end else if (s_return == C_RETURN_INC) begin
    s__R_is_address <= s_interrupt || (s_bus_r == C_BUS_R_PC);
    s__return_is_address[s_R_stack_ptr_next] <= s__R_is_address;
  end else if (s_return == C_RETURN_DEC) begin
    s__R_is_address <= s__return_is_address[s_R_stack_ptr];
  end

reg s__R_address_error = 1'b0;
always @ (posedge @UC_CLK@)
  if (!s__R_address_error) begin
    if ((s_bus_pc == C_BUS_PC_RETURN) && !s__R_is_address) begin
      $display("%t : Non-address by return instruction in @CORENAME@", $time);
      s__R_address_error <= 1'b1;
    end
    if (s_interrupt || s_interrupted)
      ; // do nothing
    else if (((s_opcode == 9'b00_0001_001) || (s_opcode == 9'b00_1001_001)) && s__R_is_address) begin
      $display("%t : Copied address to data stack in @CORENAME@", $time);
      s__R_address_error <= 1'b1;
    end
  end

reg s__range_error = 1'b0;
reg [8:0] s__mem_address_limit[0:3];
initial begin
  s__mem_address_limit[0] = @MEM_LIMIT_0@;
  s__mem_address_limit[1] = @MEM_LIMIT_1@;
  s__mem_address_limit[2] = @MEM_LIMIT_2@;
  s__mem_address_limit[3] = @MEM_LIMIT_3@;
end
always @ (posedge @UC_CLK@)
  if (s_interrupt || s_interrupted) begin
    // do nothing
  end else if ((s_opcode[3+:6] == 6'b000110) && ({ 1'b0, s_T } >= @LAST_INPORT@)) begin
    $display("%t : Range error on inport in @CORENAME@", $time);
    s__range_error <= 1'b1;
  end else if ((s_opcode[3+:6] == 6'b000111) && ({ 1'b0, s_T } >= @LAST_OUTPORT@)) begin
    $display("%t : Range error on outport in @CORENAME@", $time);
    s__range_error <= 1'b1;
  end else if ((s_opcode[5+:4] == 4'b0011) && ({ 1'b0, s_T } >= s__mem_address_limit[s_opcode[0+:2]])) begin
    $display("%t : Range error on memory operation in @CORENAME@", $time);
    s__range_error <= 1'b1;
  end

// record the execution history
reg       [L__TRACE_SIZE-1:0] s__history[@HISTORY-1@:0];
reg                     [8:0] s__opcode_s = 9'b0;
reg          [C_PC_WIDTH-1:0] s__PC_s[1:0];
reg                           s__interrupt_s = 1'b0;
reg                           s__interrupted_s = 1'b0;
integer ix__history;
initial begin
  for (ix__history=0; ix__history<@HISTORY@; ix__history=ix__history+1)
    s__history[ix__history] = {(L__TRACE_SIZE){1'b0}};
  s__PC_s[0] = {(C_PC_WIDTH){1'b0}};
  s__PC_s[1] = {(C_PC_WIDTH){1'b0}};
end
always @ (posedge @UC_CLK@) begin
  s__PC_s[1] <= s__PC_s[0];
  s__PC_s[0] <= s_PC;
  s__interrupt_s <= s_interrupt;
  s__interrupted_s <= s_interrupted;
  s__opcode_s <= s_opcode;
  for (ix__history=1; ix__history<@HISTORY@; ix__history=ix__history+1)
    s__history[ix__history-1] <= s__history[ix__history];
  // pack as per ../display_trace.v
  s__history[@HISTORY-1@] <= {
    s__interrupt_s,
    s__interrupted_s,
    s__PC_s[1],
    s__opcode_s,
    s_Np_stack_ptr,
    s__N_valid,
    s_N,
    s__T_valid,
    s_T,
    s__R_valid,
    s_R,
    s_R_stack_ptr
  };
end

// if any error occurs then print the history and terminate the simulation
wire s_terminate = s__PC_error || s__data_stack_error || s__return_stack_error || s__R_address_error || s__range_error;
always @ (posedge s_terminate) begin
  for (ix__history=0; ix__history<@HISTORY@; ix__history=ix__history+1)
    display_trace(s__history[ix__history]);
  display_trace({
    s_interrupt,
    s_interrupted,
    s__PC_s[1],
    s__opcode_s,
    s_Np_stack_ptr,
    s__N_valid,
    s_N,
    s__T_valid,
    s_T,
    s__R_valid,
    s_R,
    s_R_stack_ptr
  });
  $finish;
end

endgenerate
