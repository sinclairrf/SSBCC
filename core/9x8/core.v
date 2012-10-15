/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * SSBCC.9x8 -- Small Stack Based Computer Compiler, 9-bit opcode, 8-bit data.
 *
 ******************************************************************************/

//@SSBCC@ user_header

//@SSBCC@ module

// configuration file determined parameters
//@SSBCC@ localparam

/*******************************************************************************
 *
 * Declare the signals used throughout the system.
 *
 ******************************************************************************/

// listed in useful dispay order
reg            [C_PC_WIDTH-1:0] s_PC;           // program counter
reg                       [8:0] s_opcode;       // current opcode
reg    [C_RETURN_PTR_WIDTH-1:0] s_Rp_ptr;       // read return stack pointer
reg        [C_RETURN_WIDTH-1:0] s_R;            // top of return stack
reg                       [7:0] s_T;            // top of the data stack
reg                       [7:0] s_N;            // next-to-top on the data stack

//@SSBCC@ verilator_tracing

//@SSBCC@ functions

//@SSBCC@ signals

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
     3'b011 : s_math_rotate = { s_T[0+:7], s_T[7] };    // <<msb
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

//  opcode = 000011_x00 (adder) and 001xxx_x.. (incrementers)
reg [7:0] s_T_adder;
always @ (*)
  if (s_opcode[6] == 1'b0)
    case (s_opcode[2])
       1'b0: s_T_adder = s_N + s_T;
       1'b1: s_T_adder = s_N - s_T;
    endcase
  else
    case (s_opcode[2])
       1'b0: s_T_adder = s_T + 8'h01;
       1'b1: s_T_adder = s_T - 8'h01;
    default: s_T_adder = s_T + 8'h01;
    endcase

// opcode = 000100_0xx
//                   ^ 0 ==> "=", 1 ==> "<>"
//                  ^  0 ==> all zero, 1 ==> all ones
wire s_T_compare = s_opcode[0] ^ &(s_T == {(8){s_opcode[1]}});

// opcode = 001010_xxx
// add,sub,and,or,xor,TBD,drop,nip
reg [7:0] s_T_logic;
always @ (*)
  case (s_opcode[0+:3])
     3'b000 : s_T_logic = s_N & s_T;    // and
     3'b001 : s_T_logic = s_N | s_T;    // or
     3'b010 : s_T_logic = s_N ^ s_T;    // xor
     3'b011 : s_T_logic = s_T;          // nip
     3'b100 : s_T_logic = s_N;          // drop
     3'b101 : s_T_logic = s_N;          // drop
     3'b110 : s_T_logic = s_N;          // drop
     3'b111 : s_T_logic = s_N;          // drop
    default : s_T_logic = s_N;          // drop
  endcase

// increment PC
reg [C_PC_WIDTH-1:0] s_PC_plus1 = {(C_PC_WIDTH){1'b0}};
always @ (*)
  s_PC_plus1 = s_PC + { {(C_PC_WIDTH-1){1'b0}}, 1'b1 };

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

reg [7:0] s_T_inport = 8'h00;
//@SSBCC@ inports

/*******************************************************************************
 *
 * Instantiate the memory banks.
 *
 ******************************************************************************/

reg s_mem_wr = 1'b0;

//@SSBCC@ memory

/*******************************************************************************
 *
 * Define the states for the bus muxes and then compute these states from the
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

localparam C_BUS_T_MATH_ROTATE  = 4'b0000;      // nop and rotate operations
localparam C_BUS_T_OPCODE       = 4'b0001;
localparam C_BUS_T_N            = 4'b0010;
localparam C_BUS_T_PRE          = 4'b0011;
localparam C_BUS_T_ADDER        = 4'b0100;
localparam C_BUS_T_COMPARE      = 4'b0101;
localparam C_BUS_T_INPORT       = 4'b0110;
localparam C_BUS_T_LOGIC        = 4'b0111;
localparam C_BUS_T_MEM          = 4'b1010;
reg [3:0] s_bus_t;

localparam C_BUS_N_N            = 2'b00;       // don't change N
localparam C_BUS_N_STACK        = 2'b01;       // replace N with third-on-stack
localparam C_BUS_N_T            = 2'b10;       // replace N with T
localparam C_BUS_N_MEM          = 2'b11;       // from memory
reg [1:0] s_bus_n;

localparam C_STACK_NOP          = 2'b00;        // don't change internal data stack pointer
localparam C_STACK_INC          = 2'b01;        // add element to internal data stack
localparam C_STACK_DEC          = 2'b10;        // remove element from internal data stack
reg [1:0] s_stack;

reg s_inport                    = 1'b0;
reg s_outport                   = 1'b0;

always @ (*) begin
  // default operation is nop/math_rotate
  s_bus_pc      = C_BUS_PC_NORMAL;
  s_bus_r       = C_BUS_R_T;
  s_return      = C_RETURN_NOP;
  s_bus_t       = C_BUS_T_MATH_ROTATE;
  s_bus_n       = C_BUS_N_N;
  s_stack       = C_STACK_NOP;
  s_inport      = 1'b0;
  s_outport     = 1'b0;
  s_mem_wr      = 1'b0;
  if (s_opcode[8] == 1'b1) begin // push
    s_bus_t     = C_BUS_T_OPCODE;
    s_bus_n     = C_BUS_N_T;
    s_stack     = C_STACK_INC;
  end else if (s_opcode[7] == 1'b1) begin // jump, jumpc, call, callc
    if (!s_opcode[5] || (|s_N)) begin // always or conditional
      s_bus_pc  = C_BUS_PC_JUMP;
      if (s_opcode[6])                  // call or callc
        s_return = C_RETURN_INC;
    end
    s_bus_r     = C_BUS_R_PC;
    s_bus_t     = C_BUS_T_N;
    s_bus_n     = C_BUS_N_STACK;
    s_stack     = C_STACK_DEC;
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
      4'b0011:  begin // dual-operand adder:  add,sub
                s_bus_t         = C_BUS_T_ADDER;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b0100:  begin // 0=, -1=, 0<>, -1<>
                s_bus_t         = C_BUS_T_COMPARE;
                end
      4'b0101:  begin // return
                s_bus_pc        = C_BUS_PC_RETURN;
                s_return        = C_RETURN_DEC;
                end
      4'b0110:  begin // inport
                s_bus_t         = C_BUS_T_INPORT;
                s_inport        = 1'b1;
                end
      4'b0111:  begin // outport
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                s_outport       = 1'b1;
                end
      4'b1000:  begin // >r
                s_return        = C_RETURN_INC;
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b1001:  begin // r> (pop the return stack and push it onto the data stack)
                s_return        = C_RETURN_DEC;
                s_bus_t         = C_BUS_T_PRE;
                s_bus_n         = C_BUS_N_T;
                s_stack         = C_STACK_INC;
                end
      4'b1010:  begin // &, or, ^, nip, and drop
                s_bus_t         = C_BUS_T_LOGIC;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                end
      4'b1011:  begin // 8-bit increment/decrement
                s_bus_t         = C_BUS_T_ADDER;
                end
      4'b1100:  begin // store
                s_bus_t         = C_BUS_T_N;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                s_mem_wr        = 1'b1;
                end
      4'b1101:  begin // fetch
                s_bus_t       = C_BUS_T_MEM;
                end
      4'b1110:  begin // store+/store-
                s_bus_t         = C_BUS_T_ADDER;
                s_bus_n         = C_BUS_N_STACK;
                s_stack         = C_STACK_DEC;
                s_mem_wr        = 1'b1;
                end
      4'b1111:  begin // fetch+/fetch-
                  s_bus_t       = C_BUS_T_ADDER;
                  s_bus_n       = C_BUS_N_MEM;
                  s_stack       = C_STACK_INC;
                end
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

// Return stack candidate
reg [C_RETURN_WIDTH-1:0] s_R_pre;
generate
  if (C_PC_WIDTH < 8) begin : gen_r_narrow
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = s_T;
        C_BUS_R_PC:
          s_R_pre = { {(8-C_PC_WIDTH){1'b0}}, s_PC_plus1 };
        default:
          s_R_pre = s_T;
      endcase
  end else if (C_PC_WIDTH == 8) begin : gen_r_same
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = s_T;
        C_BUS_R_PC:
          s_R_pre = s_PC_plus1;
        default:
          s_R_pre = s_T;
      endcase
  end else begin : gen_r_wide
    always @ (*)
      case (s_bus_r)
        C_BUS_R_T:
          s_R_pre = { {(C_PC_WIDTH-8){1'b0}}, s_T };
        C_BUS_R_PC:
          s_R_pre = s_PC_plus1;
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

// Declare the return stack.
reg [C_RETURN_WIDTH-1:0] s_R_stack[2**C_RETURN_PTR_WIDTH-1:0];

//
// Low resource utilization, slow return stack implementation
//

// pointer to top of return stack and next return stack;
reg     s_R_memRd    = 1'b0;
reg     s_R_memWr    = 1'b0;
always @ (*)
  case (s_return)
    C_RETURN_NOP: begin
                  s_R_memRd    = 1'b0;
                  s_R_memWr    = 1'b0;
                  end
    C_RETURN_INC: begin
                  s_R_memRd    = 1'b0;
                  s_R_memWr    = 1'b1;
                  end
    C_RETURN_DEC: begin
                  s_R_memRd    = 1'b1;
                  s_R_memWr    = 1'b0;
                  end
         default: begin
                  s_R_memRd    = 1'b0;
                  s_R_memWr    = 1'b0;
                  end
  endcase

reg [C_RETURN_PTR_WIDTH-1:0] s_Rw_ptr = {(C_RETURN_PTR_WIDTH){1'b1}};
always @ (posedge i_clk)
  if (i_rst)
    s_Rw_ptr <= {(C_RETURN_PTR_WIDTH){1'b1}};
  else case (s_return)
    C_RETURN_NOP: s_Rw_ptr <= s_Rw_ptr;
    C_RETURN_INC: s_Rw_ptr <= s_Rw_ptr + { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
    C_RETURN_DEC: s_Rw_ptr <= s_Rw_ptr - { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
         default: s_Rw_ptr <= s_Rw_ptr;
  endcase

always @ (posedge i_clk)
  if (s_R_memWr)
    s_R_stack[s_Rw_ptr] <= s_R;

initial s_Rp_ptr = { {(C_RETURN_PTR_WIDTH-1){1'b1}}, 1'b0 };
always @ (posedge i_clk)
  if (i_rst)
    s_Rp_ptr <= { {(C_RETURN_PTR_WIDTH-1){1'b1}}, 1'b0 };
  else case (s_return)
    C_RETURN_NOP: s_Rp_ptr <= s_Rp_ptr;
    C_RETURN_INC: s_Rp_ptr <= s_Rp_ptr + { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
    C_RETURN_DEC: s_Rp_ptr <= s_Rp_ptr - { {(C_RETURN_PTR_WIDTH-1){1'b0}}, 1'b1 };
         default: s_Rp_ptr <= s_Rp_ptr;
  endcase

initial s_R = {(C_RETURN_WIDTH){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s_R <= {(C_RETURN_WIDTH){1'b0}};
  else if (s_R_memWr)
    s_R <= s_R_pre;
  else if (s_R_memRd)
    s_R <= s_R_stack[s_Rp_ptr];
  else
    s_R <= s_R;

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
    C_BUS_T_ADDER:              s_T <= s_T_adder;
    C_BUS_T_COMPARE:            s_T <= {(8){s_T_compare}};
    C_BUS_T_INPORT:             s_T <= s_T_inport;
    C_BUS_T_LOGIC:              s_T <= s_T_logic;
    C_BUS_T_MEM:                s_T <= s_memory;
    default:                    s_T <= s_T;
  endcase

/*
 * Operate the next-to-top of the data stack.
 */

// TODO -- replace this temporary implementation of the data stack
reg [7:0] s_data_stack[2**C_DATA_PTR_WIDTH-1:0];

// reference data stack pointer
reg [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr = { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 };
always @ (posedge i_clk)
  if (i_rst)
    s_Np_stack_ptr <= { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 };
  else case (s_stack)
    C_STACK_INC: s_Np_stack_ptr <= s_Np_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
    C_STACK_DEC: s_Np_stack_ptr <= s_Np_stack_ptr - { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
        default: s_Np_stack_ptr <= s_Np_stack_ptr;
  endcase


// pointer to top of data stack and next data stack
reg [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr_top = { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 };
always @ (*)
  case (s_stack)
    C_STACK_INC: s_Np_stack_ptr_top = s_Np_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
        default: s_Np_stack_ptr_top = s_Np_stack_ptr;
  endcase

always @ (posedge i_clk)
  if (s_stack == C_STACK_INC)
    s_data_stack[s_Np_stack_ptr_top] <= s_N;

initial s_N = 8'h00;
always @ (posedge i_clk)
  if (i_rst)
    s_N <= 8'h00;
  else case (s_bus_n)
    C_BUS_N_N:          s_N <= s_N;
    C_BUS_N_STACK:      s_N <= s_data_stack[s_Np_stack_ptr_top];
    C_BUS_N_T:          s_N <= s_T;
    C_BUS_N_MEM:        s_N <= s_memory;
    default:            s_N <= s_N;
  endcase

/*******************************************************************************
 *
 * Instantiate the output signals.
 *
 ******************************************************************************/

//@SSBCC@ outports

/*******************************************************************************
 *
 * Instantiate the instruction memory and the PC access of that memory.
 *
 ******************************************************************************/

//@SSBCC@ instructions

//@SSBCC@ peripherals

endmodule
