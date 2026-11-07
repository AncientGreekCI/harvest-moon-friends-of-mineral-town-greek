import os, struct, sys
from unicorn import *
from unicorn.arm_const import *
from build_stub import build_stub_bytes

STUB_ADDR = 0x087A0000
TABLE_ADDR = 0x087A0060

def run_test(entries, target_r1):
    """
    Simulates calling stream_init with target_r1.
    entries: list of (orig_addr, greek_addr)
    target_r1: input string address passed in r1
    """
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    # Map ROM space (0x08000000, 8MB) and RAM space (0x02000000, 256KB), (0x03000000, 32KB)
    mu.mem_map(0x08000000, 0x800000)
    mu.mem_map(0x02000000, 0x40000)
    mu.mem_map(0x03000000, 0x8000)

    # Build table
    table_bytes = struct.pack('<I', len(entries))
    for orig, greek in entries:
        table_bytes += struct.pack('<II', orig, greek)
    
    # Build stub
    stub = build_stub_bytes(STUB_ADDR, TABLE_ADDR)
    
    # Write to memory
    mu.mem_write(STUB_ADDR, stub)
    mu.mem_write(TABLE_ADDR, table_bytes)
    
    # Setup stream object in IWRAM
    OBJ = 0x03001000
    BUF = 0x03002000
    SP = 0x03007F00
    LR = 0x08050463 # Return address with Thumb bit set
    
    # Clear obj memory
    mu.mem_write(OBJ, b'\x00' * 0x40)
    
    mu.reg_write(UC_ARM_REG_R0, OBJ)
    mu.reg_write(UC_ARM_REG_R1, target_r1)
    mu.reg_write(UC_ARM_REG_R2, BUF)
    mu.reg_write(UC_ARM_REG_SP, SP)
    mu.reg_write(UC_ARM_REG_LR, LR)
    
    # Execute stub from STUB_ADDR (Thumb mode)
    # We stop when PC reaches LR (0x08050462)
    mu.emu_start(STUB_ADDR | 1, LR & ~1, count=1000)
    
    # Check results in OBJ
    # obj+8 = text pointer
    # obj+0xc = buf pointer
    # obj = (r1 != 0)
    res_ptr = struct.unpack_from('<I', mu.mem_read(OBJ + 8, 4))[0]
    res_buf = struct.unpack_from('<I', mu.mem_read(OBJ + 12, 4))[0]
    res_flag = struct.unpack_from('<I', mu.mem_read(OBJ, 4))[0]
    sp_after = mu.reg_read(UC_ARM_REG_SP)
    
    assert sp_after == SP, f"Stack leak! SP before {hex(SP)}, after {hex(sp_after)}"
    assert res_buf == BUF, f"Buffer mismatch! Expected {hex(BUF)}, got {hex(res_buf)}"
    assert res_flag == (1 if res_ptr != 0 else 0), "Flag mismatch"
    
    return res_ptr

if __name__ == '__main__':
    print("Testing binary search redirection stub...")
    
    # Test 1: Empty table
    r = run_test([], 0x080FB23C)
    assert r == 0x080FB23C, f"Empty table failed: got {hex(r)}"
    print("Test 1 passed (empty table fallback)")

    # Test 2: Single entry, matched
    r = run_test([(0x080FB23C, 0x087A1000)], 0x080FB23C)
    assert r == 0x087A1000, f"Single entry match failed: got {hex(r)}"
    print("Test 2 passed (single entry match)")

    # Test 3: Single entry, non-matched (lower and higher)
    r = run_test([(0x080FB23C, 0x087A1000)], 0x08000000)
    assert r == 0x08000000
    r = run_test([(0x080FB23C, 0x087A1000)], 0x08100000)
    assert r == 0x08100000
    print("Test 3 passed (single entry non-match)")

    # Test 4: Multiple entries (5 entries), match each and non-matches
    entries = [
        (0x080FB23C, 0x087A1000),
        (0x080FB284, 0x087A1050),
        (0x080FB2D0, 0x087A10A0),
        (0x080FB308, 0x087A10F0),
        (0x080FB398, 0x087A1140),
    ]
    for orig, greek in entries:
        r = run_test(entries, orig)
        assert r == greek, f"Multi-entry match failed for {hex(orig)}: got {hex(r)}, expected {hex(greek)}"
    print("Test 4 passed (all 5 entries matched correctly)")

    # Test 5: Multi-entry non-matches (before, between, after)
    assert run_test(entries, 0x08000000) == 0x08000000
    assert run_test(entries, 0x080FB250) == 0x080FB250
    assert run_test(entries, 0x080FB2FF) == 0x080FB2FF
    assert run_test(entries, 0x08200000) == 0x08200000
    print("Test 5 passed (boundary & intermediate non-matches)")

    # Test 6: 100 entries binary search stress test
    large_entries = [(0x08000000 + i * 0x100, 0x08700000 + i * 0x20) for i in range(100)]
    for orig, greek in large_entries:
        assert run_test(large_entries, orig) == greek
    # Non matches
    for i in range(100):
        probe = 0x08000000 + i * 0x100 + 4
        assert run_test(large_entries, probe) == probe
    print("Test 6 passed (100-entry stress test: 100 hits + 100 misses)")

    print("ALL STUB EMULATION TESTS PASSED!")
