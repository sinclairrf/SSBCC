/*******************************************************************************
 *
 * The processor core is implemented such that at most two layers of 6-input
 * LUTs are involved in the computations between successive clock cycles.  For
 * example, if an addition operation is performed then
 *   1. Do the unlatched addition and identify how the registers will be
 *      affected.  Here, the input to the T latch will be the adder output, the
 *      input to N will be the top of the data stack, the data stack pointer
 *      will be decremented, the return stack pointer will not be afffected, and
 *      the program counter will proceed normally.
 *   2. Do the latched operations on the registers.  Here, T will be latched as
 *      the adder output, N will be latched as the old top of the data stack,
 *      etc.
 *
 ******************************************************************************/

reg       [7:0] T                       = 8'h00;

wire            conditional_true        = |T;

wire is_jump            = !opcode_curr[8] && opcode_curr[7];
wire do_jump            = is_jump && (!opcode_curr[6] || conditional_true);

wire R_pop              =

wire T_push             = opcode_curr[8] ||
wire T_pop              = do_jump ||
always @ (posedge i_clk)
  if (i_rst) begin
    T <= 8'h00;
  end else if (T_push) begin
    if (opcode_curr[8])
      T <= opcode_curr[7:0];
    else
      T <=
  end else if (T_pop) begin
    T <= N;
  end else begin
    T <= T;
  end

/*******************************************************************************
 *
 * First stage operations.
 *
 ******************************************************************************/

// adder/subtracter
wire [7:0] math_dual_adder;
always @ (T,N,opcode_curr)
  case (opcode_curr[0])
       1'b0 : math_dual_adder <= N + T; // add
       1'b1 : math_dual_adder <= N - T; // sub
    default : math_dual_adder <= T;
  endcase

// logic operations
// 4-input LUT formulation -- 2-bit opcode, 1 bit each of T and N
wire [7:0] math_dual_logic;
always @ (T,N,opcode_curr)
  case (opcode_curr[0+:2])
      2'b00 : math_dual_logic <= T & N; // and
      2'b01 : math_dual_logic <= T | N; // or
      2'b10 : math_dual_logic <= T ^ N; // xor
      2'b11 : math_dual_logic <= T;     // nip
    default : math_dual_logic <= T;
  endcase

// shifter operations (including "nop" as no shift)
// 6-input LUT formulation -- 3-bit opcode, 3 bits of T centered at current bit
wire [7:0] math_rotate;
always @ (T,opcode_curr)
  case (opcode_curr[0+:3])
     3'b000 : math_rotate <= T;                 // nop
     3'b001 : math_rotate <= { T[0+:7], 1'b0 }; // <<0
     3'b010 : math_rotate <= { T[0+:7], 1'b1 }; // <<1
     3'b011 : math_rotate <= { T[0+:7], T[0] }; // <<lsb
     3'b100 : math_rotate <= { 1'b0, T[1+:7] }; // 0>>
     3'b101 : math_rotate <= { 1'b1, T[1+:7] }; // 1>>
     3'b110 : math_rotate <= { T[7], T[1+:7] }; // msb>>
     3'b111 : math_rotate <= { T[0], T[1+:7] }; // lsb>>
    default : math_rotate <= T;
  endcase

// T pre-multiplexer for pushing repeated values onto the data stack
wire [7:0] s_T_pre;
always @ (*)
  case (opcode_curr[0+:2])
      2'b00 : s_T_pre <= s_T;                   // dup
      2'b01 : s_T_pre <= s_R[0+:8];             // r@
      2'b10 : s_T_pre <= s_N;                   // over
      2'b11 : s_T_pre <=
    default : s_T_pre <= s_T;
  endcase

/*******************************************************************************
 *
 * Define the states for the bus muxes and then compute these stated from the
 * current opcode.
 *
 ******************************************************************************/

localparam C_BUS_PC_NORMAL      = 2'b00;
localparam C_BUS_PC_JUMP        = 2'b01;
localparam C_BUS_PC_RETURN      = 2'b11;

localparam C_BUS_R_NOP          = 2'b00;
localparam C_BUS_R_PC           = 2'b01;
localparam C_BUS_R_T            = 2'b10;

localparam C_BUS_T_PRE_OPCODE   = 3'b000;
localparam C_BUS_T_PRE_RETURN   = 3'b001;
localparam C_BUS_T_PRE_MEMORY   = 3'b010;
localparam C_BUS_T_PRE_N        = 3'b011;
localparam C_BUS_T_PRE_T        = 3'b100;
localparam C_BUS_T_PRE_INPORT   = 3'b101;

localparam C_BUS_T_NOP          = 2'b00;
localparam C_BUS_T_PRE          = 2'b01;
localparam C_BUS_T_MATH_DUAL    = 2'b10;
localparam C_BUS_T_MATH_ROTATE  = 2'b11;

localparam C_BUS_N_NOP          = 2'b00;
localparam C_BUS_N_T            = 2'b01;
localparam C_BUS_N_STACK        = 2'b10;

localparam C_STACK_NOP          = 2'b00;
localparam C_STACK_INC          = 2'b01;
localparam C_STACK_DEC          = 2'b10;

