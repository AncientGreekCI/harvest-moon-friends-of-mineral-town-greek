# -*- coding: utf-8 -*-
import struct
from PIL import Image

rom = open('pilot.gba', 'rb').read()

GRID_OFF = 0x0E89B6
BASE_ADDR = 0x4F90CC
TABLE_OFF = 0x4FA7A0

# 6 rows of 15 characters, each cell is 8x12 pixels + spacing
# In game, cells are spaced with 8px horizontal, 16px vertical
W, H = 240, 160
img = Image.new('RGB', (W, H), (252, 238, 142)) # harvest moon yellow background
pixels = img.load()

# Read the 6 rows
rows = []
for r in range(6):
    row_bytes = rom[GRID_OFF + r*31 : GRID_OFF + (r+1)*31]
    # filter out spaces (step 2)
    chars = [row_bytes[i] for i in range(0, 30, 2)]
    rows.append(chars)

# Draw characters
# Grid start in original GBA screen: x = 12, y = 32
START_X = 12
START_Y = 32
CELL_DX = 15
CELL_DY = 18

for r_idx, row in enumerate(rows):
    y_pos = START_Y + r_idx * CELL_DY
    for c_idx, code in enumerate(row):
        x_pos = START_X + c_idx * CELL_DX
        if code == 0 or code == ord(' '):
            continue
        # Get glyph idx from 0x4FA7A0
        glyph_idx = struct.unpack_from('<h', rom, TABLE_OFF + code * 2)[0]
        if glyph_idx < 0: continue
        # Read 12 bytes of bitmap
        g_bytes = rom[BASE_ADDR + glyph_idx * 12 : BASE_ADDR + (glyph_idx + 1) * 12]
        for y in range(12):
            b = g_bytes[y]
            for x in range(8):
                if (b >> (7 - x)) & 1:
                    px = x_pos + x
                    py = y_pos + y
                    if 0 <= px < W and 0 <= py < H:
                        pixels[px, py] = (16, 16, 16) # black font

# Save preview
img.save('screenshots/rendered_keyboard_preview.png')
# Also save 2x scaled
img.resize((W*2, H*2), Image.NEAREST).save('screenshots/rendered_keyboard_preview_2x.png')
print("Successfully rendered keyboard preview from pilot.gba!")
