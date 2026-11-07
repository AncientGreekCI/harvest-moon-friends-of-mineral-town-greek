"""insert_crop_sprites.py - Injects historical biblical produce sprites and palettes into FoMT.

Replaces original crops with historical equivalents:
  Spring:
    Turnip       -> Garlic (σκόρδον)
    Potato       -> Lentils (φακός)
    Cucumber     -> Kept (σίκυς)
    Strawberry   -> Mulberry (συκάμινον)
    Cabbage      -> Melon (πέπων)
  Summer:
    Tomato       -> Fig (σῦκον)
    Corn         -> Wheat (σῖτος)
    Onion        -> Kept (κρόμμυον)
    Pumpkin      -> Gourd (κολοκύνθη)
    Pineapple    -> Pomegranate (ῥόα)
  Fall:
    Eggplant     -> Olive (ἐλαία)
    Carrot       -> Leek (πράσον)
    Sweet Potato -> Beans (κύαμος)
    Spinach      -> Mint (ἡδύοσμον)
    Green Pepper -> Coriander (κορίανον)
"""

import os
import struct
import sys
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hm_greek_handover_package', 'tools'))
import hmgreek

# Table addresses in FoMT USA:
T1_OFF = 0x66805c
T3_TILES_OFF = 0x66a2cc
T4_PALS_OFF = 0x676dd0
PRODUCE_TABLE_OFF = 0xedcd8
SEED_TABLE_OFF = 0xead64
FREE_STRINGS_OFF = 0x780000  # Safe free space in lower free region (0x75C244 - 0x799AEC)

# Replacement configuration
# (crop_name, t1_idx, tile_idx, assigned_pal_idx, png_file, greek_name, produce_id, seed_id, season)
REPLACEMENTS = [
    {
        "name": "garlic",
        "t1_idx": 0x1cf,
        "tile_idx": 0x60e,
        "pal_idx": 35,
        "file": "garlic.png",
        "greek": "σκόρδον",
        "desc": "σκόρδον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα σκόρδου",
        "seed_desc": "σπέρματα σκόρδου\r\nσπεῖρον ἐν ἦρι.\r\n",
        "produce_id": 0,
        "seed_id": 0,
    },
    {
        "name": "lentils",
        "t1_idx": 0x150,
        "tile_idx": 0x3e7,
        "pal_idx": 36,
        "file": "lentils.png",
        "greek": "φακός",
        "desc": "φακός\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα φακοῦ",
        "seed_desc": "σπέρματα φακοῦ\r\nσπεῖρον ἐν ἦρι.\r\n",
        "produce_id": 1,
        "seed_id": 1,
    },
    {
        "name": "beans",
        "t1_idx": 0x1bd,
        "tile_idx": 0x5de,
        "pal_idx": 37,
        "file": "beans.png",
        "greek": "κύαμος",
        "desc": "κύαμος\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα κυάμου",
        "seed_desc": "σπέρματα κυάμου\r\nσπεῖρον ἐν φθινοπώρῳ.\r\n",
        "produce_id": 12,
        "seed_id": 12,
    },
    {
        "name": "melon",
        "t1_idx": 0x58,
        "tile_idx": 0x139,
        "pal_idx": 38,
        "file": "melon.png",
        "greek": "πέπων",
        "desc": "πέπων\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα πέπονος",
        "seed_desc": "σπέρματα πέπονος\r\nσπεῖρον ἐν ἦρι.\r\n",
        "produce_id": 4,
        "seed_id": 4,
    },
    {
        "name": "mulberry",
        "t1_idx": 0x1b3,
        "tile_idx": 0x5aa,
        "pal_idx": 39,
        "file": "mulberry.png",
        "greek": "συκάμινον",
        "desc": "συκάμινον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα συκαμίνου",
        "seed_desc": "σπέρματα συκαμίνου\r\nσπεῖρον ἐν ἦρι.\r\n",
        "produce_id": 3,
        "seed_id": 3,
    },
    {
        "name": "fig",
        "t1_idx": 0x1c6,
        "tile_idx": 0x5fe,
        "pal_idx": 41,
        "file": "fig.png",
        "greek": "σῦκον",
        "desc": "σῦκον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα σύκου",
        "seed_desc": "σπέρματα σύκου\r\nσπεῖρον ἐν θέρει.\r\n",
        "produce_id": 5,
        "seed_id": 5,
    },
    {
        "name": "wheat",
        "t1_idx": 0x71,
        "tile_idx": 0x191,
        "pal_idx": 42,
        "file": "wheat.png",
        "greek": "σῖτος",
        "desc": "σῖτος\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα σίτου",
        "seed_desc": "σπέρματα σίτου\r\nσπεῖρον ἐν θέρει.\r\n",
        "produce_id": 6,
        "seed_id": 6,
    },
    {
        "name": "pomegranate",
        "t1_idx": 0x143,
        "tile_idx": 0x3c7,
        "pal_idx": 43,
        "file": "pomegranate.png",
        "greek": "ῥόα",
        "desc": "ῥόα\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα ῥόας",
        "seed_desc": "σπέρματα ῥόας\r\nσπεῖρον ἐν θέρει.\r\n",
        "produce_id": 9,
        "seed_id": 9,
    },
    {
        "name": "gourd",
        "t1_idx": 0x157,
        "tile_idx": 0x3fb,
        "pal_idx": 44,
        "file": "gourd.png",
        "greek": "κολοκύνθη",
        "desc": "κολοκύνθη\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα κολοκύνθης",
        "seed_desc": "σπέρματα κολοκύνθης\r\nσπεῖρον ἐν θέρει.\r\n",
        "produce_id": 8,
        "seed_id": 8,
    },
    {
        "name": "olive",
        "t1_idx": 0x88,
        "tile_idx": 0x1d1,
        "pal_idx": 45,
        "file": "olive.png",
        "greek": "ἐλαία",
        "desc": "ἐλαία\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα ἐλαίας",
        "seed_desc": "σπέρματα ἐλαίας\r\nσπεῖρον ἐν φθινοπώρῳ.\r\n",
        "produce_id": 10,
        "seed_id": 10,
    },
    {
        "name": "leek",
        "t1_idx": 0x5d,
        "tile_idx": 0x14d,
        "pal_idx": 49,
        "file": "leek.png",
        "greek": "πράσον",
        "desc": "πράσον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα πράσου",
        "seed_desc": "σπέρματα πράσου\r\nσπεῖρον ἐν φθινοπώρῳ.\r\n",
        "produce_id": 11,
        "seed_id": 11,
    },
    {
        "name": "mint",
        "t1_idx": 0x1a7,
        "tile_idx": 0x58e,
        "pal_idx": 50,
        "file": "mint.png",
        "greek": "ἡδύοσμον",
        "desc": "ἡδύοσμον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα ἡδυόσμου",
        "seed_desc": "σπέρματα ἡδυόσμου\r\nσπεῖρον ἐν φθινοπώρῳ.\r\n",
        "produce_id": 13,
        "seed_id": 13,
    },
    {
        "name": "coriander",
        "t1_idx": 0xca,
        "tile_idx": 0x285,
        "pal_idx": 52,
        "file": "coriander.png",
        "greek": "κορίανον",
        "desc": "κορίανον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n",
        "seed_greek": "σπέρματα κοριάνου",
        "seed_desc": "σπέρματα κοριάνου\r\nσπεῖρον ἐν φθινοπώρῳ.\r\n",
        "produce_id": 14,
        "seed_id": 14,
    },
]

