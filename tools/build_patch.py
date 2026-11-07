import os
import struct, sys, unicodedata
from hmgreek import *
import glyphs
SRC = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('HM_ROM','Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba')
OUT_ROM = sys.argv[2] if len(sys.argv) > 2 else 'patched.gba'
OUT_IPS = sys.argv[3] if len(sys.argv) > 3 else 'hm_fomt_polytonic_v1glyphs.ips'
rom = bytearray(open(SRC, 'rb').read())
orig = bytes(rom)
assert len(rom) == 0x800000 and rom[0xAC:0xB0] == b'A4NE'
T = 0x4FA7A0
def rom_glyph(c):
    i = struct.unpack_from('<h', orig, T + 2 * ord(c))[0]
    return [format(b, '08b').replace('0', '.').replace('1', '#') for b in orig[BASE_ADDR + i * 12: BASE_ADDR + i * 12 + 12]]
glyphs.LOW_LATIN = {}
# ---- glyph set
G = {}
for cp in list(range(0x370, 0x400)) + list(range(0x1F00, 0x2000)):
    ch = chr(cp)
    if unicodedata.category(ch) not in ('Ll', 'Lu', 'Lt'): continue
    g = glyphs.build_glyph(ch, rom_glyph)
    if g: G[cp] = g
# ano teleia (middle dot) U+0387
G[0x387] = ['........'] * 6 + ['...##...', '...##...'] + ['........'] * 4
print('glyphs defined:', len(G))
# ---- thumb helpers
def bl(at, target):
    off = target - (at + 4)
    assert off % 2 == 0 and -(1 << 22) <= off < (1 << 22)
    hi = 0xF000 | ((off >> 12) & 0x7FF)
    lo = 0xF800 | ((off >> 1) & 0x7FF)
    return struct.pack('<HH', hi, lo)
def hw(*v): return b''.join(struct.pack('<H', x) for x in v)
# ---- patch 1: default width register r6 = 2 (movs r6,#2) instead of #0
assert rom[0xD0D2E:0xD0D30] == b'\x00\x26'
rom[0xD0D2E:0xD0D30] = b'\x02\x26'
# ---- patch 2: 28 bytes at 0xD0E3C
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
assert len(new) == 28
assert struct.unpack_from('<I', rom, 0xD0E7C)[0] == 0x08523290
rom[A:A + 28] = new
# ---- glyph data
free_lo = 0x75C244
for cp, g in G.items():
    c = code_of(cp); a = glyph_addr(c)
    assert a >= free_lo and a + 12 <= 0x800000
    assert all(b == 0xFF for b in orig[a:a + 12])
    rom[a:a + 12] = glyphs.rows_to_bytes(g)
# ---- test string over Mother's first line (0xFB23C .. 0xFB27B)
PAGES = [
 'α ἀ ἁ  ε ἐ ἑ  η ἠ ἡ\nι ἰ ἱ  ο ὀ ὁ  υ ὐ ὑ\nω ὠ ὡ  ρ ῥ  ᾳ ῃ ῳ',
 'ά ὰ ᾶ  έ ὲ  ή ὴ ῆ\nί ὶ ῖ  ό ὸ  ύ ὺ ῦ\nώ ὼ ῶ  ϊ ΐ ῒ ῗ  ϋ ΰ',
 'ἄ ἂ ἆ ἅ ἃ ἇ\nἔ ἒ ἕ ἓ  ἤ ἢ ἦ\nἥ ἣ ἧ  ἴ ἲ ἶ ἵ ἳ ἷ',
 'ὄ ὂ ὅ ὃ  ὔ ὒ ὖ\nὕ ὓ ὗ  ὤ ὢ ὦ\nὥ ὣ ὧ  ῤ ῥ',
 'ᾳ ᾴ ᾲ ᾷ  ᾀ ᾁ ᾄ ᾅ ᾆ ᾇ\nῃ ῄ ῂ ῇ  ᾐ ᾑ ᾔ ᾕ ᾖ ᾗ\nῳ ῴ ῲ ῷ  ᾠ ᾡ ᾤ ᾥ ᾦ ᾧ',
 'Ἀ Ἁ Ἄ Ἅ Ἆ Ἇ  Ἐ Ἑ Ἔ Ἕ\nἘ Ἠ Ἡ Ἤ Ἥ Ἦ Ἧ  Ἰ Ἱ Ἴ Ἵ\nὈ Ὁ Ὄ Ὅ  Ὑ Ὕ Ὠ Ὡ Ὤ Ὥ',
 'Ά Έ Ή Ί Ό Ύ Ώ Ϊ Ϋ\nᾼ ῌ ῼ  Ἶ Ἷ Ὦ Ὧ\nΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ',
 'αβγδεζηθικλμνξοπρσςτυφχψω\nἐν ἀρχῇ ἦν ὁ λόγος,\nκαὶ θεὸς ἦν ὁ λόγος.',
]
def cells(b):
    n = 0; i = 0
    while i < len(b):
        n += 1; i += 2 if 0xE0 <= b[i] <= 0xE3 else 1
    return n
for p in PAGES:
    for ln in p.split('\n'): assert len(ln) <= 28 and ln.count('\n') == 0, (ln, len(ln))
    assert p.count('\n') <= 2
import os
TESTMODE = os.environ.get('HM_TEST') == '1'
test = encode('\f'.join(PAGES))
if TESTMODE:
    TEXT_AT = 0x7F0000
    assert all(x == 0xFF for x in orig[TEXT_AT:TEXT_AT + len(test) + 4])
    rom[TEXT_AT:TEXT_AT + len(test) + 1] = test + b'\x00'
    # repoint the Mother opening line (0x080FB23C) to the test pages
    refs = [p for p in range(0, len(orig) - 3, 4) if struct.unpack_from('<I', orig, p)[0] == 0x080FB23C]
    print('refs to Mother line:', [hex(r) for r in refs])
    for r in refs: struct.pack_into('<I', rom, r, 0x08000000 + TEXT_AT)
print('test pages included:', TESTMODE)
open(OUT_ROM, 'wb').write(rom)
# ---- IPS
recs = []; i = 0; n = len(rom)
while i < n:
    if rom[i] != orig[i]:
        j = i
        while j < n and (rom[j] != orig[j] or (j + 1 < n and rom[j + 1] != orig[j + 1] and j - i < 0x100)): j += 1
        # extend over short unchanged gaps
        recs.append([i, j]); i = j
    else: i += 1
merged = []
for s, e in recs:
    if merged and s - merged[-1][1] <= 8: merged[-1][1] = e
    else: merged.append([s, e])
ips = bytearray(b'PATCH')
for s, e in merged:
    while e - s > 0:
        ln = min(e - s, 0xFFFF)
        assert s != 0x454F46
        ips += struct.pack('>I', s)[1:] + struct.pack('>H', ln) + bytes(rom[s:s + ln]); s += ln
ips += b'EOF'
open(OUT_IPS, 'wb').write(ips)
print('IPS records:', len(merged), 'size', len(ips))
# ---- glyph sheet
def sheet(cps, path):
    with open(path, 'w', encoding='utf-8') as f:
        for cp in cps:
            if cp in G:
                f.write('U+%04X %s  code %04X  @%06X\n' % (cp, chr(cp), code_of(cp), glyph_addr(code_of(cp))))
                f.write('\n'.join('  |' + r + '|' for r in G[cp]) + '\n')
sheet(sorted(G), 'glyph_sheet.txt')
