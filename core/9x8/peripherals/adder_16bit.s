;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Copyright 2012-2013, Sinclair R.F., Inc.
; Copyright 2019, Rodney Sinclair
;
; adder_16bit.s
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.IFNDEF D_ADDER_16BIT_S_INCLUDED
.define D_ADDER_16BIT_S_INCLUDED

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; Perform and addition or subtraction of two 16-bit values.
; ( u_1_LSB u_1_MSB u_2_LSB u_2_MSB u_op - u_op_LSB u_op_MSB )
;
; where
;   u_op = u_1 + u_2 if u_op==0
;        = u_1 - u_2 otherwise
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.function addsub_u16_u16__u16

  ; Set the operation.
  ; ( u_1_LSB u_1_MSB u_2_LSB u_2_MSB u_op - u_1_LSB u_1_MSB u_2_LSB u_2_MSB )
  .outport(O_ADDER_16BIT_OP)

  ; Load the 16-bit value u_2.
  ; ( u_1_LSB u_1_MSB u_2_LSB u_2_MSB - u_1_LSB u_1_MSB )
  .outport(O_ADDER_16BIT_MSB2) .outport(O_ADDER_16BIT_LSB2)

  ; Load the 16-bit value u_1.
  ; ( u_1_LSB u_1_MSB - )
  .outport(O_ADDER_16BIT_MSB1) .outport(O_ADDER_16BIT_LSB1)

  ; Read the result and return.
  ; ( - u_op_LSB u_op_MSB )
  .inport(I_ADDER_16BIT_LSB) I_ADDER_16BIT_MSB .return(inport)

.ENDIF
