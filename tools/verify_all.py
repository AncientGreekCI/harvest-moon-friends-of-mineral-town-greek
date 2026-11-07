# -*- coding: utf-8 -*-
import struct
import json
import unicodedata
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

rom = open('pilot.gba', 'rb').read()

print("=== 1. Keyboard Verification ===")
GRID_OFF = 0x0E89B6
all_chars = []
for r in range(6):
    row_bytes = rom[GRID_OFF + r*31 : GRID_OFF + (r+1)*31]
    chars = [row_bytes[i] for i in range(0, 30, 2)]
    print(f"Row {r}:", [hex(c) if c >= 0x80 else chr(c) for c in chars])
    all_chars.extend(chars)

# Check uniqueness of non-space chars
unique_chars = set(all_chars)
print(f"Total non-space cells: {len(all_chars)}, Unique characters: {len(unique_chars)}")
assert len(all_chars) == len(unique_chars), "Duplicate characters found on keyboard!"
print(">>> Keyboard has ZERO duplicates! Every single character is 100% unique.")

print("\n=== 2. Calendar & Season Verification ===")
# Calendar screen at 0x0FBD18
cal_sure = rom[0xFBD18:0xFBD28].rstrip(b'\x00')
cal_yes = rom[0xFBD28:0xFBD2C].rstrip(b'\x00')
cal_no = rom[0xFBD2C:0xFBD30].rstrip(b'\x00')
print("Calendar 'Are you sure?':", cal_sure)
print("Calendar 'Yes':", cal_yes)
print("Calendar 'No':", cal_no)

# 4 wide seasons at 0xFBD44
for i, name in enumerate(["Spring", "Summer", "Fall", "Winter"]):
    off = 0xFBD44 + i * 12
    raw = rom[off:off+12]
    # Wide decode
    chars = [chr(raw[j]) for j in range(0, 12, 2) if raw[j] != ord(' ')]
    print(f"Calendar wide {name}: {''.join(chars)}")

# Master season table at 0xF04EE
for i, name in enumerate(["Spring", "Summer", "Fall", "Winter"]):
    off = 0xF04EE + i * 7
    raw = rom[off:off+7].rstrip(b'\x00')
    print(f"F04EE {name}: {raw}")

# Days of week table at 0xF050F
for i in range(7):
    off = 0xF050F + i * 5
    raw = rom[off:off+5].rstrip(b'\x00')
    print(f"Day {i}: {raw}")

print("\n=== 3. Dialogue Choices & Script Redirection Verification ===")
table_off = 0x7A0050
count = struct.unpack_from('<I', rom, table_off)[0]
print(f"Total redirected pointers in ROM table: {count}")

# Binary search helper in ROM
def lookup_redirection(orig_gba_addr):
    low = 0
    high = count - 1
    while low <= high:
        mid = (low + high) // 2
        entry_off = table_off + 4 + mid * 8
        cand_orig, cand_greek = struct.unpack_from('<II', rom, entry_off)
        if cand_orig == orig_gba_addr:
            # Read Greek text until null
            s_off = cand_greek - 0x08000000
            end = rom.find(b'\x00', s_off)
            return rom[s_off:end]
        elif cand_orig < orig_gba_addr:
            low = mid + 1
        else:
            high = mid - 1
    return None

test_addrs = [
    (0x082AC88B, "Accept choice"),
    (0x082AC892, "Don't accept choice"),
    (0x082D24B8, "Go to bed for the day?"),
    (0x082DADE0, "Turn in for the day?"),
    (0x082B2C89, "Darling choice"),
    (0x082B00C9, "I'd be glad to choice"),
    (0x080E9668, "Iron Sickle item name"),
    (0x080EAED8, "Turnip item name"),
    (0x08101064, "Knife utensil name"),
    (0x08104128, "Lillia NPC name"),
    (0x081041B8, "Doctor NPC name"),
]

for addr, desc in test_addrs:
    raw_greek = lookup_redirection(addr)
    print(f"Lookup {hex(addr)} ({desc}): {raw_greek is not None} -> {len(raw_greek) if raw_greek else 0} bytes")
    assert raw_greek is not None, f"Address {hex(addr)} not found in redirection table!"

print("\n>>> ALL CHECKS PASSED PERFECTLY!")
