/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * SSBCC.9x8 -- Small Stack Based Computer Compiler, 9-bit opcode, 8-bit data.
 *
 ******************************************************************************/

//@SSBCC@ user_header

//@SSBCC@ module

//@SSBCC@ localparam
localparam C_PC_WIDTH           = 11;

localparam C_RETURN_WIDTH = (C_PC_WIDTH <= 8) ? 8 : C_PC_WIDTH;

/*******************************************************************************
 *
 * Declare the signals used throughout the system.
 *
 ******************************************************************************/

reg                       [7:0] s_N;            // next-to-top on the data stack
reg        [C_RETURN_WIDTH-1:0] s_R;            // top of return stack
reg                       [7:0] s_T;            // top of the data stack
reg            [C_PC_WIDTH-1:0] s_PC;           // program counter
reg                       [8:0] s_opcode;       // current opcode

/*******************************************************************************
 *
 * Instantiate the ALU operations.  These are listed in the order in which they
 * first occur in the opcodes.
 *
 ******************************************************************************/

// opcode = 000000_xxx
// shifter operations (including "nop" as no shift)
// 6-input LUT formulation -- 3-bit opcode, 3 bits of T centered at current bit
reg [7:0] s_math_rotate;
always @ (s_T,s_opcode)
  case (s_opcode[0+:3])
     3'b000 : s_math_rotate = s_T;                      // nop
     3'b001 : s_math_rotate = { s_T[0+:7], 1'b0 };      // <<0
     3'b010 : s_math_rotate = { s_T[0+:7], 1'b1 };      // <<1
     3'b011 : s_math_rotate = { s_T[0+:7], s_T[0] };    // <<lsb
     3'b100 : s_math_rotate = { 1'b0,      s_T[1+:7] }; // 0>>
     3'b101 : s_math_rotate = { 1'b1,      s_T[1+:7] }; // 1>>
     3'b110 : s_math_rotate = { s_T[7],    s_T[1+:7] }; // msb>>
     3'b111 : s_math_rotate = { s_T[0],    s_T[1+:7] }; // lsb>>
    default : s_math_rotate = s_T;
  endcase

// opcode = 000001_0xx
// T pre-multiplexer for pushing repeated values onto the data stack
reg [7:0] s_T_pre;
always @ (*)
  case (s_opcode[0+:2])
      2'b00 : s_T_pre = s_T;                    // dup
      2'b01 : s_T_pre = s_R[0+:8];              // r@
      2'b10 : s_T_pre = s_N;                    // over
    default : s_T_pre = s_T;
  endcase

// opcode = 000011_xxx
// add,sub,and,or,xor,TBD,drop,nip
reg [7:0] s_math_dual;
always @ (s_T,s_N,s_opcode)
  case (s_opcode[0+:3])
     3'b000 : s_math_dual = s_N + s_T;  // add
     3'b001 : s_math_dual = s_N - s_T;  // sub
     3'b010 : s_math_dual = s_N & s_T;  // and
     3'b011 : s_math_dual = s_N | s_T;  // or
     3'b100 : s_math_dual = s_N ^ s_T;  // xor
     3'b101 : s_math_dual = s_T;        // TBD
     3'b110 : s_math_dual = s_N;        // drop
     3'b111 : s_math_dual = s_T;        // nip
    default : s_math_dual = s_T;
  endcase

// opcode = 000100_xxx
// Test for for the patterns 0_000000_0, 0_000000_1, 0_111111_0, 0_111111_1,
// 1_000000_0, 1_000000_1, 1_111111_0, and 1_111111_1.
wire [7:0] s_T_compare = {(8){&(~{ s_opcode[2], {(6){s_opcode[1]}}, s_opcode[0]} ^ s_T)}};

