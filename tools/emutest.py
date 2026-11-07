import os
import struct, sys
from unicorn import *
from unicorn.arm_const import *
from hmgreek import *
orig = open(os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'),'rb').read()
patched = open('patched.gba','rb').read()
FUNC = 0x080D0D28
def run(rom, code):
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    mu.mem_map(0x08000000, 0x800000); mu.mem_write(0x08000000, rom)
    mu.mem_map(0x03000000, 0x8000); mu.mem_map(0x02000000, 0x40000)
    mu.mem_map(0x04000000, 0x1000)
    SP = 0x03007F00; BUF = 0x03001000
    mu.reg_write(UC_ARM_REG_SP, SP); mu.reg_write(UC_ARM_REG_R0, BUF); mu.reg_write(UC_ARM_REG_R1, code)
    LR = 0x08700001; mu.reg_write(UC_ARM_REG_LR, LR)
    calls = []
    def hook(uc, addr, size, ud):
        if addr in (0x080D3914, 0x080D3918, 0x080D391C):
            r = [uc.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            calls.append((addr, r[0], r[1], r[2] if addr == 0x080D3914 else None))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            uc.reg_write(UC_ARM_REG_R0, 0)   # thunk return value (copy routine returns nothing useful)
    mu.hook_add(UC_HOOK_CODE, hook, begin=0x080D3910, end=0x080D3920)
    try:
        mu.emu_start(FUNC | 1, LR & ~1, count=20000)
    except UcError as e:
        return ('ERR', str(e), calls)
    return (mu.reg_read(UC_ARM_REG_R0), calls)
# regression: single-byte and a spread of 2-byte codes must be identical
bad = 0
codes = list(range(0, 0x100)) + list(range(0x8140, 0x8200)) + list(range(0x889F, 0x8A00, 7)) + list(range(0x9F40, 0x9FFF, 5)) + [0xFF21, 0xFF3F, 0xFF40, 0xFF41, 0xFFFF, 0x8140, 0x829F, 0x82A0, 0x8340, 0xE040, 0xEAA4, 0xDF] 
codes = [c for c in codes if not (0xE000 <= c < 0xE400)]
codes += list(range(0xE400, 0xF000, 11)) + list(range(0xF040, 0xFC00, 13))
for c in codes:
    a = run(orig, c); b = run(patched, c)
    if a[0] == 'ERR' or b[0] == 'ERR' or a != b:
        bad += 1
        if bad < 8: print('MISMATCH', hex(c), a, b)
print('regression codes:', len(codes), 'mismatches:', bad)
# custom codes
ok = 0; fail = 0
for ch in 'αβγωΑΩἀἐἦῇὁΐΰΆάὤᾠ':
    c = code_of(ord(ch)); r = run(patched, c)
    want = 0x08000000 + BASE_ADDR + 12 * (c << 2)
    good = (r[0] == 1 and len(r[1]) == 1 and r[1][0][1] == want)
    ok += good; fail += (not good)
    if not good: print('FAIL', ch, hex(c), r, hex(want))
print('custom codes ok', ok, 'fail', fail)
c = code_of(ord('α')); r = run(patched, c); print('sample', hex(c), 'width', r[0], 'src', hex(r[1][0][1]), 'dst', hex(r[1][0][2]))
# lead byte alone must still report 'no glyph' (returns 0) so the engine waits for byte 2
print('lead-only E0/E1/E2 returns:', [run(patched, b)[0] for b in (0xE0, 0xE1, 0xE2)])
# ascii A as sanity
print('A returns', run(patched, 0x41)[0], hex(run(patched,0x41)[1][0][1]))