always @ (opcode_curr,T) begin
  s_bus_pc      <= C_BUS_PC_NORMAL;
  s_bus_r       <= C_BUS_R_NOP;
  s_bus_t_pre   <= C_BUS_T_PRE_RETURN;
  s_bus_t       <= C_BUS_T_NOP;
  s_bus_n       <= C_BUS_N_NOP;
  s_return      <= C_RETURN_NOP;
  s_stack       <= C_STACK_NOP;
  s_interrupt_enabled_change    <= 1'b1;
  s_interrupt_enabled_next      <= s_interrupt_enabled;
  s_interrupt_holdoff           <= 1'b0;
  s_outport_next                <= 1'b0;
  if (opcode_curr[8] == 1'b1) begin // push
    s_bus_t_pre <= C_BUS_T_PRE_OPCODE;
    s_bus_t     <= C_BUS_T_PRE;
    s_bus_n     <= C_BUS_N_T;
    s_stack     <= C_STACK_INC;
  end else if (opcode_curr[7] = 1'b1) begin // jump or jumpc
    if (opcode_curr[6] = 1'b0 || (|s_T))
    s_bus_t_pre <= C_BUS_T_PRE_N;
    s_bus_t     <= C_BUS_T_PRE;
    s_bus_n     <= C_BUS_N_STACK;
    s_stack     <= C_STACK_DEC;
    s_interrupt_holdoff <= 1'b1;
  end else case (opcode_curr[3+:4])
      4'b0000:  // nop, math_rotate
                s_bus_t         <= C_BUS_T_MATH_ROTATE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_NOP;
      4'b0001:  // dup, r@, over
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_T;
                s_stack         <= C_STACK_INC;
      4'b0010:  // swap
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_T;
      4'b0011:  // dual-operand math:  add/sub
                s_bus_t         <= C_BUS_T_MATH_ADDER;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b0100:  // dual-operand math:  and/or/xor/nip
                s_bus_t         <= C_BUS_T_MATH_LOGIC;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b0101:  // return
                s_bus_pc        <= C_BUS_PC_RETURN;
                s_return        <= C_RETURN_DEC;
      4'b0110:  // inport
                s_bus_t         <= C_BUS_T_INPORT;
      4'b0111:  // outport
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b1000:  // call
                s_bus_pc        <= C_BUS_PC_JUMP;
                s_return        <= C_RETURN_INC;
                s_bus_r         <= C_BUS_R_PC;
      4'b1001:  // callc
                s_bus_pc        <= C_BUS_PC_JUMP;
                s_return        <= C_RETURN_INC;
                s_bus_r         <= C_BUS_R_PC;
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b1010:  // drop
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b1011:  // >r
                s_return        <= C_RETURN_INC;
                s_bus_r         <= C_BUS_R_T;
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      4'b1100:  // r> (pop the return stack and push it onto the data stack)
                s_return        <= C_RETURN_DEC;
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_T;
                s_stack         <= C_STACK_INC;
      4'b1101:  // enable/disable the interrupt
                s_interrupt_enabled_change <= 1'b1;
                s_interrupt_enabled_next <= opcode_curr[0];
      4'b1110:  // @ (fetch)
                s_bus_t         <= C_BUS_T_MEMORY;
      4'b1111:  // ! (store)
                s_bus_t         <= C_BUS_T_PRE;
                s_bus_n         <= C_BUS_N_STACK;
                s_stack         <= C_STACK_DEC;
      default:  // nop
    endcase
  end
end

/*******************************************************************************
 *
 * run the state machines for the processor components.
 *
 ******************************************************************************/

/*
 * Operate the program counter.
 */

// reduced-warning message method to extract the jump address from the top of
// the stack and the current opcode
wire s_PC_jump[C_PC_WIDTH-1:0];
generate
  if (C_PC_WIDTH <= 8) begin : gen_pc_narrow
    s_PC_jump <= s_T[0+:C_PC_WIDTH];
  end else begin : gen_pc_wide
    s_PC_jump <= { opcode_curr[0+:C_PC_WIDTH-8], s_T };
endgenerate

always @ (posedge i_clk)
  if (i_rst)
    s_PC <= C_RESET;
  else case (s_bus_pc)
    case C_BUS_PC_NORMAL: s_PC <= s_PC + 1;
    case C_BUS_PC_JUMP:   s_PC <= s_PC_jump;
    case C_BUS_PC_RETURN: s_PC <= s_R;
    default:              s_PC <= s_PC_next;
  endcase

wire [1:0] s_bus_t_pre
always @ (posedge s_registers_opcode)
  case (s_registers_opcode)
    4'b0000:            s_bus_t_pre <= C_BUS_T_PRE_RETURN;      // nop
    4'b0001:
    4'b0010:            s_bus_t_pre <= C_BUS_T_PRE_RETURN;      // add/sub
    4'b0011:            s_bus_t_pre <= C_BUS_T_PRE_RETURN;      // math_opcode
    default:            s_bus_t_pre <= C_BUS_T_PRE_RETURN;
  endcase;

always @ (opcode_curr[7+:2], s_registers_opcode) begin
  bus__adder_out <= 1'b0;
  bus__math_out  <= 1'b0;
  bus__latch_T   <= 1'b0;
  bus__pop_T     <= 1'b0;
  bus__push_T    <= 1'b0;
  bus__pop_N     <= 1'b0;
  bus__push_N    <= 1'b0;
  bus__pop_R     <= 1'b0;
  bus__push_R    <= 1'b0;
  if (opcode_curr[7+:2] == 2'b00)
    case (s_registers_opcode)
      4'b0000: ;                                // nop
      4'b0001: ?
      4'b0010: bus__adder_out     <= 1'b1;      // add/sub
               bus__latch_T       <= 1'b1;
               bus__pop_N         <= 1'b1;
      4'b0011: bus__math_out      <= 1'b1;      // math_opcode
               bus__latch_T       <= 1'b1;
               bus__pop_N         <= 1'b1;
      default:
    endcase
end

wire N_gets_top         = opcode_curr[8];
wire N_gets_third       = opcode_curr[7] || 
wire N_same