// increment PC
reg [C_PC_WIDTH-1:0] s_PC_plus1 = {(C_PC_WIDTH){1'b0}};
always @ (*)
  s_PC_plus1 <= s_PC + { {(C_PC_WIDTH-1){1'b0}}, 1'b1 };

// Reduced-warning-message method to extract the jump address from the top of
// the stack and the current opcode.
wire [C_PC_WIDTH-1:0] s_PC_jump;
generate
  if (C_PC_WIDTH <= 8) begin : gen_pc_jump_narrow
    assign s_PC_jump = s_T[0+:C_PC_WIDTH];
  end else begin : gen_pc_jump_wide
    assign s_PC_jump = { s_opcode[0+:C_PC_WIDTH-8], s_T };
  end
endgenerate

/*******************************************************************************
 *
 * Instantiate the input port data selection.
 *
 * Note:  This creates and computes an 8-bit wire called "s_inport".
 *
 ******************************************************************************/

//@SSBCC@ inports

/*******************************************************************************
 *
 * Define the states for the bus muxes and then compute these stated from the
 * 6 msb of the opcode.
 *
 ******************************************************************************/

localparam C_BUS_PC_NORMAL      = 2'b00;
localparam C_BUS_PC_JUMP        = 2'b01;
localparam C_BUS_PC_RETURN      = 2'b11;
reg [1:0] s_bus_pc;

localparam C_BUS_R_T            = 1'b0;         // no-op and push T onto return stack
localparam C_BUS_R_PC           = 1'b1;         // push PC onto return stack
reg s_bus_r;

localparam C_RETURN_NOP         = 2'b00;        // don't change return stack pointer
localparam C_RETURN_INC         = 2'b01;        // add element to return stack
localparam C_RETURN_DEC         = 2'b10;        // remove element from return stack
reg [1:0] s_return;

localparam C_BUS_T_MATH_ROTATE  = 3'b000;       // nop and rotate operations
localparam C_BUS_T_OPCODE       = 3'b001;
localparam C_BUS_T_N            = 3'b010;
localparam C_BUS_T_PRE          = 3'b011;
localparam C_BUS_T_MATH_DUAL    = 3'b100;
localparam C_BUS_T_COMPARE      = 3'b101;
localparam C_BUS_T_INPORT       = 3'b110;
localparam C_BUS_T_MEMORY       = 3'b111;
reg [2:0] s_bus_t;

localparam C_BUS_N_N            = 2'b00;        // don't change N
localparam C_BUS_N_T            = 2'b01;        // replace N with T
localparam C_BUS_N_STACK        = 2'b10;        // replace N with third-on-stack
reg [1:0] s_bus_n;

localparam C_STACK_NOP          = 2'b00;        // don't change internal data stack pointer
localparam C_STACK_INC          = 2'b01;        // add element to internal data stack
localparam C_STACK_DEC          = 2'b10;        // remove element from internal data stack
reg [1:0] s_stack;

reg s_interrupt_enabled         = 1'b0;
reg s_interrupt_enabled_change  = 1'b0;
reg s_interrupt_enabled_next    = 1'b0;
reg s_interrupt_holdoff         = 1'b0;
reg s_outport                   = 1'b0;

always @ (*) begin
  // default operation is nop/math_rotate
  s_bus_pc      = C_BUS_PC_NORMAL;
  s_bus_r       = C_BUS_R_T;
  s_return      = C_RETURN_NOP;
  s_bus_t       = C_BUS_T_MATH_ROTATE;
  s_bus_n       = C_BUS_N_N;
  s_stack       = C_STACK_NOP;
  s_interrupt_enabled_change    = 1'b1;
  s_interrupt_enabled_next      = s_interrupt_enabled;
  s_interrupt_holdoff           = 1'b0;
  s_outport     = 1'b0;
  if (s_opcode[8] == 1'b1) begin // push
    s_bus_t     = C_BUS_T_OPCODE;
    s_bus_n     = C_BUS_N_T;
    s_stack     = C_STACK_INC;
  end else if (s_opcode[6+:2] == 2'b10) begin // jump
    s_bus_pc    = C_BUS_PC_JUMP;
    s_bus_t     = C_BUS_T_N;
    s_bus_n     = C_BUS_N_STACK;
    s_stack     = C_STACK_DEC;
    s_interrupt_holdoff = 1'b1;
  end else if (s_opcode[6+:2] == 2'b11) begin // jumpc
    if (|s_N) begin
      s_bus_pc  = C_BUS_PC_JUMP;
    end
    s_bus_t     = C_BUS_T_N;
    s_bus_n     = C_BUS_N_STACK;
    s_stack     = C_STACK_DEC;
    s_interrupt_holdoff = 1'b1;
  end else case (s_opcode[3+:4])
      4'b0000:  // nop, math_rotate
                ;
      4'b0001:  begin // dup, r@, over
                s_bus_t         = C_BUS_T_PRE;
                s_bus_n         = C_BUS_N_T;
                s_stack         = C_STACK_INC;
                end
      4'b0010:  begin // swap
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_T;
                end
      4'b0011:  begin // dual-operand math:  add,sub,TBD,TBD,and,or,xor,nip
                s_bus_t         = C_BUS_T_MATH_DUAL;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b0100:  begin // 0=, -1=
                s_bus_t         = C_BUS_T_COMPARE;
                end
      4'b0101:  begin // return
                s_bus_pc        = C_BUS_PC_RETURN;
                s_return        = C_RETURN_DEC;
                end
      4'b0110:  begin // inport
                s_bus_t         = C_BUS_T_INPORT;
                end
      4'b0111:  begin // outport
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                s_outport       = 1'b1;
                end
      4'b1000:  begin // call
                s_bus_r         = C_BUS_R_PC;
                if (|s_T)
                s_return        = C_RETURN_INC;
                end
      4'b1001:  begin // callc
                s_bus_r         = C_BUS_R_PC;
                if (|s_T)
                  s_return      = C_RETURN_INC;
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b1010:  // unused
                ;
      4'b1011:  begin // >r
                s_return        = C_RETURN_INC;
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b1100:  begin // r> (pop the return stack and push it onto the data stack)
                s_return        = C_RETURN_DEC;
                s_bus_t         = C_BUS_T_PRE;
                s_bus_n         = C_BUS_N_T;
                s_stack         = C_STACK_INC;
                end
      4'b1101:  // store
                ; // TODO -- implement this instruction
                //s_interrupt_enabled_change = 1'b1;
                //s_interrupt_enabled_next = s_opcode[0];
      4'b1110:  // fetch (low)
                ; // TODO -- implement this instruction
      4'b1111:  // fetch (high) -- same as fetch (low)
                ; // TODO -- implement this instruction
      default:  // nop
                ;
    endcase
end

/*******************************************************************************
 *
 * Operate the MUXes
 *
 ******************************************************************************/

// non-clocked PC required for shadow register in SRAM blocks
reg [C_PC_WIDTH-1:0] s_PC_next;
always @ (*)
  case (s_bus_pc)
    C_BUS_PC_NORMAL:
      s_PC_next = s_PC_plus1;
    C_BUS_PC_JUMP:
      s_PC_next = s_PC_jump;
    C_BUS_PC_RETURN:
      s_PC_next = s_R[0+:C_PC_WIDTH];
    default:
      s_PC_next = s_PC_plus1;
  endcase

// Hold candidate value of PC for return stack.
reg [C_PC_WIDTH-1:0] s_PC_return;
always @ (posedge i_clk)
  s_PC_return <= s_PC_plus1;

// Return stack candidate
reg [C_RETURN_WIDTH-1:0] s_R_pre;
generate
  if (C_PC_WIDTH < 8) begin : gen_r_narrow
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = s_T;
        C_BUS_R_PC:
          s_R_pre = { {(8-C_PC_WIDTH){1'b0}}, s_PC_return };
        default:
          s_R_pre = s_T;
      endcase
  end else if (C_PC_WIDTH == 8) begin : gen_r_same
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = s_T;
        C_BUS_R_PC:
          s_R_pre = s_PC_return;
        default:
          s_R_pre = s_T;
      endcase
  end else begin : gen_r_wide
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = { {(C_PC_WIDTH-8){1'b0}}, s_T };
        C_BUS_R_PC:
          s_R_pre = s_PC_return;
        default:
          s_R_pre = { {(C_PC_WIDTH-8){1'b0}}, s_T };
      endcase
  end
endgenerate

/*******************************************************************************
 *
 * run the state machines for the processor components.
 *
 ******************************************************************************/

/*
 * Operate the program counter.
 */

initial s_PC = {(C_PC_WIDTH){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s_PC <= {(C_PC_WIDTH){1'b0}};
  else
    s_PC <= s_PC_next;

/*
 * Operate the return stack.
 */

//@SSBCC@ memory_return_stack
// TODO -- replace this temporary implementation of the return stack
localparam C_RETURN_PTR_WIDTH   =  5;
reg [C_RETURN_WIDTH-1:0] s_R_stack[2**C_RETURN_PTR_WIDTH-1:0];
localparam C_SMALL_RETURN_STACK_IMPLEMENTATION = 1;

generate
if (C_SMALL_RETURN_STACK_IMPLEMENTATION) begin : gen_small_return_stack

  //
  // Low resource utilization, slow return stack implementation
  //

  reg [C_RETURN_PTR_WIDTH-1:0] s_R_ptr_next;

  // reference return stack pointer;
  reg [C_RETURN_PTR_WIDTH-1:0] s_R_ptr = {(C_RETURN_PTR_WIDTH){1'b1}};
  always @ (posedge i_clk)
    if (i_rst)
      s_R_ptr <= {(C_RETURN_PTR_WIDTH){1'b1}};
    else
      s_R_ptr <= s_R_ptr_next;

  // pointer to top of return stack and next return stack;
  reg                          s_R_memWr    = 1'b0;
  initial                      s_R_ptr_next = {(C_RETURN_PTR_WIDTH){1'b0}};
  reg [C_RETURN_PTR_WIDTH-1:0] s_R_ptr_top  = {(C_RETURN_PTR_WIDTH){1'b0}};
  always @ (*)
    case (s_return)
      C_RETURN_NOP: begin
                    s_R_memWr    <= 1'b0;
                    s_R_ptr_next <= s_R_ptr;
                    s_R_ptr_top  <= s_R_ptr;
                    end
      C_RETURN_INC: begin
                    s_R_memWr    <= 1'b1;
                    s_R_ptr_next <= s_R_ptr + { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
                    s_R_ptr_top  <= s_R_ptr + { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
                    end
      C_RETURN_DEC: begin
                    s_R_memWr    <= 1'b0;
                    s_R_ptr_next <= s_R_ptr - { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
                    s_R_ptr_top  <= s_R_ptr;
                    end
           default: begin
                    s_R_memWr    <= 1'b0;
                    s_R_ptr_next <= s_R_ptr;
                    s_R_ptr_top  <= s_R_ptr;
                    end
    endcase

  always @ (posedge i_clk)
    if (s_R_memWr)
      s_R_stack[s_R_ptr_top] <= s_R_pre;

  initial s_R = {(C_RETURN_WIDTH){1'b0}};
  always @ (*)
    s_R <= s_R_stack[s_R_ptr_top];

end else begin : gen_fast_return_stack
  // TODO -- debug this section

  //
  // High resource utilization, fast return stack implementation
  //

  initial                         s_R             = {(C_RETURN_WIDTH){1'b0}};
  reg        [C_RETURN_WIDTH-1:0] s_R_next        = {(C_RETURN_WIDTH){1'b0}};
  reg                             s_R_hasValue    = 1'b0;
  reg    [C_RETURN_PTR_WIDTH-1:0] s_R_ptr         = {(C_RETURN_PTR_WIDTH){1'b0}};
  reg    [C_RETURN_PTR_WIDTH-1:0] s_R_ptr_next    = {(C_RETURN_PTR_WIDTH){1'b0}};

  always @ (posedge i_clk)
    if (i_rst) begin
      s_R          <= {(C_RETURN_WIDTH){1'b0}};
      s_R_hasValue <= 1'b0;
    end else case (s_return)
      C_RETURN_NOP:
        begin
        s_R          <= s_R;
        s_R_hasValue <= s_R_hasValue;
        end
      C_RETURN_INC:
        begin
        s_R          <= s_R_pre;
        s_R_hasValue <= 1'b1;
        end
      C_RETURN_DEC:
        begin
        s_R          <= s_R_next;
        s_R_hasValue <= |s_R_ptr;
        end
      default:
        begin
        s_R          <= s_R;
        s_R_hasValue <= s_R_hasValue;
        end
    endcase

  reg s_R_memWr = 1'b0;
  always @ (*)
    if (!s_R_hasValue) begin
      s_R_ptr_next = {(C_RETURN_PTR_WIDTH){1'b0}};
      s_R_memWr = 1'b0;
    end else begin
      s_R_memWr = 1'b0;
      case (s_return)
        C_RETURN_NOP:
          s_R_ptr_next = s_R_ptr;
        C_RETURN_INC:
          begin
            s_R_memWr = 1'b1;
            if (s_R_hasValue)
              s_R_ptr_next = s_R_ptr + { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
            else
              s_R_ptr_next = s_R_ptr;
          end
        C_RETURN_DEC:
          if (|s_R_ptr)
            s_R_ptr_next = s_R_ptr - { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
          else
            s_R_ptr_next = s_R_ptr;
        default:
          s_R_ptr_next = s_R_ptr;
      endcase
    end

  always @ (posedge i_clk)
    s_R_ptr <= s_R_ptr_next;

  always @ (posedge i_clk) begin
    if (s_R_memWr) begin
      s_R_stack[s_R_ptr] <= s_R;
      s_R_next <= s_R;
    end else
      s_R_next <= s_R_stack[s_R_ptr];
  end
end
endgenerate

/*
 * Operate the top of the data stack.
 */

initial s_T = 8'h00;
always @ (posedge i_clk)
  if (i_rst)
    s_T <= 8'h00;
  else case (s_bus_t)
    C_BUS_T_MATH_ROTATE:        s_T <= s_math_rotate;
    C_BUS_T_OPCODE:             s_T <= s_opcode[0+:8];  // push 8-bit value
    C_BUS_T_N:                  s_T <= s_N;
    C_BUS_T_PRE:                s_T <= s_T_pre;
    C_BUS_T_MATH_DUAL:          s_T <= s_math_dual;
    C_BUS_T_COMPARE:            s_T <= s_T_compare;
    C_BUS_T_INPORT:             s_T <= 8'h00; // TODO -- change
    C_BUS_T_MEMORY:             s_T <= 8'h00; // TODO -- change
    default:                    s_T <= s_T;
  endcase

/*
 * Operate the next-to-top of the data stack.
 */

//@SSBCC@ memory_data_stack
// TODO -- replace this temporary implementation of the data stack
localparam C_DATA_PTR_WIDTH = 6;
reg [7:0] s_N_stack[2**C_DATA_PTR_WIDTH-1:0];
localparam C_SMALL_DATA_STACK_IMPLEMENTATION = 1;

generate
if (C_SMALL_DATA_STACK_IMPLEMENTATION) begin : gen_small_data_stack

  //
  // Low resource utilization, slow data stack implementation
  //

  reg [C_DATA_PTR_WIDTH-1:0] s_N_stack_ptr_next;

  // reference data stack pointer
  reg [C_DATA_PTR_WIDTH-1:0] s_N_stack_ptr = { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
  always @ (posedge i_clk)
    if (i_rst)
      s_N_stack_ptr <= { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
    else
      s_N_stack_ptr <= s_N_stack_ptr_next;

  // pointer to top of data stack and next data stack
  reg                        s_N_memWr          = 1'b0;
  initial                    s_N_stack_ptr_next = { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
  reg [C_DATA_PTR_WIDTH-1:0] s_N_stack_ptr_top  = { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
  always @ (*)
    case (s_stack)
      C_STACK_NOP: begin
                   s_N_memWr <= 1'b0;
                   s_N_stack_ptr_next <= s_N_stack_ptr;
                   s_N_stack_ptr_top  <= s_N_stack_ptr;
                   end
      C_STACK_INC: begin
                   s_N_memWr <= 1'b1;
                   s_N_stack_ptr_next <= s_N_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                   s_N_stack_ptr_top  <= s_N_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                   end
      C_STACK_DEC: begin
                   s_N_memWr <= 1'b0;
                   s_N_stack_ptr_next <= s_N_stack_ptr - { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                   s_N_stack_ptr_top  <= s_N_stack_ptr;
                   end
          default: begin
                   s_N_memWr <= 1'b0;
                   s_N_stack_ptr_next <= s_N_stack_ptr;
                   s_N_stack_ptr_top  <= s_N_stack_ptr;
                   end
    endcase

  always @ (posedge i_clk)
    if (s_N_memWr)
      s_N_stack[s_N_stack_ptr_top] <= s_T;

  initial s_N = 8'h00;
  always @ (*)
    s_N <= s_N_stack[s_N_stack_ptr_top];

end else begin : gen_fast_data_stack

  initial s_N = 8'h00;
  always @ (posedge i_clk)
    if (i_rst)
      s_N <= 8'h00;
    else case (s_bus_n)
      C_BUS_N_N:          s_N <= s_N;
      C_BUS_N_T:          s_N <= s_T;
      C_BUS_N_STACK:      s_N <= s_N; // fix this
      default:            s_N <= s_N;
    endcase

end
endgenerate


/*******************************************************************************
 *
 * Instantiate the output signals.
 *
 * Note:  This includes output strobes associated with input ports.
 *
 ******************************************************************************/

//@SSBCC@ outports
// TODO -- replace this temporary hard-wired "o_led" port
initial o_led = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    o_led <= 1'b0;
  else if (s_outport)
    o_led <= s_N[0];
  else
    o_led <= o_led;

/*******************************************************************************
 *
 * Instantiate the memories.
 *
 ******************************************************************************/

//@SSBCC@ memories
// TODO -- replace this temporary access of the program space.
initial s_opcode = 9'h000;
always @ (posedge i_clk)
  if (i_rst)
    s_opcode <= 9'h000;
  else
    s_opcode <= s_opcodeMemory[s_PC];

endmodule
