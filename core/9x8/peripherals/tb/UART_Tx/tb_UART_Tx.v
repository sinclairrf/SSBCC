/*******************************************************************************
 *
 * Copyright 2012, Sinclair R.F., Inc.
 *
 * SSBCC.9x8 -- Small Stack Based Computer Compiler, 9-bit opcode, 8-bit data.
 *
 ******************************************************************************/


module tb_UART_Tx(
  // synchronous reset and processor clock
  input  wire           i_rst,
  input  wire           i_clk,
  output reg            o_uart1_tx,
  output reg            o_uart2_tx,
  output reg            o_uart3_tx,
  output reg            o_done
);

parameter G_CLK_FREQ_HZ = 100_000_000;
parameter G_BAUD = 230400;

// configuration file determined parameters
localparam C_PC_WIDTH                              =    6;
localparam C_RETURN_PTR_WIDTH                      =    4;
localparam C_DATA_PTR_WIDTH                        =    5;

// computed parameters
localparam C_RETURN_WIDTH = (C_PC_WIDTH <= 8) ? 8 : C_PC_WIDTH;

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
reg      [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr_top;
                                                // read data stack pointer

/* verilator tracing_off */

reg  [7:0] s__o_uart1_tx__Tx    = 8'd0;
reg        s__o_uart1_tx__busy  = 1'd0;
reg        s__o_uart1_tx__wr    = 1'd0;
reg  [7:0] s__o_uart2_tx__Tx    = 8'd0;
reg        s__o_uart2_tx__busy  = 1'd0;
reg        s__o_uart2_tx__wr    = 1'd0;
reg  [7:0] s__o_uart3_tx__Tx    = 8'd0;
reg        s__o_uart3_tx__busy  = 1'd0;
reg        s__o_uart3_tx__wr    = 1'd0;

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
always @ (*)
  case (s_T)
      8'h00 : s_T_inport = { 7'h0, s__o_uart1_tx__busy };
      8'h01 : s_T_inport = { 7'h0, s__o_uart2_tx__busy };
      8'h02 : s_T_inport = { 7'h0, s__o_uart3_tx__busy };
    default : s_T_inport = 8'h00;
  endcase


/*******************************************************************************
 *
 * Instantiate the memory banks.
 *
 ******************************************************************************/

reg s_mem_wr = 1'b0;

wire [7:0] s_memory = 8'h00;

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

