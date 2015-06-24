//
// PERIPHERAL interrupt
// Copyright 2015, Sinclair R.F., Inc.
//
reg s_in_jump = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s_in_jump <= 1'b0;
  else
    s_in_jump <= (s_bus_pc == C_BUS_PC_JUMP) || (s_bus_pc == C_BUS_PC_RETURN);
wire @WIDTH@ s_interrupt_raw = ( @INVERT@ ^ @INSIGNAL@ ) & @MASK@;
reg @WIDTH@ s_interrupt_raw_s = @INVERT@;
always @ (posedge i_clk)
  if (i_rst)
    s_interrupt_raw_s <= @INVERT@;
  else
    s_interrupt_raw_s <= s_interrupt_raw;
wire @WIDTH@ s_interrupt_trigger_raw = s_interrupt_raw & ~s_interrupt_raw_s;
reg s_interrupt_trigger_any = 1'b0;
always @ (posedge i_clk)
  if (i_rst) begin
    s_interrupt_trigger <= @ZERO@;
    s_interrupt_trigger_any <= 1'b0;
  end else if (@CLEAR_TRIGGER@) begin
    s_interrupt_trigger <= s_interrupt_trigger_raw;
    s_interrupt_trigger_any <= |s_interrupt_trigger_raw;
  end else begin
    s_interrupt_trigger <= s_interrupt_trigger | s_interrupt_trigger_raw;
    s_interrupt_trigger_any <= s_interrupt_trigger_any || (|s_interrupt_trigger_raw);
  end
reg s_interrupt_ena;
always @ (*)
  s_interrupt = s_interrupt_ena && s_interrupt_trigger_any && ~s_in_jump;
always @ (posedge i_clk)
  if (i_rst)
    s_interrupted <= 1'b0;
  else
    s_interrupted <= s_interrupt;
initial s_interrupt_ena = 1'b0;
always @ (posedge i_clk)
  if (i_rst)
    s_interrupt_ena <= 1'b0;
  else if (s_interrupt)
    s_interrupt_ena <= 1'b0;
  else if (s_outport && (s_T == @IX_OUTPORT_ENA@))
    s_interrupt_ena <= 1'b1;
  else if (s_outport && (s_T == @IX_OUTPORT_DIS@))
    s_interrupt_ena <= 1'b0;
  else
    s_interrupt_ena <= s_interrupt_ena;
