# Copyright 2019, Rodney Sinclair
#
# Populate gtkwave

gtkwave::/Edit/Insert_Comment   "AXI Bus"
gtkwave::addSignalsFromList     {
                                tb.uut.axi_lite_aclk
                                tb.uut.axi_lite_aresetn
                                tb.uut.axi_lite_awaddr
                                tb.uut.axi_lite_wdata
                                tb.uut.axi_lite_wstrb
                                tb.uut.axi_lite_awready
                                tb.uut.axi_lite_awvalid
                                tb.uut.axi_lite_wready
                                tb.uut.axi_lite_wvalid
                                tb.uut.axi_lite_bready
                                tb.uut.axi_lite_bvalid
                                tb.uut.axi_lite_bresp
                                tb.uut.axi_lite_araddr
                                tb.uut.axi_lite_arready
                                tb.uut.axi_lite_arvalid
                                tb.uut.axi_lite_rready
                                tb.uut.axi_lite_rvalid
                                tb.uut.axi_lite_rresp
                                tb.uut.axi_lite_rdata
                                }

gtkwave::/Edit/Insert_Comment   "uc"
gtkwave::addSignalsFromList     "tb.uut.i_rst"
gtkwave::addSignalsFromList     "tb.uut.i_clk"
gtkwave::addSignalsFromList     "tb.uut.s_PC"
gtkwave::/Edit/Time_Warp/Warp_Marked +16nsec
gtkwave::addSignalsFromList     "tb.uut.s_opcode"
gtkwave::/Edit/Time_Warp/Warp_Marked +8nsec
gtkwave::addSignalsFromList     "tb.uut.s_opcode_name"
gtkwave::/Edit/Data_Format/ASCII
gtkwave::addSignalsFromList     {
                                tb.uut.s_R_stack_ptr
                                tb.uut.s_R
                                tb.uut.s_T
                                tb.uut.s_N
                                tb.uut.s_Np_stack_ptr
                                }
gtkwave::/Edit/Insert_Comment   "uc side of RAM"
gtkwave::addSignalsFromList     "tb.uut.s__axi_lite__mc_addr"
