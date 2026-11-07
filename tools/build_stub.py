import struct
import capstone
from unicorn import *
from unicorn.arm_const import *

cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

COND_EQ = 0
COND_NE = 1
COND_CS = 2
COND_CC = 3
COND_MI = 4
COND_PL = 5
COND_VS = 6
COND_VC = 7
COND_HI = 8
COND_LS = 9
COND_GE = 10
COND_LT = 11
COND_GT = 12
COND_LE = 13

def build_stub_bytes(stub_base_gba, table_gba_addr):
    """
    Builds the Thumb machine code for the binary search redirection stub.
    stub_base_gba: e.g. 0x087A0000
    table_gba_addr: e.g. 0x087A0080
    """
    # Layout plan:
    # 0x00: push {r0, r2, r4-r7, lr}   (0xB5F5)
    # 0x02: ldr r4, [pc, #lit_offset]  (loads table_gba_addr)
    # 0x04: ldr r5, [r4, #0]           (0x6825) - r5 = count
    # 0x06: cmp r5, #0                 (0x2D00)
    # 0x08: beq .done                  (branch if count == 0)
    # 0x0A: movs r6, #0                (0x2600) - low = 0
    # 0x0C: subs r7, r5, #1            (0x1E6F) - high = count - 1
    # .loop (0x0E):
    # 0x0E: cmp r6, r7                 (0x42BE)
    # 0x10: bhi .done                  (branch if low > high)
    # 0x12: adds r2, r6, r7            (0x19F2) - r2 = low + high
    # 0x14: lsrs r2, r2, #1            (0x0852) - r2 = mid = (low + high) >> 1
    # 0x16: lsls r3, r2, #3            (0x00D3) - r3 = mid * 8
    # 0x18: adds r3, #4                (0x3304) - r3 = mid * 8 + 4 (skip count header)
    # 0x1A: adds r3, r4, r3            (0x18E3) - r3 = &table[mid]
    # 0x1C: ldr r0, [r3, #0]           (0x6818) - r0 = table[mid].orig_addr
    # 0x1E: cmp r0, r1                 (0x4288) - compare key with input r1
    # 0x20: beq .found                 (branch if key == target)
    # 0x22: blo .is_lower              (branch if key < target)
    # .is_higher (0x24):
    # 0x24: cmp r2, #0                 (0x2A00) - guard mid == 0
    # 0x26: beq .done                  (branch to done if mid == 0 to avoid underflow)
    # 0x28: subs r7, r2, #1            (0x1E57) - high = mid - 1
    # 0x2A: b .loop                    (jump back to loop)
    # .is_lower (0x2C):
    # 0x2C: adds r6, r2, #1            (0x1C56) - low = mid + 1
    # 0x2E: b .loop                    (jump back to loop)
    # .found (0x30):
    # 0x30: ldr r1, [r3, #4]           (0x6859) - r1 = table[mid].greek_addr
    # .done (0x32):
    # 0x32: pop {r0, r2, r4-r7}        (0xBCF5)
    # 0x34: str r1, [r0, #8]           (0x6081)
    # 0x36: str r2, [r0, #0xc]         (0x60C2)
    # 0x38: movs r3, #0                (0x2300)
    # 0x3A: str r3, [r0, #0x10]        (0x6103)
    # 0x3C: strb r3, [r0, #0x14]       (0x7503)
    # 0x3E: rsbs r2, r1, #0            (0x424A)
    # 0x40: orrs r2, r1                (0x430A)
    # 0x42: lsrs r2, r2, #0x1f         (0x0FD2)
    # 0x44: str r2, [r0]               (0x6002)
    # 0x46: strh r3, [r0, #6]          (0x80C3)
    # 0x48: pop {pc}                   (0xBD00)
    # 0x4A: nop (0x46C0) for alignment
    # 0x4C: .word table_gba_addr
    
    code = bytearray()
    
    def b(src, dst):
        imm = (dst - (src + 4)) >> 1
        return struct.pack('<H', 0xE000 | (imm & 0x7FF))

    def bcc(cond, src, dst):
        imm = (dst - (src + 4)) >> 1
        assert -128 <= imm <= 127, f'bcc out of range: {imm}'
        return struct.pack('<H', 0xD000 | ((cond & 0xF) << 8) | (imm & 0xFF))

    def ldr_pc(reg, src, dst):
        pc_base = (src + 4) & ~3
        imm = (dst - pc_base) >> 2
        assert 0 <= imm <= 255, f'ldr_pc out of range: {imm}'
        return struct.pack('<H', 0x4800 | (reg << 8) | (imm & 0xFF))

    # Addresses
    A_PUSH = 0x00
    A_LDR_TABLE = 0x02
    A_LDR_COUNT = 0x04
    A_CMP_COUNT = 0x06
    A_BEQ_DONE = 0x08
    A_MOV_LOW = 0x0A
    A_SUB_HIGH = 0x0C
    A_LOOP = 0x0E
    A_BHI_DONE = 0x10
    A_ADD_MID = 0x12
    A_LSR_MID = 0x14
    A_LSL_MID = 0x16
    A_ADD_SKIP = 0x18
    A_ADD_TBL = 0x1A
    A_LDR_KEY = 0x1C
    A_CMP_KEY = 0x1E
    A_BEQ_FOUND = 0x20
    A_BLO_LOWER = 0x22
    A_CMP_ZERO = 0x24
    A_BEQ_DONE2 = 0x26
    A_SUB_HIGH2 = 0x28
    A_B_LOOP1 = 0x2A
    A_ADD_LOW = 0x2C
    A_B_LOOP2 = 0x2E
    A_FOUND = 0x30
    A_DONE = 0x32
    A_POP_REGS = 0x32
    A_ORIG_START = 0x34
    A_POP_PC = 0x48
    A_NOP = 0x4A
    A_LITERAL = 0x4C

    code += struct.pack('<H', 0xB5F5)                 # 00: push {r0, r2, r4-r7, lr}
    code += ldr_pc(4, A_LDR_TABLE, A_LITERAL)         # 02: ldr r4, [pc, #lit]
    code += struct.pack('<H', 0x6825)                 # 04: ldr r5, [r4, #0] (count)
    code += struct.pack('<H', 0x2D00)                 # 06: cmp r5, #0
    code += bcc(COND_EQ, A_BEQ_DONE, A_DONE)          # 08: beq .done
    code += struct.pack('<H', 0x2600)                 # 0A: movs r6, #0 (low = 0)
    code += struct.pack('<H', 0x1E6F)                 # 0C: subs r7, r5, #1 (high = count - 1)
    # Loop
    assert len(code) == A_LOOP
    code += struct.pack('<H', 0x42BE)                 # 0E: cmp r6, r7
    code += bcc(COND_HI, A_BHI_DONE, A_DONE)          # 10: bhi .done
    code += struct.pack('<H', 0x19F2)                 # 12: adds r2, r6, r7
    code += struct.pack('<H', 0x0852)                 # 14: lsrs r2, r2, #1 (mid)
    code += struct.pack('<H', 0x00D3)                 # 16: lsls r3, r2, #3 (mid * 8)
    code += struct.pack('<H', 0x3304)                 # 18: adds r3, #4
    code += struct.pack('<H', 0x18E3)                 # 1A: adds r3, r4, r3 (&table[mid])
    code += struct.pack('<H', 0x6818)                 # 1C: ldr r0, [r3, #0] (orig_addr)
    code += struct.pack('<H', 0x4288)                 # 1E: cmp r0, r1
    code += bcc(COND_EQ, A_BEQ_FOUND, A_FOUND)        # 20: beq .found
    code += bcc(COND_CC, A_BLO_LOWER, A_ADD_LOW)      # 22: blo .is_lower
    # Higher
    code += struct.pack('<H', 0x2A00)                 # 24: cmp r2, #0
    code += bcc(COND_EQ, A_BEQ_DONE2, A_DONE)         # 26: beq .done
    code += struct.pack('<H', 0x1E57)                 # 28: subs r7, r2, #1 (high = mid - 1)
    code += b(A_B_LOOP1, A_LOOP)                      # 2A: b .loop
    # Lower
    assert len(code) == A_ADD_LOW
    code += struct.pack('<H', 0x1C56)                 # 2C: adds r6, r2, #1 (low = mid + 1)
    code += b(A_B_LOOP2, A_LOOP)                      # 2E: b .loop
    # Found
    assert len(code) == A_FOUND
    code += struct.pack('<H', 0x6859)                 # 30: ldr r1, [r3, #4] (greek_addr)
    # Done / Original 0xADD5C logic
    assert len(code) == A_DONE
    code += struct.pack('<H', 0xBCF5)                 # 32: pop {r0, r2, r4-r7}
    code += struct.pack('<H', 0x6081)                 # 34: str r1, [r0, #8]
    code += struct.pack('<H', 0x60C2)                 # 36: str r2, [r0, #0xc]
    code += struct.pack('<H', 0x2300)                 # 38: movs r3, #0
    code += struct.pack('<H', 0x6103)                 # 3A: str r3, [r0, #0x10]
    code += struct.pack('<H', 0x7503)                 # 3C: strb r3, [r0, #0x14]
    code += struct.pack('<H', 0x424A)                 # 3E: rsbs r2, r1, #0
    code += struct.pack('<H', 0x430A)                 # 40: orrs r2, r1
    code += struct.pack('<H', 0x0FD2)                 # 42: lsrs r2, r2, #0x1f
    code += struct.pack('<H', 0x6002)                 # 44: str r2, [r0]
    code += struct.pack('<H', 0x80C3)                 # 46: strh r3, [r0, #6]
    code += struct.pack('<H', 0xBD00)                 # 48: pop {pc}
    code += struct.pack('<H', 0x46C0)                 # 4A: nop
    assert len(code) == A_LITERAL
    code += struct.pack('<I', table_gba_addr)         # 4C: table_gba_addr
    assert len(code) == 0x50
    return bytes(code)

if __name__ == '__main__':
    stub = build_stub_bytes(0x087A0000, 0x087A0100)
    print(f'Stub length: {len(stub)} bytes')
    for ins in cs.disasm(stub, 0x087A0000):
        print(f'0x{ins.address:08X}:  {ins.mnemonic:<7} {ins.op_str}')
