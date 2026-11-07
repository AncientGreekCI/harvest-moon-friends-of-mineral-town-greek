import os
import struct
from PIL import Image

with open('Harvest Moon - Friends of Mineral Town (USA).gba', 'rb') as f:
    rom = f.read()

res_base = 0x6678a0
t1_off = 0x66805c
t3_tiles_off = 0x66a2cc
t4_pals_off = 0x676dd0

crops = [
    ("turnip", 0x1cf),
    ("turnip_seeds", 0x1d0),
    ("potato", 0x150),
    ("potato_seeds", 0x151),
    ("cucumber", 0x75),
    ("cucumber_seeds", 0x76),
    ("strawberry", 0x1b3),
    ("strawberry_seeds", 0x1b6),
    ("cabbage", 0x58),
    ("cabbage_seeds", 0x59),
    ("tomato", 0x1c6),
    ("tomato_seeds", 0x1c8),
    ("corn", 0x71),
    ("corn_seeds", 0x73),
    ("onion", 0x132),
    ("onion_seeds", 0x133),
    ("pumpkin", 0x157),
    ("pumpkin_seeds", 0x159),
    ("pineapple", 0x143),
    ("pineapple_seeds", 0x144),
    ("eggplant", 0x88),
    ("eggplant_seeds", 0x8a),
    ("carrot", 0x5d),
    ("carrot_seeds", 0x5e),
    ("sweet_potato", 0x1bd),
    ("sweet_potato_seeds", 0x1be),
    ("spinach", 0x1a7),
    ("spinach_seeds", 0x1a8),
    ("green_pepper", 0xca),
    ("green_pepper_seeds", 0xcb),
]

os.makedirs('sprites/crops_original', exist_ok=True)

def bgr555_to_rgb(val):
    r = (val & 0x1F) << 3
    g = ((val >> 5) & 0x1F) << 3
    b = ((val >> 10) & 0x1F) << 3
    return (r, g, b)

def decode_tile(data, off):
    pixels = bytearray(64)
    for y in range(8):
        for x in range(0, 8, 2):
            b = data[off + y * 4 + x // 2]
            pixels[y * 8 + x] = b & 0x0F
            pixels[y * 8 + x + 1] = (b >> 4) & 0x0F
    return pixels

def decode_16x16(data, tile_base_off):
    # 4 tiles in 1D order: TL, TR, BL, BR
    tl = decode_tile(data, tile_base_off)
    tr = decode_tile(data, tile_base_off + 32)
    bl = decode_tile(data, tile_base_off + 64)
    br = decode_tile(data, tile_base_off + 96)
    
    out = bytearray(256)
    for y in range(8):
        for x in range(8):
            out[y * 16 + x] = tl[y * 8 + x]
            out[y * 16 + (x + 8)] = tr[y * 8 + x]
            out[(y + 8) * 16 + x] = bl[y * 8 + x]
            out[(y + 8) * 16 + (x + 8)] = br[y * 8 + x]
    return out

print("Exporting crops and seeds...")
crop_details = []

for name, t1_idx in crops:
    entry_addr = t1_off + t1_idx * 16
    entry = rom[entry_addr : entry_addr + 16]
    f_count, pal_idx, tile_count, tile_idx = struct.unpack('<HHHH', entry[:8])
    
    # Palette at t4_pals_off + pal_idx * 32
    pal_addr = t4_pals_off + pal_idx * 32
    raw_pal = struct.unpack('<16H', rom[pal_addr : pal_addr + 32])
    rgb_pal = []
    for c in raw_pal:
        rgb_pal.extend(bgr555_to_rgb(c))
    
    # Tiles at t3_tiles_off + tile_idx * 32
    tile_addr = t3_tiles_off + tile_idx * 32
    sprite_data = decode_16x16(rom, tile_addr)
    
    img = Image.new('P', (16, 16))
    img.putpalette(rgb_pal)
    px = img.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = sprite_data[y * 16 + x]
    
    # Save indexed 16x16 PNG
    out_16 = f'sprites/crops_original/{name}.png'
    img.save(out_16)
    
    # Also save an 8x scaled version for easy viewing
    img_large = img.resize((128, 128), Image.NEAREST)
    img_large.save(f'sprites/crops_original/{name}_x8.png')
    
    crop_details.append({
        'name': name,
        't1_idx': t1_idx,
        'pal_idx': pal_idx,
        'pal_addr': hex(pal_addr),
        'tile_idx': tile_idx,
        'tile_addr': hex(tile_addr),
    })
    print(f"Exported {name:20s}: tile={hex(tile_addr)} (idx {hex(tile_idx)}), pal={hex(pal_addr)} (idx {hex(pal_idx)})")

# Also render an all-in-one preview sheet of all 30 items
preview = Image.new('RGB', (16 * 10, 16 * 3), (240, 240, 240))
for i, item in enumerate(crop_details):
    img = Image.open(f"sprites/crops_original/{item['name']}.png").convert('RGBA')
    col = i % 10
    row = i // 10
    # Paste with transparency (color 0 transparent)
    preview.paste(img, (col * 16, row * 16), img)

preview_scaled = preview.resize((preview.width * 4, preview.height * 4), Image.NEAREST)
preview_scaled.save('sprites/crops_original/crops_all_preview.png')
print("Saved all-in-one preview: sprites/crops_original/crops_all_preview.png")