def rgb_to_bgr555(r, g, b):
    return ((r >> 3) & 0x1F) | (((g >> 3) & 0x1F) << 5) | (((b >> 3) & 0x1F) << 10)

def encode_tile_4bpp(pixels, start_x, start_y):
    tile_bytes = bytearray(32)
    for y in range(8):
        for x in range(0, 8, 2):
            p0 = pixels[start_x + x, start_y + y] & 0x0F
            p1 = pixels[start_x + x + 1, start_y + y] & 0x0F
            tile_bytes[y * 4 + x // 2] = p0 | (p1 << 4)
    return tile_bytes

def encode_16x16_sprite(img):
    px = img.load()
    tl = encode_tile_4bpp(px, 0, 0)
    tr = encode_tile_4bpp(px, 8, 0)
    bl = encode_tile_4bpp(px, 0, 8)
    br = encode_tile_4bpp(px, 8, 8)
    return tl + tr + bl + br

def patch_rom(rom_path, out_path, sprites_dir='sprites/crops_historical'):
    with open(rom_path, 'rb') as f:
        rom = bytearray(f.read())
        
    print(f"Loaded ROM: {rom_path} ({len(rom)} bytes)")
    
    # Cursor for storing new Greek text strings in free space
    str_cursor = FREE_STRINGS_OFF
    
    def alloc_string(text):
        nonlocal str_cursor
        encoded = hmgreek.encode(text, box=False, end=False) + b'\x00'
        # Align to 4 bytes
        while str_cursor % 4 != 0:
            str_cursor += 1
        addr = str_cursor
        rom[addr : addr + len(encoded)] = encoded
        str_cursor += len(encoded)
        return 0x08000000 + addr
    
    for item in REPLACEMENTS:
        png_path = os.path.join(sprites_dir, item['file'])
        if not os.path.exists(png_path):
            print(f"Warning: {png_path} not found, skipping!")
            continue
            
        img = Image.open(png_path)
        assert img.size == (16, 16), f"{png_path} must be 16x16!"
        
        # 1. Palette conversion
        raw_pal = img.getpalette()[:48]
        pal_bytes = bytearray(32)
        for i in range(16):
            r = raw_pal[i * 3]
            g = raw_pal[i * 3 + 1]
            b = raw_pal[i * 3 + 2]
            c16 = rgb_to_bgr555(r, g, b) if i > 0 else 0x0000
            pal_bytes[i*2 : i*2+2] = struct.pack('<H', c16)
            
        # Write palette into Table 4 slot
        pal_dest = T4_PALS_OFF + item['pal_idx'] * 32
        rom[pal_dest : pal_dest + 32] = pal_bytes
        
        # 2. Update Table 1 palette index
        t1_dest = T1_OFF + item['t1_idx'] * 16 + 2
        rom[t1_dest : t1_dest + 2] = struct.pack('<H', item['pal_idx'])
        
        # 3. Sprite tiles conversion
        tile_bytes = encode_16x16_sprite(img)
        tile_dest = T3_TILES_OFF + item['tile_idx'] * 32
        rom[tile_dest : tile_dest + 128] = tile_bytes
        
        # 4. Greek Name and Description for Produce item
        name_ptr = alloc_string(item['greek'])
        desc_ptr = alloc_string(item['desc'])
        p_record = PRODUCE_TABLE_OFF + item['produce_id'] * 16
        rom[p_record : p_record + 4] = struct.pack('<I', name_ptr)
        rom[p_record + 12 : p_record + 16] = struct.pack('<I', desc_ptr)
        
        # 5. Greek Name and Description for Seed item
        seed_name_ptr = alloc_string(item['seed_greek'])
        seed_desc_ptr = alloc_string(item['seed_desc'])
        s_record = SEED_TABLE_OFF + item['seed_id'] * 12
        rom[s_record : s_record + 4] = struct.pack('<I', seed_name_ptr)
        rom[s_record + 8 : s_record + 12] = struct.pack('<I', seed_desc_ptr)
        
        print(f"Injected {item['name']:12s} ({item['greek']}): tiles -> {hex(tile_dest)}, pal[{item['pal_idx']}] -> {hex(pal_dest)}, name_ptr -> {hex(name_ptr)}")

    # Also update Kept crops (Cucumber and Onion) names to Ancient Greek
    kept_items = [
        {"id": 2, "name": "σίκυς", "desc": "σίκυς\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n", "seed_id": 2, "seed_name": "σπέρματα σίκυος", "seed_desc": "σπέρματα σίκυος\r\nσπεῖρον ἐν ἦρι.\r\n"},
        {"id": 7, "name": "κρόμμυον", "desc": "κρόμμυον\r\nφαγεῖν ἢ πέμψαι ἔξεστιν.\r\n", "seed_id": 7, "seed_name": "σπέρματα κρομμύου", "seed_desc": "σπέρματα κρομμύου\r\nσπεῖρον ἐν θέρει.\r\n"}
    ]
    for k in kept_items:
        np = alloc_string(k['name'])
        dp = alloc_string(k['desc'])
        p_record = PRODUCE_TABLE_OFF + k['id'] * 16
        rom[p_record : p_record + 4] = struct.pack('<I', np)
        rom[p_record + 12 : p_record + 16] = struct.pack('<I', dp)
        
        snp = alloc_string(k['seed_name'])
        sdp = alloc_string(k['seed_desc'])
        s_record = SEED_TABLE_OFF + k['seed_id'] * 12
        rom[s_record : s_record + 4] = struct.pack('<I', snp)
        rom[s_record + 8 : s_record + 12] = struct.pack('<I', sdp)
        print(f"Updated kept crop {k['name']}: name_ptr -> {hex(np)}")

    print(f"Free space used for Greek item strings: {str_cursor - FREE_STRINGS_OFF} bytes (at {hex(FREE_STRINGS_OFF)} - {hex(str_cursor)})")

    with open(out_path, 'wb') as f:
        f.write(rom)
    print(f"Successfully wrote patched ROM to {out_path} ({len(rom)} bytes)")

    # Generate updated IPS patch against clean USA ROM
    clean_rom_path = 'Harvest Moon - Friends of Mineral Town (USA).gba'
    if os.path.exists(clean_rom_path):
        clean_rom = open(clean_rom_path, 'rb').read()
        recs = []; i = 0; n = len(rom); clean_n = len(clean_rom)
        while i < n:
            o_val = clean_rom[i] if i < clean_n else 0xFF
            if rom[i] != o_val:
                j = i
                while j < n and (rom[j] != (clean_rom[j] if j < clean_n else 0xFF) or (j + 1 < n and rom[j + 1] != (clean_rom[j + 1] if j + 1 < clean_n else 0xFF) and j - i < 0x100)):
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
                ips += struct.pack('>I', s)[1:] + struct.pack('>H', ln) + bytes(rom[s:s + ln])
                s += ln
        ips += b'EOF'
        ips_path = 'hm_greek_handover_package/patches/hm_fomt_greek_pilot.ips'
        os.makedirs(os.path.dirname(ips_path), exist_ok=True)
        with open(ips_path, 'wb') as f:
            f.write(ips)
        print(f"Generated IPS patch: {ips_path} ({len(ips)} bytes)")

if __name__ == '__main__':
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    src = sys.argv[1] if len(sys.argv) > 1 else 'Harvest Moon - Friends of Mineral Town (Greek Pilot).gba'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'Harvest Moon - Friends of Mineral Town (Greek Pilot).gba'
    patch_rom(src, dst)
