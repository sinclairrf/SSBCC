; Copyright 2015, Sinclair R.F., Inc.
; demonstrate dual interrupt peripheral

.memory ROM myrom
.variable msg N"INT\n"

.memory RAM myram
.variable ixMsg 0

.main
  ; Mask all but the external interrupt and then enable interrupts.
  C_INTERRUPT .outport(O_INTERRUPT_MASK)
  .ena

  ; Sit in an infinite loop while the interrupt handler does everything else.
  :infinite .jump(infinite)

.interrupt
  ; Get the interrupt event(s).
  ; ( - u_int )
  .inport(I_INTERRUPT)

  ; Test for the external interrupt.
  ; ( u_int - u_int )
  dup C_INTERRUPT & 0= .jumpc(not_external)
    ; Set the index into the output message.
    msg .storevalue(ixMsg)
    ; Enable the UART_Tx interrupt.
    .inport(I_INTERRUPT_MASK) C_UART_TX_INTERRUPT or .outport(O_INTERRUPT_MASK)
  :not_external

  ; Test for the UART_Tx not_busy interrupt.
  ; ( u_int - u_int )
  dup C_UART_TX_INTERRUPT & 0= .jumpc(not_uart)
    ; Get the next character to transmit and move the pointer to the next
    ; character.
    ; ( - u_char )
    .fetchvalue(ixMsg) .fetch+(myrom) .storevalue(ixMsg)
    ; If the character is a terminating null character then discard it and
    ; disable this part of the interrupt, otherwise output it.
    .jumpc(not_null,nop)
      ; ( u_char - )
      drop
      .inport(I_INTERRUPT_MASK) ${~C_UART_TX_INTERRUPT} & .outport(O_INTERRUPT_MASK)
      .jump(not_uart)
    :not_null
      ; ( u_char - )
      .outport(O_UART_TX)
  :not_uart

  ; Drop the interrupt event from the data stack and return from the interrupt.
  ; ( u_int - )
  drop .returni
