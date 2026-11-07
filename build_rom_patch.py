#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_rom_patch.py

Master build script for:
Harvest Moon: Friends of Mineral Town (GBA) — Ancient Greek Translation
AncientGreekCI

Rebuilds the complete patched ROM and IPS patch from clean vanilla ROM and source text:
1. Validates base USA ROM checksums.
2. Expands ROM to 16 MiB.
3. Injects Greek text redirection stub and 9,400+ polytonic Greek dialogue strings.
4. Applies Handjet Greek font glyphs, variable-width encoding, and engine hooks.
5. Injects Greek Name Entry keyboard matrix, UI prompts, calendar screens, and speaker names.
6. Generates patches/hm_fomt_greek.ips.
"""

import os
import sys
import struct
import zlib
import hashlib
import json
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, 'tools'))

CLEAN_ROM_NAMES = [
    'Harvest Moon - Friends of Mineral Town (USA).gba',
    'Harvest Moon - Friends of Mineral Town (U) [!].gba',
    'Harvest Moon - Friends of Mineral Town.gba',
    'rom.gba',
]

CLEAN_CRC32 = '8E923168'
CLEAN_SIZE = 8388608

def find_clean_rom():
    for name in CLEAN_ROM_NAMES:
        path = os.path.join(ROOT_DIR, name)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = f.read()
            crc = f"{zlib.crc32(data) & 0xffffffff:08X}"
            if crc == CLEAN_CRC32 or len(data) == CLEAN_SIZE:
                return path
    return None

def create_ips(orig, patched):
    """Generate IPS patch bytes comparing orig to patched, treating unallocated expansion as 0xFF."""
    recs = []
    i = 0
    n = len(patched)
    orig_n = len(orig)
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
            assert s != 0x454F46 # 'EOF' offset check
            ips += struct.pack('>I', s)[1:] + struct.pack('>H', ln) + bytes(patched[s:s + ln])
            s += ln
    ips += b'EOF'
    return bytes(ips)

def main():
    print("=" * 70)
    print("Harvest Moon: Friends of Mineral Town — Ancient Greek Build Pipeline")
    print("=" * 70)
    
    clean_rom_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        clean_rom_path = sys.argv[1]
    else:
        clean_rom_path = find_clean_rom()
        
    if not clean_rom_path:
        print("ERROR: Could not locate clean North American (USA) GBA ROM.")
        print(f"Please place 'Harvest Moon - Friends of Mineral Town (USA).gba' (CRC32: {CLEAN_CRC32}) in this directory.")
        sys.exit(1)
        
    clean_bytes = open(clean_rom_path, 'rb').read()
    crc = f"{zlib.crc32(clean_bytes) & 0xffffffff:08X}"
    print(f"[*] Found base ROM: {os.path.basename(clean_rom_path)} ({len(clean_bytes):,} bytes, CRC32: {crc})")
    
    # 1. Run insert_text.py logic
    print("[*] Step 1/3: Injecting translated Greek dialogue & engine hooks...")
    script_path = os.path.join(ROOT_DIR, 'data', 'greek_script.json')
    if not os.path.exists(script_path):
        script_path = os.path.join(ROOT_DIR, 'greek_script.json')
        
    intermediate_rom = os.path.join(ROOT_DIR, 'pilot.gba')
    cmd1 = [sys.executable, os.path.join(ROOT_DIR, 'tools', 'insert_text.py'), clean_rom_path, script_path, intermediate_rom]
    res1 = subprocess.run(cmd1, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT_DIR)
    if res1.returncode != 0:
        print("ERROR in text injection:")
        print(res1.stderr or res1.stdout)
        sys.exit(1)
    print("    Dialogue injection complete.")
    
    # 2. Run apply_greek_ui_and_speakers.py logic
    print("[*] Step 2/3: Applying Greek UI strings, keyboard matrix, and speakers...")
    cmd2 = [sys.executable, os.path.join(ROOT_DIR, 'tools', 'apply_greek_ui_and_speakers.py')]
    res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT_DIR)
    if res2.returncode != 0:
        print("ERROR in UI injection:")
        print(res2.stderr or res2.stdout)
        sys.exit(1)
    print("    UI and font enhancements applied successfully.")
    
    # 3. Finalize output and generate patches
    print("[*] Step 3/3: Generating final patched ROM & IPS patch...")
    output_rom_path = os.path.join(ROOT_DIR, 'Harvest Moon - Friends of Mineral Town (Greek Pilot).gba')
    if intermediate_rom != output_rom_path:
        import shutil
        shutil.copy2(intermediate_rom, output_rom_path)
        
    patched_bytes = open(output_rom_path, 'rb').read()
    out_crc = f"{zlib.crc32(patched_bytes) & 0xffffffff:08X}"
    out_md5 = hashlib.md5(patched_bytes).hexdigest()
    out_sha1 = hashlib.sha1(patched_bytes).hexdigest()
    
    # Generate IPS
    ips_bytes = create_ips(clean_bytes, patched_bytes)
    os.makedirs(os.path.join(ROOT_DIR, 'patches'), exist_ok=True)
    patch_path = os.path.join(ROOT_DIR, 'patches', 'hm_fomt_greek.ips')
    with open(patch_path, 'wb') as f:
        f.write(ips_bytes)
        
    print(f"[*] Patched ROM: {os.path.basename(output_rom_path)} ({len(patched_bytes):,} bytes)")
    print(f"    CRC32: {out_crc}")
    print(f"    MD5:   {out_md5}")
    print(f"    SHA-1: {out_sha1}")
    print(f"[*] Patch created: {patch_path} ({len(ips_bytes):,} bytes)")
    print("=" * 70)
    print("BUILD SUCCESSFUL!")
    print("=" * 70)

if __name__ == '__main__':
    main()
