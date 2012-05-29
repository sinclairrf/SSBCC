################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Transmit side of a UART:
#   1 start bit
#   8 data bits
#   n stop bits
#
# Usage:
#   PERIPHERAL UART_Tx [name],[noFIFO|FIFO=n],[nStop=n],baudmethod=[clk/rate,count]
# Where:
#   name
#     is the base name for the outport symbol within the assembly code
#     default:  UART
#   noFIFO
#     the peripheral will not have a FIFO
#     this is the default
#   FIFO=n
#     adds a FIFO of depth n
#   nStop=n
#     configures the peripheral for n stop bits
#     default:  1 stop bit
#     Note:  n must be at least 1
#   baudmethod
#     specifies the method to generate the desired bit rate:
#     1st method:  clk/rate
#       clk is the frequency of "i_clk" in Hz
#         a number will be interpreted as the clock frequency in Hz
#         a symbol will be interpreted as a parameter
#           Note:  this parameter must have been declared with a "PARAMETER"
#           command
#       rate is the desired baud rate
#         this is specified as per "clk"
#     2nd method:
#       specify the number of "i_clk" clock cycles between bit edges
#
# The following INPORTs are provided by the peripheral:
#   I_name_STATUS
#     bit 0:  busy status
#       this bit will be high when the core cannot accept more data
#       Note:  If there is no FIFO this means that the core is still
#         transmitting the last byte.  If there is a FIFO it means that the FIFO
#         cannot accept any more data.
#
# The following OUTPORTs are provided by the peripheral:
#   O_name_TX
#     this is the next 8-bit value to transmit or to queue for transmission
#
################################################################################