reg [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr_next;

// reference data stack pointer
reg [C_DATA_PTR_WIDTH-1:0] s_Np_stack_ptr = { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
always @ (posedge i_clk)
  if (i_rst)
    s_Np_stack_ptr <= { {(C_DATA_PTR_WIDTH-1){1'b1}}, 1'b0 };
  else
    s_Np_stack_ptr <= s_Np_stack_ptr_next;

// pointer to top of data stack and next data stack
initial                    s_Np_stack_ptr_next = { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 };
initial                    s_Np_stack_ptr_top  = { {(C_DATA_PTR_WIDTH-2){1'b1}}, 2'b01 };
always @ (*)
  case (s_stack)
    C_STACK_NOP: begin
                 s_Np_stack_ptr_next = s_Np_stack_ptr;
                 s_Np_stack_ptr_top  = s_Np_stack_ptr;
                 end
    C_STACK_INC: begin
                 s_Np_stack_ptr_next = s_Np_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                 s_Np_stack_ptr_top  = s_Np_stack_ptr + { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                 end
    C_STACK_DEC: begin
                 s_Np_stack_ptr_next = s_Np_stack_ptr - { {(C_DATA_PTR_WIDTH-1){1'b0}}, 1'b1 };
                 s_Np_stack_ptr_top  = s_Np_stack_ptr;
                 end
        default: begin
                 s_Np_stack_ptr_next = s_Np_stack_ptr;
                 s_Np_stack_ptr_top  = s_Np_stack_ptr;
                 end
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

initial s__o_uart1_tx__Tx = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__Tx <= 8'd0;
  else if (s_outport && (s_T == 8'h00))
    s__o_uart1_tx__Tx <= s_N[0+:8];
  else
    s__o_uart1_tx__Tx <= s__o_uart1_tx__Tx;

initial s__o_uart1_tx__wr = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__wr <= 1'b0;
  else if (s_outport)
    s__o_uart1_tx__wr <= (s_T == 8'h00);
  else
    s__o_uart1_tx__wr <= 1'b0;

initial s__o_uart2_tx__Tx = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__Tx <= 8'd0;
  else if (s_outport && (s_T == 8'h01))
    s__o_uart2_tx__Tx <= s_N[0+:8];
  else
    s__o_uart2_tx__Tx <= s__o_uart2_tx__Tx;

initial s__o_uart2_tx__wr = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__wr <= 1'b0;
  else if (s_outport)
    s__o_uart2_tx__wr <= (s_T == 8'h01);
  else
    s__o_uart2_tx__wr <= 1'b0;

initial s__o_uart3_tx__Tx = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart3_tx__Tx <= 8'd0;
  else if (s_outport && (s_T == 8'h02))
    s__o_uart3_tx__Tx <= s_N[0+:8];
  else
    s__o_uart3_tx__Tx <= s__o_uart3_tx__Tx;

initial s__o_uart3_tx__wr = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart3_tx__wr <= 1'b0;
  else if (s_outport)
    s__o_uart3_tx__wr <= (s_T == 8'h02);
  else
    s__o_uart3_tx__wr <= 1'b0;

initial o_done = 1'd0;
always @ (posedge i_clk)
  if (i_rst)
    o_done <= 1'd0;
  else if (s_outport && (s_T == 8'h03))
    o_done <= s_N[0+:1];
  else
    o_done <= o_done;


/*******************************************************************************
 *
 * Instantiate the instruction memory and the PC access of that memory.
 *
 ******************************************************************************/

reg [8:0] s_opcodeMemory[63:0];
initial begin
  // .main
  s_opcodeMemory['h00] = 9'h12F; // 
  s_opcodeMemory['h01] = 9'h0C0; // call load_message
  s_opcodeMemory['h02] = 9'h000; // nop
  s_opcodeMemory['h03] = 9'h100; // :loop1 O_UART1_TX
  s_opcodeMemory['h04] = 9'h038; // outport
  s_opcodeMemory['h05] = 9'h054; // drop
  s_opcodeMemory['h06] = 9'h103; // 
  s_opcodeMemory['h07] = 9'h0A0; // jumpc loop1
  s_opcodeMemory['h08] = 9'h000; // nop
  s_opcodeMemory['h09] = 9'h054; // drop
  s_opcodeMemory['h0A] = 9'h12F; // 
  s_opcodeMemory['h0B] = 9'h0C0; // call load_message
  s_opcodeMemory['h0C] = 9'h000; // nop
  s_opcodeMemory['h0D] = 9'h101; // :loop2 O_UART2_TX
  s_opcodeMemory['h0E] = 9'h038; // outport
  s_opcodeMemory['h0F] = 9'h054; // drop
  s_opcodeMemory['h10] = 9'h10D; // 
  s_opcodeMemory['h11] = 9'h0A0; // jumpc loop2
  s_opcodeMemory['h12] = 9'h000; // nop
  s_opcodeMemory['h13] = 9'h054; // drop
  s_opcodeMemory['h14] = 9'h12F; // 
  s_opcodeMemory['h15] = 9'h0C0; // call load_message
  s_opcodeMemory['h16] = 9'h000; // nop
  s_opcodeMemory['h17] = 9'h102; // :loop3 O_UART3_TX
  s_opcodeMemory['h18] = 9'h038; // outport
  s_opcodeMemory['h19] = 9'h054; // drop
  s_opcodeMemory['h1A] = 9'h102; // :wait3 I_UART3_TX
  s_opcodeMemory['h1B] = 9'h030; // inport
  s_opcodeMemory['h1C] = 9'h11A; // 
  s_opcodeMemory['h1D] = 9'h0A0; // jumpc wait3
  s_opcodeMemory['h1E] = 9'h054; // drop
  s_opcodeMemory['h1F] = 9'h117; // 
  s_opcodeMemory['h20] = 9'h0A0; // jumpc loop3
  s_opcodeMemory['h21] = 9'h000; // nop
  s_opcodeMemory['h22] = 9'h054; // drop
  s_opcodeMemory['h23] = 9'h102; // :wait I_UART3_TX
  s_opcodeMemory['h24] = 9'h030; // inport
  s_opcodeMemory['h25] = 9'h123; // 
  s_opcodeMemory['h26] = 9'h0A0; // jumpc wait
  s_opcodeMemory['h27] = 9'h054; // drop
  s_opcodeMemory['h28] = 9'h101; // 0x01
  s_opcodeMemory['h29] = 9'h103; // O_DONE
  s_opcodeMemory['h2A] = 9'h038; // outport
  s_opcodeMemory['h2B] = 9'h054; // drop
  s_opcodeMemory['h2C] = 9'h12C; // :infinite 
  s_opcodeMemory['h2D] = 9'h080; // jump infinite
  s_opcodeMemory['h2E] = 9'h000; // nop
  // load_message
  s_opcodeMemory['h2F] = 9'h100; // 0x00
  s_opcodeMemory['h30] = 9'h121; // 21 '!'
  s_opcodeMemory['h31] = 9'h164; // 64 'd'
  s_opcodeMemory['h32] = 9'h16C; // 6C 'l'
  s_opcodeMemory['h33] = 9'h172; // 72 'r'
  s_opcodeMemory['h34] = 9'h16F; // 6F 'o'
  s_opcodeMemory['h35] = 9'h157; // 57 'W'
  s_opcodeMemory['h36] = 9'h120; // 0x20
  s_opcodeMemory['h37] = 9'h16F; // 6F 'o'
  s_opcodeMemory['h38] = 9'h16C; // 6C 'l'
  s_opcodeMemory['h39] = 9'h16C; // 6C 'l'
  s_opcodeMemory['h3A] = 9'h165; // 65 'e'
  s_opcodeMemory['h3B] = 9'h028; // return
  s_opcodeMemory['h3C] = 9'h148; // 48 'H'
  s_opcodeMemory['h3D] = 9'h000;
  s_opcodeMemory['h3E] = 9'h000;
  s_opcodeMemory['h3F] = 9'h000;
end

initial s_opcode = 9'h000;
always @ (posedge i_clk)
  if (i_rst)
    s_opcode <= 9'h000;
  else
    s_opcode <= s_opcodeMemory[s_PC];

//
// Peripherals
//

//
// PERIPHERAL UART_Tx:  o_uart1_tx
//
generate
reg s__o_uart1_tx__uart_busy;
// FIFO=32
localparam L__o_uart1_tx__FIFO_LENGTH = 32;
localparam L__o_uart1_tx__FIFO_NBITS = $clog2(L__o_uart1_tx__FIFO_LENGTH);
reg [7:0] s__o_uart1_tx__fifo_mem[32-1:0];
reg [L__o_uart1_tx__FIFO_NBITS:0] s__o_uart1_tx__fifo_addr_in = {(L__o_uart1_tx__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__fifo_addr_in <= {(L__o_uart1_tx__FIFO_NBITS+1){1'b0}};
  else if (s__o_uart1_tx__wr) begin
    s__o_uart1_tx__fifo_addr_in <= s__o_uart1_tx__fifo_addr_in + { {(L__o_uart1_tx__FIFO_NBITS){1'b0}}, 1'b1 };
    s__o_uart1_tx__fifo_mem[s__o_uart1_tx__fifo_addr_in[0+:L__o_uart1_tx__FIFO_NBITS]] <= s__o_uart1_tx__Tx;
  end
reg [L__o_uart1_tx__FIFO_NBITS:0] s__o_uart1_tx__fifo_addr_out;
reg s__o_uart1_tx__fifo_has_data = 1'b0;
reg s__o_uart1_tx__fifo_full = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__o_uart1_tx__fifo_has_data <= 1'b0;
    s__o_uart1_tx__fifo_full <= 1'b0;
  end else begin
    s__o_uart1_tx__fifo_has_data <= (s__o_uart1_tx__fifo_addr_out != s__o_uart1_tx__fifo_addr_in);
    s__o_uart1_tx__fifo_full <= (s__o_uart1_tx__fifo_addr_out == (s__o_uart1_tx__fifo_addr_in ^ { 1'b1, {(L__o_uart1_tx__FIFO_NBITS){1'b0}} }));
  end
initial s__o_uart1_tx__fifo_addr_out = {(L__o_uart1_tx__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__fifo_addr_out <= {(L__o_uart1_tx__FIFO_NBITS+1){1'b0}};
  else if (s__o_uart1_tx__go)
    s__o_uart1_tx__fifo_addr_out <= s__o_uart1_tx__fifo_addr_out + { {(L__o_uart1_tx__FIFO_NBITS){1'b0}}, 1'b1 };
reg s__o_uart1_tx__go = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__go <= 1'b0;
  else if (s__o_uart1_tx__fifo_has_data && !s__o_uart1_tx__uart_busy && !s__o_uart1_tx__go)
    s__o_uart1_tx__go <= 1'b1;
  else
    s__o_uart1_tx__go <= 1'b0;
reg [7:0] s__o_uart1_tx__Tx_data = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__Tx_data <= 8'd0;
  else
    s__o_uart1_tx__Tx_data <= s__o_uart1_tx__fifo_mem[s__o_uart1_tx__fifo_addr_out[0+:L__o_uart1_tx__FIFO_NBITS]];
// Count the clock cycles to decimate to the desired baud rate.
localparam L__o_uart1_tx__COUNT       = 868-1;
localparam L__o_uart1_tx__COUNT_NBITS = $clog2(L__o_uart1_tx__COUNT);
reg [L__o_uart1_tx__COUNT_NBITS-1:0] s__o_uart1_tx__count = {(L__o_uart1_tx__COUNT_NBITS){1'b0}};
reg s__o_uart1_tx__count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__o_uart1_tx__count <= {(L__o_uart1_tx__COUNT_NBITS){1'b0}};
    s__o_uart1_tx__count_is_zero <= 1'b0;
  end else if (s__o_uart1_tx__go || s__o_uart1_tx__count_is_zero) begin
    s__o_uart1_tx__count <= L__o_uart1_tx__COUNT[0+:L__o_uart1_tx__COUNT_NBITS];
    s__o_uart1_tx__count_is_zero <= 1'b0;
  end else begin
    s__o_uart1_tx__count <= s__o_uart1_tx__count - { {(L__o_uart1_tx__COUNT_NBITS-1){1'b0}}, 1'b1 };
    s__o_uart1_tx__count_is_zero <= (s__o_uart1_tx__count == { {(L__o_uart1_tx__COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s__o_uart1_tx__out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__out_stream <= 8'hFF;
  else if (s__o_uart1_tx__go)
    s__o_uart1_tx__out_stream <= s__o_uart1_tx__Tx_data;
  else if (s__o_uart1_tx__count_is_zero)
    s__o_uart1_tx__out_stream <= { 1'b1, s__o_uart1_tx__out_stream[1+:7] };
  else
    s__o_uart1_tx__out_stream <= s__o_uart1_tx__out_stream;
// Generate the output bit stream.
initial o_uart1_tx = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    o_uart1_tx <= 1'b1;
  else if (s__o_uart1_tx__go)
    o_uart1_tx <= 1'b0;
  else if (s__o_uart1_tx__count_is_zero)
    o_uart1_tx <= s__o_uart1_tx__out_stream[0];
  else
    o_uart1_tx <= o_uart1_tx;
// Count down the number of bits.
localparam L__o_uart1_tx__NTX       = 1+8+1-1;
localparam L__o_uart1_tx__NTX_NBITS = $clog2(L__o_uart1_tx__NTX);
reg [L__o_uart1_tx__NTX_NBITS-1:0] s__o_uart1_tx__ntx = {(L__o_uart1_tx__NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__ntx <= {(L__o_uart1_tx__NTX_NBITS){1'b0}};
  else if (s__o_uart1_tx__go)
    s__o_uart1_tx__ntx <= L__o_uart1_tx__NTX[0+:L__o_uart1_tx__NTX_NBITS];
  else if (s__o_uart1_tx__count_is_zero)
    s__o_uart1_tx__ntx <= s__o_uart1_tx__ntx - { {(L__o_uart1_tx__NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s__o_uart1_tx__ntx <= s__o_uart1_tx__ntx;
// The status bit is 1 if the core is busy and 0 otherwise.
initial s__o_uart1_tx__uart_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart1_tx__uart_busy <= 1'b0;
  else if (s__o_uart1_tx__go)
    s__o_uart1_tx__uart_busy <= 1'b1;
  else if (s__o_uart1_tx__count_is_zero && (s__o_uart1_tx__ntx == {(L__o_uart1_tx__NTX_NBITS){1'b0}}))
    s__o_uart1_tx__uart_busy <= 1'b0;
  else
    s__o_uart1_tx__uart_busy <= s__o_uart1_tx__uart_busy;
always @ (*) s__o_uart1_tx__busy = s__o_uart1_tx__fifo_full;
endgenerate

//
// PERIPHERAL UART_Tx:  o_uart2_tx
//
generate
reg s__o_uart2_tx__uart_busy;
// FIFO=32
localparam L__o_uart2_tx__FIFO_LENGTH = 32;
localparam L__o_uart2_tx__FIFO_NBITS = $clog2(L__o_uart2_tx__FIFO_LENGTH);
reg [7:0] s__o_uart2_tx__fifo_mem[32-1:0];
reg [L__o_uart2_tx__FIFO_NBITS:0] s__o_uart2_tx__fifo_addr_in = {(L__o_uart2_tx__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__fifo_addr_in <= {(L__o_uart2_tx__FIFO_NBITS+1){1'b0}};
  else if (s__o_uart2_tx__wr) begin
    s__o_uart2_tx__fifo_addr_in <= s__o_uart2_tx__fifo_addr_in + { {(L__o_uart2_tx__FIFO_NBITS){1'b0}}, 1'b1 };
    s__o_uart2_tx__fifo_mem[s__o_uart2_tx__fifo_addr_in[0+:L__o_uart2_tx__FIFO_NBITS]] <= s__o_uart2_tx__Tx;
  end
reg [L__o_uart2_tx__FIFO_NBITS:0] s__o_uart2_tx__fifo_addr_out;
reg s__o_uart2_tx__fifo_has_data = 1'b0;
reg s__o_uart2_tx__fifo_full = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__o_uart2_tx__fifo_has_data <= 1'b0;
    s__o_uart2_tx__fifo_full <= 1'b0;
  end else begin
    s__o_uart2_tx__fifo_has_data <= (s__o_uart2_tx__fifo_addr_out != s__o_uart2_tx__fifo_addr_in);
    s__o_uart2_tx__fifo_full <= (s__o_uart2_tx__fifo_addr_out == (s__o_uart2_tx__fifo_addr_in ^ { 1'b1, {(L__o_uart2_tx__FIFO_NBITS){1'b0}} }));
  end
initial s__o_uart2_tx__fifo_addr_out = {(L__o_uart2_tx__FIFO_NBITS+1){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__fifo_addr_out <= {(L__o_uart2_tx__FIFO_NBITS+1){1'b0}};
  else if (s__o_uart2_tx__go)
    s__o_uart2_tx__fifo_addr_out <= s__o_uart2_tx__fifo_addr_out + { {(L__o_uart2_tx__FIFO_NBITS){1'b0}}, 1'b1 };
reg s__o_uart2_tx__go = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__go <= 1'b0;
  else if (s__o_uart2_tx__fifo_has_data && !s__o_uart2_tx__uart_busy && !s__o_uart2_tx__go)
    s__o_uart2_tx__go <= 1'b1;
  else
    s__o_uart2_tx__go <= 1'b0;
reg [7:0] s__o_uart2_tx__Tx_data = 8'd0;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__Tx_data <= 8'd0;
  else
    s__o_uart2_tx__Tx_data <= s__o_uart2_tx__fifo_mem[s__o_uart2_tx__fifo_addr_out[0+:L__o_uart2_tx__FIFO_NBITS]];
// Count the clock cycles to decimate to the desired baud rate.
localparam L__o_uart2_tx__COUNT       = (G_CLK_FREQ_HZ+115200/2)/115200-1;
localparam L__o_uart2_tx__COUNT_NBITS = $clog2(L__o_uart2_tx__COUNT);
reg [L__o_uart2_tx__COUNT_NBITS-1:0] s__o_uart2_tx__count = {(L__o_uart2_tx__COUNT_NBITS){1'b0}};
reg s__o_uart2_tx__count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__o_uart2_tx__count <= {(L__o_uart2_tx__COUNT_NBITS){1'b0}};
    s__o_uart2_tx__count_is_zero <= 1'b0;
  end else if (s__o_uart2_tx__go || s__o_uart2_tx__count_is_zero) begin
    s__o_uart2_tx__count <= L__o_uart2_tx__COUNT[0+:L__o_uart2_tx__COUNT_NBITS];
    s__o_uart2_tx__count_is_zero <= 1'b0;
  end else begin
    s__o_uart2_tx__count <= s__o_uart2_tx__count - { {(L__o_uart2_tx__COUNT_NBITS-1){1'b0}}, 1'b1 };
    s__o_uart2_tx__count_is_zero <= (s__o_uart2_tx__count == { {(L__o_uart2_tx__COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s__o_uart2_tx__out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__out_stream <= 8'hFF;
  else if (s__o_uart2_tx__go)
    s__o_uart2_tx__out_stream <= s__o_uart2_tx__Tx_data;
  else if (s__o_uart2_tx__count_is_zero)
    s__o_uart2_tx__out_stream <= { 1'b1, s__o_uart2_tx__out_stream[1+:7] };
  else
    s__o_uart2_tx__out_stream <= s__o_uart2_tx__out_stream;
// Generate the output bit stream.
initial o_uart2_tx = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    o_uart2_tx <= 1'b1;
  else if (s__o_uart2_tx__go)
    o_uart2_tx <= 1'b0;
  else if (s__o_uart2_tx__count_is_zero)
    o_uart2_tx <= s__o_uart2_tx__out_stream[0];
  else
    o_uart2_tx <= o_uart2_tx;
// Count down the number of bits.
localparam L__o_uart2_tx__NTX       = 1+8+1-1;
localparam L__o_uart2_tx__NTX_NBITS = $clog2(L__o_uart2_tx__NTX);
reg [L__o_uart2_tx__NTX_NBITS-1:0] s__o_uart2_tx__ntx = {(L__o_uart2_tx__NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__ntx <= {(L__o_uart2_tx__NTX_NBITS){1'b0}};
  else if (s__o_uart2_tx__go)
    s__o_uart2_tx__ntx <= L__o_uart2_tx__NTX[0+:L__o_uart2_tx__NTX_NBITS];
  else if (s__o_uart2_tx__count_is_zero)
    s__o_uart2_tx__ntx <= s__o_uart2_tx__ntx - { {(L__o_uart2_tx__NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s__o_uart2_tx__ntx <= s__o_uart2_tx__ntx;
// The status bit is 1 if the core is busy and 0 otherwise.
initial s__o_uart2_tx__uart_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart2_tx__uart_busy <= 1'b0;
  else if (s__o_uart2_tx__go)
    s__o_uart2_tx__uart_busy <= 1'b1;
  else if (s__o_uart2_tx__count_is_zero && (s__o_uart2_tx__ntx == {(L__o_uart2_tx__NTX_NBITS){1'b0}}))
    s__o_uart2_tx__uart_busy <= 1'b0;
  else
    s__o_uart2_tx__uart_busy <= s__o_uart2_tx__uart_busy;
always @ (*) s__o_uart2_tx__busy = s__o_uart2_tx__fifo_full;
endgenerate

//
// PERIPHERAL UART_Tx:  o_uart3_tx
//
generate
reg s__o_uart3_tx__uart_busy;
// noFIFO
wire s__o_uart3_tx__go = s__o_uart3_tx__wr;
wire [7:0] s__o_uart3_tx__Tx_data = s__o_uart3_tx__Tx;
// Count the clock cycles to decimate to the desired baud rate.
localparam L__o_uart3_tx__COUNT       = (100000000+G_BAUD/2)/G_BAUD-1;
localparam L__o_uart3_tx__COUNT_NBITS = $clog2(L__o_uart3_tx__COUNT);
reg [L__o_uart3_tx__COUNT_NBITS-1:0] s__o_uart3_tx__count = {(L__o_uart3_tx__COUNT_NBITS){1'b0}};
reg s__o_uart3_tx__count_is_zero = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s__o_uart3_tx__count <= {(L__o_uart3_tx__COUNT_NBITS){1'b0}};
    s__o_uart3_tx__count_is_zero <= 1'b0;
  end else if (s__o_uart3_tx__go || s__o_uart3_tx__count_is_zero) begin
    s__o_uart3_tx__count <= L__o_uart3_tx__COUNT[0+:L__o_uart3_tx__COUNT_NBITS];
    s__o_uart3_tx__count_is_zero <= 1'b0;
  end else begin
    s__o_uart3_tx__count <= s__o_uart3_tx__count - { {(L__o_uart3_tx__COUNT_NBITS-1){1'b0}}, 1'b1 };
    s__o_uart3_tx__count_is_zero <= (s__o_uart3_tx__count == { {(L__o_uart3_tx__COUNT_NBITS-1){1'b0}}, 1'b1 });
  end
// Latch the bits to output.
reg [7:0] s__o_uart3_tx__out_stream = 8'hFF;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart3_tx__out_stream <= 8'hFF;
  else if (s__o_uart3_tx__go)
    s__o_uart3_tx__out_stream <= s__o_uart3_tx__Tx_data;
  else if (s__o_uart3_tx__count_is_zero)
    s__o_uart3_tx__out_stream <= { 1'b1, s__o_uart3_tx__out_stream[1+:7] };
  else
    s__o_uart3_tx__out_stream <= s__o_uart3_tx__out_stream;
// Generate the output bit stream.
initial o_uart3_tx = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    o_uart3_tx <= 1'b1;
  else if (s__o_uart3_tx__go)
    o_uart3_tx <= 1'b0;
  else if (s__o_uart3_tx__count_is_zero)
    o_uart3_tx <= s__o_uart3_tx__out_stream[0];
  else
    o_uart3_tx <= o_uart3_tx;
// Count down the number of bits.
localparam L__o_uart3_tx__NTX       = 1+8+2-1;
localparam L__o_uart3_tx__NTX_NBITS = $clog2(L__o_uart3_tx__NTX);
reg [L__o_uart3_tx__NTX_NBITS-1:0] s__o_uart3_tx__ntx = {(L__o_uart3_tx__NTX_NBITS){1'b0}};
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart3_tx__ntx <= {(L__o_uart3_tx__NTX_NBITS){1'b0}};
  else if (s__o_uart3_tx__go)
    s__o_uart3_tx__ntx <= L__o_uart3_tx__NTX[0+:L__o_uart3_tx__NTX_NBITS];
  else if (s__o_uart3_tx__count_is_zero)
    s__o_uart3_tx__ntx <= s__o_uart3_tx__ntx - { {(L__o_uart3_tx__NTX_NBITS-1){1'b0}}, 1'b1 };
  else
    s__o_uart3_tx__ntx <= s__o_uart3_tx__ntx;
// The status bit is 1 if the core is busy and 0 otherwise.
initial s__o_uart3_tx__uart_busy = 1'b1;
always @ (posedge i_clk)
  if (i_rst)
    s__o_uart3_tx__uart_busy <= 1'b0;
  else if (s__o_uart3_tx__go)
    s__o_uart3_tx__uart_busy <= 1'b1;
  else if (s__o_uart3_tx__count_is_zero && (s__o_uart3_tx__ntx == {(L__o_uart3_tx__NTX_NBITS){1'b0}}))
    s__o_uart3_tx__uart_busy <= 1'b0;
  else
    s__o_uart3_tx__uart_busy <= s__o_uart3_tx__uart_busy;
always @ (*) s__o_uart3_tx__busy = s__o_uart3_tx__uart_busy;
endgenerate

endmodule
