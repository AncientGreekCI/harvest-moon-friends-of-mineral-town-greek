"""Polytonic Greek encoding + glyph set for Harvest Moon: FoMT (USA) - Ancient Greek project.
Encoding: Greek & Coptic U+0370-03FF -> lead 0xE0, second = 0x20 + (cp-0x370)
          Greek Extended U+1F00-1FFF  -> n=cp-0x1F00, lead = 0xE1 + n//224, second = 0x20 + n%224
Everything else (space, ASCII punctuation, digits) stays single-byte ASCII."""
import unicodedata

BASE_ADDR = 0x4F90CC      # half-width glyph array base (code uses 12-byte stride)
def code_of(cp):
    if 0x370 <= cp <= 0x3FF:
        return (0xE0 << 8) | (0x20 + cp - 0x370)
    if 0x1F00 <= cp <= 0x1FFF:
        n = cp - 0x1F00
        return ((0xE1 + n // 224) << 8) | (0x20 + n % 224)
    return None
def glyph_addr(code):      # patched routine: r5 = code<<2, address = BASE + r5*12
    return BASE_ADDR + 48 * code

def encode(text, box=True, end=True):
    """Unicode (NFC or NFD) Greek text -> game bytes. '\n' -> CRLF line break, '\f' -> new box."""
    text = unicodedata.normalize('NFC', text)
    out = bytearray()
    if box: out.append(0x0C)
    for ch in text:
        if ch == '\n': out += b'\r\n'
        elif ch == '\f': out += b'\x05\x0c'
        else:
            c = code_of(ord(ch))
            if c is not None: out += bytes([c >> 8, c & 0xFF])
            elif ord(ch) < 0x80: out.append(ord(ch))
            else: raise ValueError('unsupported char %r U+%04X' % (ch, ord(ch)))
    if end: out.append(0x05)
    return bytes(out)


import re
PUNCT = {'\u00b7': '\u0387', '\u037e': ';', '\u201c': '"', '\u201d': '"', '\u00ab': '"', '\u00bb': '"',
         '\u2018': "'", '\u2019': "'", '\u02bc': "'", '\u2014': '-', '\u2013': '-', '\u2026': '...',
         '\u00a0': ' ', '\u1fbd': "'", '\u1fbf': "'"}
def normalize(text):
    """NFC + map typographic punctuation to what the font has"""
    text = unicodedata.normalize('NFC', text)
    return ''.join(PUNCT.get(c, c) for c in text)
import json as _json, os as _os
_p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'supported.json')
SUPPORTED = set(_json.load(open(_p))) if _os.path.exists(_p) else None
TOKEN = re.compile(r'\{N:(.)\}')
def cell_width(s, name_cells=6):
    """cells used by a line (a name-insert token is reserved name_cells wide)"""
    s = TOKEN.sub('N' * name_cells, s)
    return len(s)
def encode_line(s):
    out = bytearray(); i = 0
    while i < len(s):
        m = TOKEN.match(s, i)
        if m: out += bytes([0xFF, ord(m.group(1))]); i = m.end(); continue
        ch = s[i]; c = code_of(ord(ch))
        if c is not None:
            if SUPPORTED is not None and ord(ch) not in SUPPORTED: raise ValueError('no glyph for %r U+%04X' % (ch, ord(ch)))
            out += bytes([c >> 8, c & 0xFF])
        elif 0x20 <= ord(ch) < 0x7F: out.append(ord(ch))
        else: raise ValueError('unsupported char %r U+%04X' % (ch, ord(ch)))
        i += 1
    return bytes(out)
