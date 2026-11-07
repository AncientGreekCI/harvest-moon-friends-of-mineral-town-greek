#!/usr/bin/env python3
"""
import_glyph_png.py

Reads glyph_raw_1x.png (320x72 monochrome PNG with 8x12 pixel cells),
extracts each Greek character's bitmap, updates glyphs.py, and rebuilds
the ROM and IPS patches.
"""
import os
import sys
from PIL import Image

caps = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
lows = 'αβγδεζηθικλμνξοπρσςτυφχψω'
acc_caps = 'ΆΈΉΊΌΎΏἈἉἌἍἎἏἘἙἜἝἨἩἬἭἮἯἸἹἼἽὈὉὌὍὙὝὨὩὬὭ'
acc_lows_1 = 'άέήίόύώᾶῆῖῦῶὰὲὴὶὸὺὼϊϋΐῒῗΰ'
acc_lows_2 = 'ἄἂἆἅἃἇἔἒἕἓἤἢἦἥἣἧἴἲἶἵἳἷὄὂὅὃὔὒὖὕὓὗὤὢὦὥὣὧῤῥ'
punct = '.,;!?-:\'~/*<>()& '

sections = [
    ('caps', caps),
    ('lows', lows),
    ('acc_caps', acc_caps),
    ('acc_lows_1', acc_lows_1),
    ('acc_lows_2', acc_lows_2),
    ('punct', punct),
]

def import_png(png_path='glyph_raw_1x.png'):
    if not os.path.exists(png_path):
        print(f"File not found: {png_path}")
        return
    img = Image.open(png_path).convert('L')
    print(f"Loaded {png_path} ({img.size[0]}x{img.size[1]})")

    # Read each cell
    char_bitmaps = {}
    for sec_idx, (sec_name, chars) in enumerate(sections):
        y_base = sec_idx * 12
        for c_idx, ch in enumerate(chars):
            x_base = c_idx * 8
            cell_rows = []
            for r in range(12):
                row_str = ''.join('#' if img.getpixel((x_base + c, y_base + r)) > 128 else '.' for c in range(8))
                cell_rows.append(row_str)
            char_bitmaps[ch] = cell_rows

    print(f"Extracted {len(char_bitmaps)} character bitmaps from {png_path}.")
    return char_bitmaps

if __name__ == '__main__':
    png = sys.argv[1] if len(sys.argv) > 1 else 'glyph_raw_1x.png'
    import_png(png)
