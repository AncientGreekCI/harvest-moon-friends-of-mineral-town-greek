import struct
import json
from unicorn import *
from unicorn.arm_const import *

ROM_PATH = 'Harvest Moon - Friends of Mineral Town (Greek Pilot).gba'
SCRIPT_PATH = 'greek_script.json'

def test_full_rom():
    rom = open(ROM_PATH, 'rb').read()
    script = json.load(open(SCRIPT_PATH, 'r', encoding='utf-8'))

    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    mu.mem_map(0x08000000, len(rom))
    mu.mem_map(0x02000000, 0x40000)
    mu.mem_map(0x03000000, 0x8000)
    mu.mem_map(0x04000000, 0x1000) # I/O regs dummy

    mu.mem_write(0x08000000, rom)

    STREAM_OBJ = 0x03001000
    BUF = 0x03002000
    SP = 0x03007F00
    LR = 0x08050463 # Return address to 0x08050462 Thumb

    # Check trampoline at 0x080ADD5C
    trampoline = rom[0xADD5C:0xADD64]
    ins1, ins2, dest = struct.unpack('<HHI', trampoline)
    assert ins1 == 0x4B00, f"Expected ldr r3, [pc, #0], got {hex(ins1)}"
    assert ins2 == 0x4718, f"Expected bx r3, got {hex(ins2)}"
    assert dest == 0x087A0001, f"Expected stub at 0x087A0001, got {hex(dest)}"
    print("Trampoline at 0x080ADD5C verified.")

    # 1. Test each of the 20 translated pilot lines
    for msg in script:
        for addr_hex in msg['addrs']:
            orig_gba = 0x08000000 + int(addr_hex, 16)
            
            # Reset registers and stream object
            mu.mem_write(STREAM_OBJ, b'\x00' * 0x40)
            mu.reg_write(UC_ARM_REG_R0, STREAM_OBJ)
            mu.reg_write(UC_ARM_REG_R1, orig_gba)
            mu.reg_write(UC_ARM_REG_R2, BUF)
            mu.reg_write(UC_ARM_REG_SP, SP)
            mu.reg_write(UC_ARM_REG_LR, LR)

            # Call 0x080ADD5C
            mu.emu_start(0x080ADD5C | 1, LR & ~1, count=1000)

            # Check result stored at STREAM_OBJ + 8
            got_ptr = struct.unpack_from('<I', mu.mem_read(STREAM_OBJ + 8, 4))[0]
            assert got_ptr >= 0x087A00F4, f"Failed redirect for {msg['id']} at {hex(orig_gba)}: got {hex(got_ptr)}"
            
            # Read string at got_ptr and compare with msg['hex']
            rom_off = got_ptr - 0x08000000
            expected_bytes = bytes.fromhex(msg['hex'])
            actual_bytes = rom[rom_off:rom_off + len(expected_bytes)]
            assert actual_bytes == expected_bytes, f"Content mismatch for {msg['id']}"

    print(f"All {len(script)} messages successfully redirected to exact Greek bytes!")

    # 2. Test non-translated address (must remain unchanged!)
    untranslated_orig = 0x08123456 # Dummy address outside message redirection table
    mu.mem_write(STREAM_OBJ, b'\x00' * 0x40)
    mu.reg_write(UC_ARM_REG_R0, STREAM_OBJ)
    mu.reg_write(UC_ARM_REG_R1, untranslated_orig)
    mu.reg_write(UC_ARM_REG_R2, BUF)
    mu.reg_write(UC_ARM_REG_SP, SP)
    mu.reg_write(UC_ARM_REG_LR, LR)

    mu.emu_start(0x080ADD5C | 1, LR & ~1, count=1000)
    got_ptr = struct.unpack_from('<I', mu.mem_read(STREAM_OBJ + 8, 4))[0]
    assert got_ptr == untranslated_orig, f"Untranslated string should remain {hex(untranslated_orig)}, got {hex(got_ptr)}"
    print(f"Untranslated message fallback verified (passed through unchanged).")

    # 3. Test calling from actual scene setter at 0x08050454
    # 050454: adds r4, r5, #0
    # 050456: adds r4, #0xec
    # 050458: adds r0, r4, #0
    # 05045a: adds r1, r7, #0
    # 05045c: adds r2, r6, #0
    # 05045e: bl   #0x80add5c
    # 050462: adds r0, r4, #0
    CALL_SITE = 0x08050458
    STOP_PC = 0x08050462
    mu.reg_write(UC_ARM_REG_R4, STREAM_OBJ)
    mu.reg_write(UC_ARM_REG_R7, 0x080FB23C) # Mother's first line
    mu.reg_write(UC_ARM_REG_R6, BUF)
    mu.reg_write(UC_ARM_REG_SP, SP)
    mu.emu_start(CALL_SITE | 1, STOP_PC, count=1000)

    got_ptr = struct.unpack_from('<I', mu.mem_read(STREAM_OBJ + 8, 4))[0]
    assert got_ptr >= 0x087A00F4, f"Real call site test failed: got {hex(got_ptr)}"
    print(f"Real scene caller at 0x08050458 verified end-to-end!")
    print("ALL ROM HOOK AND TRANSLATION REDIRECTION TESTS PASSED!")

if __name__ == '__main__':
    test_full_rom()
