#!/usr/bin/env python3
"""
Inserts translated Greek script into the Harvest Moon: FoMT ROM using the runtime redirection hook.
Applies font glyphs if not already present.
Outputs patched ROM and IPS patch.
"""
import os
import sys
import json
import struct
import unicodedata
from hmgreek import BASE_ADDR, code_of, glyph_addr
import glyphs
from build_stub import build_stub_bytes

def apply_font_patch_if_needed(rom, orig):
    """Ensures the v1 polytonic font glyphs and engine hook are in the ROM."""
    T = 0x4FA7A0
    def rom_glyph(c):
        i = struct.unpack_from('<h', orig, T + 2 * ord(c))[0]
        return [format(b, '08b').replace('0', '.').replace('1', '#') for b in orig[BASE_ADDR + i * 12: BASE_ADDR + i * 12 + 12]]

    glyphs.LOW_LATIN = {}
    G = {}
    for cp in list(range(0x370, 0x400)) + list(range(0x1F00, 0x2000)):
        ch = chr(cp)
        if unicodedata.category(ch) not in ('Ll', 'Lu', 'Lt') and ch not in glyphs.STANDALONE_DIACRITICS: continue
        g = glyphs.build_glyph(ch, rom_glyph)
        if g: G[cp] = g
    G[0x387] = ['........'] * 6 + ['...##...', '...##...'] + ['........'] * 4

    def bl(at, target):
        off = target - (at + 4)
        assert off % 2 == 0 and -(1 << 22) <= off < (1 << 22)
        hi = 0xF000 | ((off >> 12) & 0x7FF)
        lo = 0xF800 | ((off >> 1) & 0x7FF)
        return struct.pack('<HH', hi, lo)
    def hw(*v): return b''.join(struct.pack('<H', x) for x in v)

    # Patch 1: default width register r6 = 2
    if rom[0xD0D2E:0xD0D30] != b'\x02\x26':
        rom[0xD0D2E:0xD0D30] = b'\x02\x26'

    # Patch 2: glyph dispatch at 0xD0E3C (28 bytes)
    A = 0xD0E3C
    new = b''
    new += hw(0x0A91)            # d0e3c lsrs r1,r2,#10
    new += hw(0x2938)            # d0e3e cmp  r1,#0x38 (code 0xE000-0xE3FF)
    new += hw(0xD102)            # d0e40 bne  d0e48
    new += hw(0x0095)            # d0e42 lsls r5,r2,#2
    new += hw(0x2601)            # d0e44 movs r6,#1
    new += hw(0xE007)            # d0e46 b    d0e58
    new += hw(0x1C10)            # d0e48 adds r0,r2,#0
    new += bl(A + 0xE, 0xD0CD4)  # d0e4a bl   0xD0CD4
    new += hw(0x2800)            # d0e4e cmp  r0,#0
    new += hw(0xDB02)            # d0e50 blt  d0e58
    new += hw(0x490A)            # d0e52 ldr  r1,[pc,#0x28]  (=0x08523290 literal at d0e7c)
    new += hw(0x0040)            # d0e54 lsls r0,r0,#1
    new += hw(0x5E0D)            # d0e56 ldrsh r5,[r1,r0]
    rom[A:A + 28] = new

    # Write glyph bitmaps
    for cp, g in G.items():
        c = code_of(cp); a = glyph_addr(c)
        assert 0x75C244 <= a and a + 12 <= 0x800000
        rom[a:a + 12] = glyphs.rows_to_bytes(g)

def create_ips(orig, patched):
    recs = []; i = 0; n = len(patched); orig_n = len(orig)
    while i < n:
        o_val = orig[i] if i < orig_n else 0xFF
        if patched[i] != o_val:
            j = i
            while j < n and (patched[j] != (orig[j] if j < orig_n else 0xFF) or (j + 1 < n and patched[j + 1] != (orig[j + 1] if j + 1 < orig_n else 0xFF) and j - i < 0x100)):
                j += 1
            recs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for s, e in recs:
        if merged and s - merged[-1][1] <= 8:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    ips = bytearray(b'PATCH')
    for s, e in merged:
        while e - s > 0:
            ln = min(e - s, 0xFFFF)
            assert s != 0x454F46
            ips += struct.pack('>I', s)[1:] + struct.pack('>H', ln) + bytes(patched[s:s + ln])
            s += ln
    ips += b'EOF'
    return bytes(ips)

