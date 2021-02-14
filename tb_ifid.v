module tb_ifid;

reg reset;
reg [31:0] instruction;
wire [63:0] ifid_reg;
reg [31:0] pc;

initial begin
    $from_myhdl(
        reset,
        instruction,
        pc
    );
    $to_myhdl(
        ifid_reg
    );
end

ifid dut(
    reset,
    instruction,
    ifid_reg,
    pc
);

endmodule
