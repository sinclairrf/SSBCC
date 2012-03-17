# Copyright 2012, Sinclair R.F., Inc.
#
# Assembler for SSBCC 9x8 processor

################################################################################
#
# Stage 1:  Parse the files.
#
# Read the entire file, doing the following while reading the file:
# @ Store the raw content of each line or group of lines for output to the
#   assembled memory initialization.
# @ A line belongs to a group if (1) its first non-blank character is a ';' or
#   (2) it is a continuation line.  A continuation line is defined as a line
#   with the continuation character '\' followed by 0 or more blanks or tabs and
#   then either the end of the line or the comment character ';'.  Any other use
#   of the continuation character outside of a character or string is an error
#   and immediately terminates the parser.
# @ Convert each of these lines or group of lines into an array of the raw
#   tokens.
# @ For each array of tokens that begins with one of the macro directives
#     .constant
#     .function
#     .include
#     .interrupt (variant of ".function" macro)
#     .macro
#     .main
#     .memory
#     .variable
#   update the assembler dictionaries as required and put the assembler in the
#   appropriate state.  A malformed macro array is an error and immediately
#   terminates the parser.  Add a report of the macro to the group of lines.  No
#   more processing is done for a macro array.
# @ Accumulate the arrays of tokens comprising the body of a ".function" or
#   ".main" body.
# @ At the end of a ".function" or ".main" body, do the following:
#   @ Issue an error if a ".function" body does not end in a ".jump" or
#     ".return".  Issue an error if a ".main" body does not end in a ".jump".
#   @ Perform full substitution for all user-defined macros.
#   @ Perform full substitution for ".fetch", ".fetchindexed", ".store", and
#     ".storeindexed" pre-defined macros.
#   @ Perform preliminary substitution for ".call" and ".callc" pre-defeined
#     macros and add the call index to the ".function" definition (to identify
#     which functions are actually required by the program).
#   @ Make a list of jump targets within the ".function" or ".main" body.
#   @ Perform preliminary substitution for ".jump" and ".jumpc" pre-defined
#     macros.  Issue an error if the jump target is not defined within the body.
#   - At this point the space required for the function or main program should
#     be fully defined.
#   @ Compute the offset of each jump target within the ".function" or ".main"
#     body.
#
################################################################################

################################################################################
#
# Stage 2:  Perform the following consistency checks.
#
# @ Ensure a ".main" body was defined.
# @ If interrupts are enabled for the processor, ensure a single ".interrupt"
#   function was defined.
# @ If interrupts are not enabled and an ".interrupt" was defined, then issue a
#   warning message.
# @ Ensure all required ".function"s are defined.
#
################################################################################

################################################################################
#
# Stage 3:  Compute addresses.
#
# Compute the addresses for the ".main" and required ".function" bodies as
# follows:
# @ Set the function address to 0.
# @ If interrupts are enabled, then add 3 to the function address.
# @ Set the start address of the main program to the current function address,
#   compute the addresses of all jump targets within the ".main" body, and then
#   add the length of the ".main" body to the function address.
# @ Loop through the ".function" list in the order in which the functions were
#   defined and do the following:
#   @ If the function was not used, then disabled its body.
#   @ Otherwise, set the start address of the ".function" to the current
#     function address, compute the addresses of all jump targets within the
#     ".function" body, and add then length of the ".function" body to the
#     function address.
# @ If then total program length exceedes the allowable program length, then
#   issue an error.
# @ Loop through the ".main" body and ".function" bodies, setting the addresses
#   for all the ".call" and ".callc" macros.
#
################################################################################

################################################################################
#
# Stage 4:  Emit the program
#
# Do the following:
# @ If interrupts are enabled, then set the first 3 instructions to be a ".jump"
#   instruction to the ".interrupt" function.
# @ Write the instructions for the ".main" body.
# @ Loop through the ".function" list in the order in which they were defined
#   and write their instructions.
# @ Print the memory and instruction usage statistics.
#
################################################################################