def insert_translations(rom_path, json_path, out_rom_path, out_ips_path):
    orig = open(rom_path, 'rb').read()
    assert len(orig) == 0x800000 and orig[0xAC:0xB0] == b'A4NE', "Invalid HM:FoMT USA ROM"
    rom = bytearray(orig)

    # 1. Apply font patch
    apply_font_patch_if_needed(rom, orig)

    # 2. Load translations
    script_data = json.load(open(json_path, 'r', encoding='utf-8'))
    print(f"Loaded {len(script_data)} translated messages.")

    # 3. Layout ROM free space
    # Free range: 0x7A0000 to 0x800000 (393,216 bytes)
    BASE_OFFSET = 0x7A0000
    STUB_SIZE = 0x50 # 80 bytes
    stub_gba_addr = 0x08000000 + BASE_OFFSET
    table_offset = BASE_OFFSET + STUB_SIZE
    table_gba_addr = 0x08000000 + table_offset

    # Collect entries and layout strings
    entries = []
    string_pool = bytearray()
    
    # Calculate table size first so we know where strings start
    # Each message can have multiple original addresses
    total_entries_count = sum(len(msg['addrs']) for msg in script_data)
    table_size = 4 + total_entries_count * 8
    # Align strings start to 4 bytes
    strings_start_offset = (table_offset + table_size + 3) & ~3
    current_string_offset = strings_start_offset

    for msg in script_data:
        msg_bytes = bytes.fromhex(msg['hex']) + b'\x00' # NUL-terminated
        # String GBA address
        msg_gba_addr = 0x08000000 + current_string_offset
        for addr_hex in msg['addrs']:
            orig_rom_off = int(addr_hex, 16)
            orig_gba_addr = 0x08000000 + orig_rom_off
            entries.append((orig_gba_addr, msg_gba_addr))
        
        string_pool += msg_bytes
        current_string_offset += len(msg_bytes)
        # Pad to 4 bytes alignment
        while len(string_pool) % 4 != 0:
            string_pool.append(0)
            current_string_offset += 1

    # Sort table by original address
    entries.sort(key=lambda x: x[0])
    table_bytes = struct.pack('<I', len(entries))
    for orig_ptr, greek_ptr in entries:
        table_bytes += struct.pack('<II', orig_ptr, greek_ptr)

    total_used = (strings_start_offset - BASE_OFFSET) + len(string_pool)
    print(f"Total entries in redirection table: {len(entries)}")
    print(f"Redirection stub at: 0x{BASE_OFFSET:06X} (GBA 0x{stub_gba_addr:08X})")
    print(f"Redirection table at: 0x{table_offset:06X} (GBA 0x{table_gba_addr:08X}), size {len(table_bytes)} bytes")
    print(f"String pool at: 0x{strings_start_offset:06X}, size {len(string_pool)} bytes")
    print(f"Total upper free space used: {total_used} / {0x800000 - BASE_OFFSET} bytes ({(total_used/(0x800000 - BASE_OFFSET))*100:.2f}%)")

    # If exceeding 8 MiB (0x800000), expand ROM to 16 MiB (0x1000000)
    if BASE_OFFSET + total_used > len(rom):
        target_len = max(0x1000000, (BASE_OFFSET + total_used + 0xFFFFF) & ~0xFFFFF)
        print(f"Exceeded 8 MiB mark. Expanding ROM to 16 MiB (size: {target_len} bytes)...")
        rom.extend(b'\xFF' * (target_len - len(rom)))

    assert BASE_OFFSET + total_used <= len(rom), "ROM buffer overflow!"

    # 4. Generate and write stub
    stub_code = build_stub_bytes(stub_gba_addr, table_gba_addr)
    assert len(stub_code) == STUB_SIZE
    rom[BASE_OFFSET:BASE_OFFSET + STUB_SIZE] = stub_code

    # 5. Write table
    rom[table_offset:table_offset + len(table_bytes)] = table_bytes

    # 6. Write strings
    rom[strings_start_offset:strings_start_offset + len(string_pool)] = string_pool

    # 7. Patch 0x080ADD5C trampoline
    # 0xADD5C: ldr r3, [pc, #0] (0x4B00)
    # 0xADD5E: bx  r3          (0x4718)
    # 0xADD60: stub_gba_addr | 1
    trampoline = struct.pack('<HHI', 0x4B00, 0x4718, stub_gba_addr | 1)
    rom[0xADD5C:0xADD5C + 8] = trampoline

    # 8. Save ROM
    open(out_rom_path, 'wb').write(rom)
    print(f"Patched ROM saved to: {out_rom_path}")

    # 9. Create IPS patch
    ips_data = create_ips(orig, rom)
    open(out_ips_path, 'wb').write(ips_data)
    print(f"IPS patch saved to: {out_ips_path} ({len(ips_data)} bytes)")

if __name__ == '__main__':
    rom_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('HM_ROM', 'Harvest Moon - Friends of Mineral Town (USA).gba')
    json_file = sys.argv[2] if len(sys.argv) > 2 else 'greek_script.json'
    out_rom = sys.argv[3] if len(sys.argv) > 3 else 'hm_fomt_greek_pilot.gba'
    out_ips = sys.argv[4] if len(sys.argv) > 4 else 'patches/hm_fomt_greek_pilot.ips'
    
    os.makedirs(os.path.dirname(os.path.abspath(out_ips)), exist_ok=True)
    insert_translations(rom_file, json_file, out_rom, out_ips)
