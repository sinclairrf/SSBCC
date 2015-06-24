// Copyright 2013-2015, Sinclair R.F., Inc.
// short, human-readable versions of s_opcode suitable for waveform viewers
reg [3*8-1:0] s_opcode_name = "nop";
always @ (posedge i_clk)
  if (s_interrupt)
    s_opcode_name = "int"; // interrupt cycle
  else if (s_interrupted)
    s_opcode_name = "npi"; // nop induced by interrupt
  else casez (s_opcode)
    9'b00_0000_000 : s_opcode_name = "nop";
    9'b00_0000_001 : s_opcode_name = "<<0";
    9'b00_0000_010 : s_opcode_name = "<<1";
    9'b00_0000_011 : s_opcode_name = "<<m";
    9'b00_0000_100 : s_opcode_name = "0>>";
    9'b00_0000_101 : s_opcode_name = "1>>";
    9'b00_0000_110 : s_opcode_name = "m>>";
    9'b00_0000_111 : s_opcode_name = "l>>";
    9'b00_0001_000 : s_opcode_name = "dup";
    9'b00_0001_001 : s_opcode_name = "r@ ";
    9'b00_0001_010 : s_opcode_name = "ovr";
    9'b00_0001_011 : s_opcode_name = "+c ";
    9'b00_0001_111 : s_opcode_name = "-c ";
    9'b00_0010_010 : s_opcode_name = "swp";
    9'b00_0011_000 : s_opcode_name = "+  ";
    9'b00_0011_100 : s_opcode_name = "-  ";
    9'b00_0100_000 : s_opcode_name = "0= ";
    9'b00_0100_001 : s_opcode_name = "0<>";
    9'b00_0100_010 : s_opcode_name = "-1=";
    9'b00_0100_011 : s_opcode_name = "-1#";
    9'b00_0101_000 : s_opcode_name = "rtn";
    9'b00_0110_000 : s_opcode_name = "inp";
    9'b00_0111_000 : s_opcode_name = "out";
    9'b00_1000_000 : s_opcode_name = ">r ";
    9'b00_1001_001 : s_opcode_name = "r> ";
    9'b00_1010_000 : s_opcode_name = "&  ";
    9'b00_1010_001 : s_opcode_name = "or ";
    9'b00_1010_010 : s_opcode_name = "^  ";
    9'b00_1010_011 : s_opcode_name = "nip";
    9'b00_1010_100 : s_opcode_name = "drp";
    9'b00_1011_000 : s_opcode_name = "1+ ";
    9'b00_1011_100 : s_opcode_name = "1- ";
    9'b00_1100_000 : s_opcode_name = "s0 ";
    9'b00_1100_001 : s_opcode_name = "s1 ";
    9'b00_1100_010 : s_opcode_name = "s2 ";
    9'b00_1100_011 : s_opcode_name = "s3 ";
    9'b00_1101_000 : s_opcode_name = "@0 ";
    9'b00_1101_001 : s_opcode_name = "@1 ";
    9'b00_1101_010 : s_opcode_name = "@2 ";
    9'b00_1101_011 : s_opcode_name = "@3 ";
    9'b00_1110_000 : s_opcode_name = "s0+";
    9'b00_1110_001 : s_opcode_name = "s1+";
    9'b00_1110_010 : s_opcode_name = "s2+";
    9'b00_1110_011 : s_opcode_name = "s3+";
    9'b00_1110_100 : s_opcode_name = "s0-";
    9'b00_1110_101 : s_opcode_name = "s1-";
    9'b00_1110_110 : s_opcode_name = "s2-";
    9'b00_1110_111 : s_opcode_name = "s3-";
    9'b00_1111_000 : s_opcode_name = "@0+";
    9'b00_1111_001 : s_opcode_name = "@1+";
    9'b00_1111_010 : s_opcode_name = "@2+";
    9'b00_1111_011 : s_opcode_name = "@3+";
    9'b00_1111_100 : s_opcode_name = "@0-";
    9'b00_1111_101 : s_opcode_name = "@1-";
    9'b00_1111_110 : s_opcode_name = "@2-";
    9'b00_1111_111 : s_opcode_name = "@3-";
    9'b0_100_????? : s_opcode_name = "jp ";
    9'b0_110_????? : s_opcode_name = "cl ";
    9'b0_101_????? : s_opcode_name = "jpc";
    9'b0_111_????? : s_opcode_name = "clc";
    9'b1_????_???? : s_opcode_name = "psh";
           default : s_opcode_name = "INV";
  endcase
