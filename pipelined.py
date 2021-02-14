from myhdl import block, always_comb, instance, intbv, delay, always, instances
from myhdl import Signal as signal
from myhdl import ResetSignal as rsig
from myhdl import StopSimulation as expectation
from defs import *
from random import randrange


@block
def clock(clk):

    @always(delay(10))
    def clck():
        clk.next = not clk

    return clck


@block
def pc_adder(reset, clk, pc, pc_addr):

    @always(clk.posedge)
    def padder():
        if reset.next == INACTIVE_HIGH:
            pc_addr.next = (pc.next + 1)

    return padder


@block
def pc_mux(reset, pc, pc_addr, jmp_addr, pc_sel):

    @always_comb
    def pmux():
        if reset.next == INACTIVE_HIGH:
            if pc_sel:
                pc.next = jmp_addr
            else:
                pc.next = pc_addr

    return pmux


@block
def pc_assign(reset, read_addr, pc):

    @always_comb
    def assign():
        if reset.next == INACTIVE_HIGH:
            read_addr.next = pc

    return assign


@block
def inst_mem(reset, read_addr, instruction):

    inx = open('mc_code').read().splitlines()
    inst_ram = [signal(intbv(int(inx[i], 2))[CPU_BITS:]) for i in range(128)]

    @always_comb
    def itcm():
        if reset.next == INACTIVE_HIGH:
            instruction.next = inst_ram[read_addr]

    return itcm


@block
def imm_gen(reset, instruction, im_gen):

    @always_comb
    def immgen():
        if reset.next == INACTIVE_HIGH:

            if instruction[7:0] == ITYPE:
                im_gen.next[12:] = instruction[32:20]

            elif instruction[7:0] == STYPE:
                im_gen.next[12:5] = instruction[32:25]
                im_gen.next[5:] = instruction[12:7]

            elif instruction[7:0] == SBTYPE:
                im_gen.next[12] = instruction[31]
                im_gen.next[11:5] = instruction[31:25]
                im_gen.next[11] = instruction[7]
                im_gen.next[5:1] = instruction[12:8]
                im_gen.next[0] = 0

            if instruction[31] == 0:
                pad = signal(intbv(0)[20:])
                im_gen.next[32:(31 - 20)] = pad

            else:
                temp = (2**20) - 1
                pad = signal(intbv(temp)[20:])
                im_gen.next[32:(31 - 20)] = pad

    return immgen


@block
def reg_file(reset, clk, ra, rb, wa, wda, reg_wr, rda, rdb):

    registers = [signal(intbv(10 + i)[CPU_BITS:]) for i in range(32)]

    @always_comb
    def read():
        if reset.next == INACTIVE_HIGH:
            if ra:
                rda.next = registers[ra]

            if rb:
                rdb.next = registers[rb]

    @always(clk.posedge)
    def write():
        if reset.next == INACTIVE_HIGH:
            if reg_wr and (wa > 0):
                registers[wa].next = wda

    return read, write


@block
def control(reset, opcode, brnch, mem_rd, mem_to_rgs, alu_op, mem_wr, alu_src, reg_wr):

    @always_comb
    def cont():
        if reset.next == INACTIVE_HIGH:
            if opcode == RTYPE:
                alu_src.next = False
                mem_to_rgs.next = False
                reg_wr.next = True
                mem_rd.next = False
                mem_wr.next = False
                brnch.next = False
                alu_op.next = 2

            elif opcode == ITYPE:
                alu_src.next = True
                mem_to_rgs.next = True
                reg_wr.next = True
                mem_rd.next = True
                mem_wr.next = False
                brnch.next = False
                alu_op.next = 0

            elif opcode == STYPE:
                alu_src.next = True
                mem_to_rgs.next = False
                reg_wr.next = False
                mem_rd.next = False
                mem_wr.next = True
                brnch.next = False
                alu_op.next = 0

            elif opcode == SBTYPE:
                alu_src.next = False
                mem_to_rgs.next = False
                reg_wr.next = False
                mem_rd.next = False
                mem_wr.next = False
                brnch.next = True
                alu_op.next = 7

    return cont


@block
def ifid(reset, instruction, ifid_reg, pc):

    @always_comb
    def reg():
        if reset.next == INACTIVE_HIGH:
            ifid_reg.next[CPU_BITS:0] = instruction
            ifid_reg.next[IFID_REG_BITS:CPU_BITS] = pc

    return reg


@block
def cpu_top(clk, reset):

    pc, pc_addr, jmp_addr, read_addr, instruction = [signal(intbv(0)[CPU_BITS:]) for _ in range(5)]
    pc_sel = signal(intbv(0)[1:])

    ifid_reg = signal(intbv(0)[IFID_REG_BITS:])

    padr = pc_adder(reset, clk, pc, pc_addr)
    padr.convert(hdl='Verilog')

    pcmx = pc_mux(reset, pc, pc_addr, jmp_addr, pc_sel)
    pcmx.convert(hdl='Verilog')

    pcmx = pc_mux(reset, pc, pc_addr, jmp_addr, pc_sel)
    pcmx.convert(hdl='Verilog')

    nxpc = pc_assign(reset, read_addr, pc)
    nxpc.convert(hdl='Verilog')

    imem = inst_mem(reset, read_addr, instruction)
    imem.convert(hdl='Verilog')

    rfdi = ifid(reset, instruction, ifid_reg, pc)
    rfdi.convert(hdl='Verilog')

    return instances()


@block
def top():

    clk = signal(intbv(0)[1:])
    reset = rsig(0, active=0, isasync=True)

    cl = clock(clk)

    cpu = cpu_top(clk, reset)
    # cpu.convert(hdl='Verilog')

    @instance
    def stimulus():
        reset.next = ACTIVE_LOW
        yield clk.negedge
        reset.next = INACTIVE_HIGH

    return instances()


def main():

    tb = top()
    tb.config_sim(trace=True)
    tb.run_sim(200)


if __name__ == '__main__':
    main()
