module tb_pc_adder;

reg reset;
reg [0:0] clk;
reg [31:0] pc;
wire [31:0] pc_addr;

initial begin
    $from_myhdl(
        reset,
        clk,
        pc
    );
    $to_myhdl(
        pc_addr
    );
end

pc_adder dut(
    reset,
    clk,
    pc,
    pc_addr
);

endmodule
