"""Glyph designs: 8 px wide x 12 rows, 1bpp. Rows are listed as 8-char strings ('#' = pixel).
Custom letters are drawn in cols 1-6 (modular element-based design inspired by Handjet).
Caps occupy rows 0-9, lowercase x-height rows 3-9, descenders rows 10-11, ascenders rows 1-2."""
import unicodedata

def rows_to_bytes(rows):
    assert len(rows) == 12
    return bytes(int(r.replace('#','1').replace('.','0'), 2) for r in rows)

def pad(top, lines):
    """place 3-7 char lines at row `top` with col 0 (or col 7 for 7-wide) empty sidebearing"""
    g = ['........'] * 12
    for i, l in enumerate(lines):
        if len(l) == 7:
            g[top + i] = (l + '.')[:8]
        elif len(l) <= 3:
            g[top + i] = ('..' + l + '........')[:8]
        else:
            g[top + i] = ('.' + l + '........')[:8]
    return g

LOW = {  # (top_row, lines) - Authentic Handjet Regular modular pixel grids adapted to 8x12
 'α': (3, ['.##.#.','#..##.','#...#.','#...#.','#...#.','#..##.','.##..#']),
 'β': (1, ['.###.','#...#','#...#','####.','#...#','#...#','##..#','#.##.','#....','#....','#....']),
 'γ': (3, ['#...#','#...#','#...#','.#..#','.#.#.','..##.','..#..','..#..','..#..']),
 'δ': (1, ['.####','#....','.#...','..#..','.#.#.','#...#','#...#','#...#','.###.']),
 'ε': (3, ['.###.','#...#','#....','.###.','#....','#...#','.###.']),
 'ζ': (1, ['####..','....#.','...#..','..#...','.#....','.#....','.#....','..###.','.....#','.....#','...##.']),
 'η': (3, ['#..##.','.##..#','.#...#','.#...#','.#...#','.#...#','.#...#','.....#','.....#']),
 'θ': (1, ['.###.','#...#','#...#','#####','#...#','#...#','#...#','#...#','.###.']),
 'ι': (3, ['##.','.#.','.#.','.#.','.#.','.#.','..#']),
 'κ': (3, ['#...#','#..#.','#..#.','###..','#..#.','#..#.','#...#']),
 'λ': (1, ['###....','...#...','....#..','...##..','...#.#.','..#..#.','..#...#','..#...#','..#...#']),
 'μ': (3, ['#...#','#...#','#...#','#...#','##.##','#.#.#','#....','#....','#....']),
 'ν': (3, ['#...#','#...#','#...#','#...#','.#..#','.#.#.','..##.']),
 'ξ': (1, ['####..','....#.','...#..','..#...','.#....','..###.','.#....','..###.','.....#','.....#','...##.']),
 'ο': (3, ['.###.','#...#','#...#','#...#','#...#','#...#','.###.']),
 'π': (3, ['#######','.#...#.','.#...#.','.#...#.','.#...#.','.#...#.','.#....#']),
 'ρ': (3, ['.###.','#...#','#...#','#...#','##..#','#.##.','#....','#....','#....']),
 'σ': (3, ['.#####','#..#..','#...#.','#...#.','#...#.','#...#.','.###..']),
 'ς': (3, ['.###.','#...#','#....','#....','#....','#....','.###.','....#','..##.']),
 'τ': (3, ['#####','..#..','..#..','..#..','..#..','..#..','...#.']),
 'υ': (3, ['#...#','#...#','#...#','#...#','#...#','#...#','.###.']),
 'φ': (3, ['.#..##.','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','.#####.','...#...','...#...']),
 'χ': (3, ['#....#','.#...#','.#..#.','..#.#.','..##..','..#.#.','.#..#.','.#...#','#....#']),
 'ψ': (1, ['...#...','...#...','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','.#####.','...#...','...#...']),
 'ω': (3, ['.#...#.','#.....#','#..#..#','#..#..#','#..#..#','#..#..#','.##.##.']),
}

CAP = {  # 10-row caps (rows 0-9) - Authentic Handjet Regular modular pixel grids adapted to 8x12
 'Α': ['..#..','.#.#.','.#.#.','#...#','#...#','#...#','#####','#...#','#...#','#...#'],
 'Β': ['####.','#...#','#...#','#...#','####.','#...#','#...#','#...#','#...#','####.'],
 'Γ': ['####'] + ['#...']*9,
 'Δ': ['..#..','.###.','.#.#.','#...#','#...#','#...#','#...#','#...#','#...#','#####'],
 'Ε': ['####','#...','#...','#...','####','#...','#...','#...','#...','####'],
 'Ζ': ['######','#....#','....#.','....#.','...#..','...#..','..#...','.#....','.#...#','######'],
 'Η': ['#...#','#...#','#...#','#...#','#####','#...#','#...#','#...#','#...#','#...#'],
 'Θ': ['.###.','#...#','#...#','#...#','#.#.#','#...#','#...#','#...#','#...#','.###.'],
 'Ι': ['###'] + ['.#.']*8 + ['###'],
 'Κ': ['#....#','#...#.','#...#.','#..#..','###...','#..#..','#..#..','#...#.','#...#.','#....#'],
 'Λ': ['..#..','.#.#.','.#.#.','#...#','#...#','#...#','#...#','#...#','#...#','#...#'],
 'Μ': ['#.....#','#.....#','##...##','#.#.#.#','#.#.#.#','#..#..#','#..#..#','#.....#','#.....#','#.....#'],
 'Ν': ['#....#','#....#','##...#','#.#..#','#.#..#','#..#.#','#..#.#','#...##','#...##','#....#'],
 'Ξ': ['#####','..#..','..#..','..#..','#####','..#..','..#..','..#..','..#..','#####'],
 'Ο': ['.###.','#...#','#...#','#...#','#...#','#...#','#...#','#...#','#...#','.###.'],
 'Π': ['#####'] + ['#...#']*9,
 'Ρ': ['####.','#...#','#...#','#...#','#...#','####.','#....','#....','#....','#....'],
 'Σ': ['#####','.#..#','.#...','..#..','...#.','..#..','..#..','.#...','.#..#','#####'],
 'Τ': ['#####'] + ['..#..']*9,
 'Υ': ['#....#','#....#','.#...#','.#..#.','..#.#.','..##..','...#..','...#..','...#..','...#..'],
 'Φ': ['...#...','.#####.','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','.#####.','...#...'],
 'Χ': ['#....#','#....#','.#...#','.#..#.','..#.#.','..##..','..#.#.','.#..#.','.#...#','#....#'],
 'Ψ': ['#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','#..#..#','.#####.','...#...','...#...','...#...'],
 'Ω': ['.####.','#....#','#....#','#....#','#....#','#....#','#....#','.#..#.','.#..#.','##..##'],
}

LATIN_CAP = {}
LATIN_LOW = {}

def squash_cap(g10, n=8):
    g = list(g10)
    while len(g) > n:
        cand = [i for i in range(2, 8) if g[i] == g[i-1]] or [i for i in range(2, 8) if g[i] == g[i+1]]
        g.pop(cand[0] if cand else (3 if len(g) % 2 else 6))
    return g

# Standalone 8x12 glyphs for polytonic spacing diacritics (U+1FBF..U+1FFE, U+0384..U+0385),
# positioned in cols 2..7 so they sit cleanly right before an unshifted, full-size capital letter!
STANDALONE_DIACRITICS = {
    '\u0384': ({'\u0301'},),                   # ΄ Tonos
    '\u1FFD': ({'\u0301'},),                   # ´ Oxia
    '\u1FEF': ({'\u0300'},),                   # ` Varia
    '\u1FC0': ({'\u0342'},),                   # ῀ Perispomeni
    '\u1FBF': ({'\u0313'},),                   # ᾿ Psili (Smooth breathing)
    '\u1FFE': ({'\u0314'},),                   # ῾ Dasia (Rough breathing)
    '\u1FCE': ({'\u0313', '\u0301'},),         # ῎ Psili + Oxia
    '\u1FCD': ({'\u0313', '\u0300'},),         # ῍ Psili + Varia
    '\u1FCF': ({'\u0313', '\u0342'},),         # ῏ Psili + Perispomeni
    '\u1FDE': ({'\u0314', '\u0301'},),         # ῞ Dasia + Oxia
    '\u1FDD': ({'\u0314', '\u0300'},),         # ῝ Dasia + Varia
    '\u1FDF': ({'\u0314', '\u0342'},),         # ῟ Dasia + Perispomeni
    '\u0385': ({'\u0308', '\u0301'},),         # ΅ Dialytika + Tonos
    '\u1FEE': ({'\u0308', '\u0301'},),         # ΅ Dialytika + Oxia
    '\u1FED': ({'\u0308', '\u0300'},),         # ῭ Dialytika + Varia
    '\u1FC1': ({'\u0308', '\u0342'},),         # ῁ Dialytika + Perispomeni
}

# Map from frozenset of combining marks on a capital letter to its standalone spacing diacritic char
MARKS_TO_STANDALONE_CHAR = {
    frozenset({'\u0301'}): '\u1FFD',
    frozenset({'\u0300'}): '\u1FEF',
    frozenset({'\u0342'}): '\u1FC0',
    frozenset({'\u0313'}): '\u1FBF',
    frozenset({'\u0314'}): '\u1FFE',
    frozenset({'\u0313', '\u0301'}): '\u1FCE',
    frozenset({'\u0313', '\u0300'}): '\u1FCD',
    frozenset({'\u0313', '\u0342'}): '\u1FCF',
    frozenset({'\u0314', '\u0301'}): '\u1FDE',
    frozenset({'\u0314', '\u0300'}): '\u1FDD',
    frozenset({'\u0314', '\u0342'}): '\u1FDF',
    frozenset({'\u0308', '\u0301'}): '\u1FEE',
    frozenset({'\u0308', '\u0300'}): '\u1FED',
    frozenset({'\u0308', '\u0342'}): '\u1FC1',
}

def split_capital_diacritic(ch):
    """Decompose an accented Greek capital into (standalone_diacritic_char_or_None, unaccented_capital_or_with_sub_iota)."""
    nfd = unicodedata.normalize('NFD', ch)
    base, marks = nfd[0], set(nfd[1:])
    if not base.isupper() or not marks:
        return None, ch
    marks_above = frozenset(marks - {'\u0345', '\u0308'} if marks == {'\u0308'} else marks - {'\u0345'})
    diac_ch = MARKS_TO_STANDALONE_CHAR.get(marks_above)
    # Keep iota subscript on capital if present, or plain base capital
    rem_ch = unicodedata.normalize('NFC', base + ('\u0345' if '\u0345' in marks else '') + ('\u0308' if marks == {'\u0308'} else ''))
    return diac_ch, rem_ch

def standalone_diacritic_pixels(marks):
    """Crisp, Handjet-proportioned standalone diacritic in cols 1..7 (rows 0..3) to precede a capital letter."""
    px = set()
    has_br = bool(marks & {'\u0313', '\u0314'})
    has_ac = bool(marks & {'\u0301', '\u0300', '\u0342'})
    if has_br and has_ac:
        if '\u0342' in marks:
            # Side-by-side in cols 1..7: breathing in cols 1..2 (rows 1..2), circumflex in cols 4..7 (rows 0..1)
            # Zero vertical stacking, zero closed loops!
            if '\u0313' in marks: px |= {(1, 1), (2, 2)}
            if '\u0314' in marks: px |= {(1, 2), (2, 1)}
            px |= {(0, 5), (0, 6), (1, 4), (1, 7)}
        else:
            # Side-by-side in cols 2..7: breathing in cols 2..3 (rows 0..2), accent in cols 5..7 (rows 0..2)
            if '\u0313' in marks: px |= {(0, 2), (1, 3), (2, 2)}
            if '\u0314' in marks: px |= {(0, 3), (1, 2), (2, 3)}
            if '\u0301' in marks: px |= {(0, 7), (1, 6), (2, 5)}
            if '\u0300' in marks: px |= {(0, 5), (1, 6), (2, 7)}
    elif has_br:
        # Standalone breathing in cols 5..6 (rows 0..2) right next to the capital letter
        if '\u0313' in marks: px |= {(0, 5), (1, 6), (2, 5)}
        if '\u0314' in marks: px |= {(0, 6), (1, 5), (2, 6)}
    elif has_ac:
        # Standalone Handjet tonoscomb.case in cols 5..7 (rows 0..2)
        if '\u0301' in marks: px |= {(0, 7), (1, 6), (2, 5)}
        if '\u0300' in marks: px |= {(0, 5), (1, 6), (2, 7)}
        if '\u0342' in marks: px |= {(0, 4), (0, 5), (0, 6), (1, 3), (1, 7)}
    if '\u0308' in marks:
        px |= {(1, 3), (1, 7)}
    return px

MARKS = {'\u0313', '\u0314', '\u0301', '\u0300', '\u0342', '\u0308', '\u0345'}
def mark_pixels(marks, row0, nrows):
    """Crisp lowercase polytonic diacritics in rows 0..1 (with 1px gap between breathing & accent/circumflex)."""
    px = set()
    has_br = bool(marks & {'\u0313', '\u0314'})
    has_ac = bool(marks & {'\u0301', '\u0300', '\u0342'})
    if has_br and has_ac:
        if '\u0342' in marks:
            # Side-by-side in rows 0..1 with a 1-pixel gap at col 2!
            # Breathing in cols 0..1 (rows 0..1), Circumflex arch in cols 3..6 (rows 0..1).
            # Leaves row 2 100% empty above the vowel and eliminates vertical stacking!
            if '\u0313' in marks: px |= {(0, 0), (1, 1)}
            if '\u0314' in marks: px |= {(0, 1), (1, 0)}
            px |= {(0, 4), (0, 5), (1, 3), (1, 6)}
        else:
            # Breathing + Acute/Grave: separated by a clean 1-pixel gap at col 3!
            # Breathing in cols 1..2 (rows 0..1), Acute/Grave in cols 4..5 (rows 0..1)
            if '\u0313' in marks: px |= {(0, 1), (1, 2)}
            if '\u0314' in marks: px |= {(0, 2), (1, 1)}
            if '\u0301' in marks: px |= {(0, 5), (1, 4)}
            if '\u0300' in marks: px |= {(0, 4), (1, 5)}
    elif has_br:
        # Single breathing centered in cols 3..4 (rows 0..1)
        if '\u0313' in marks: px |= {(0, 3), (1, 4)}
        if '\u0314' in marks: px |= {(0, 4), (1, 3)}
    elif has_ac:
        # Single accent centered in cols 2..5 (rows 0..1)
        if '\u0301' in marks: px |= {(0, 4), (1, 3)}
        if '\u0300' in marks: px |= {(0, 3), (1, 4)}
        if '\u0342' in marks: px |= {(0, 2), (0, 3), (0, 4), (1, 1), (1, 5)}
    if '\u0308' in marks:
        if has_ac:
            px |= {(1, 1), (1, 5)}
        else:
            px |= {(1, 2), (1, 4)}
    return px

def mark_pixels_left(marks):
    """Left-side diacritics in col 0 (and col 1 for rows 0..1 when clear) for capital letters."""
    px = set()
    has_br = bool(marks & {'\u0313', '\u0314'})
    has_ac = bool(marks & {'\u0301', '\u0300', '\u0342'})
    if has_br and has_ac:
        # Breathing at rows 0..1, accent at rows 3..4 in col 0..1
        if '\u0313' in marks: px |= {(0, 0), (1, 1), (2, 0)}
        if '\u0314' in marks: px |= {(0, 1), (1, 0), (2, 1)}
        if '\u0301' in marks: px |= {(4, 1), (5, 0)}
        if '\u0300' in marks: px |= {(4, 0), (5, 1)}
        if '\u0342' in marks: px |= {(4, 0), (4, 1), (5, 0)}
    elif has_br:
        if '\u0313' in marks: px |= {(0, 0), (1, 1), (2, 0)}
        if '\u0314' in marks: px |= {(0, 1), (1, 0), (2, 1)}
    elif has_ac:
        # Handjet tonoscomb.case: diagonal slash to the left of the capital
        if '\u0301' in marks: px |= {(0, 1), (1, 0), (2, 0)}
        if '\u0300' in marks: px |= {(0, 0), (1, 0), (2, 1)}
        if '\u0342' in marks: px |= {(0, 0), (0, 1), (1, 0), (1, 1)}
    if '\u0308' in marks:
        px |= {(0, 0), (2, 0)}
    return px

# Narrowed 4-wide variants for 5-wide/6-wide capital vowels when preceded by a left-side diacritic,
# so col 1 is a clean 1-pixel gap between the diacritic (in col 0/1) and the capital (in cols 2..6)!
CAP_ACCENTED_BASE = {
 'Α': ['..#..','.#.#.','.#.#.','#...#','#...#','#...#','#####','#...#','#...#','#...#'], # top cols 0..1 of Α are empty!
 'Ε': ['####','#...','#...','#...','####','#...','#...','#...','#...','####'], # 4-wide: fits in cols 3..6!
 'Η': ['#..#','#..#','#..#','#..#','####','#..#','#..#','#..#','#..#','#..#'], # 4-wide: fits in cols 3..6!
 'Ι': ['###'] + ['.#.']*8 + ['###'], # 3-wide: fits in cols 3..5!
 'Ο': ['.##.','#..#','#..#','#..#','#..#','#..#','#..#','#..#','#..#','.##.'], # 4-wide: fits in cols 3..6!
 'Υ': ['#...#','#...#','.#.#.','.#.#.','..#..','..#..','..#..','..#..','..#..','..#..'], # 5-wide: fits in cols 2..6!
 'Ω': ['.##.','#..#','#..#','#..#','#..#','#..#','#..#','#..#','.#.#','#..#'], # 4-wide: fits in cols 3..6!
 'Ρ': ['###.','#..#','#..#','#..#','#..#','###.','#...','#...','#...','#...'], # 4-wide: fits in cols 3..6!
}

def build_glyph(ch, rom_glyph=None):
    if ch in STANDALONE_DIACRITICS:
        marks = STANDALONE_DIACRITICS[ch][0]
        gl = [list('........') for _ in range(12)]
        for (r, c) in standalone_diacritic_pixels(marks):
            if 0 <= r < 12 and 0 <= c < 8: gl[r][c] = '#'
        return [''.join(r) for r in gl]
    nfd = unicodedata.normalize('NFD', ch)
    base, marks = nfd[0], set(nfd[1:])
    if not marks <= MARKS: return None
    upper = base.isupper()
    if base in LOW: top, lines = LOW[base]; g = pad(top, lines)
    elif base in CAP:
        # Capital letters ALWAYS keep their exact, unshifted, un-squashed Handjet shape!
        # (Their preceding left-side diacritic is emitted as a separate standalone diacritic glyph).
        g = pad(0, CAP[base])
    elif rom_glyph and base in LATIN_CAP: g = list(rom_glyph(LATIN_CAP[base]))
    elif rom_glyph and base in LATIN_LOW: g = list(rom_glyph(LATIN_LOW[base]))
    else: return None
    marks_above = marks - {'\u0345'}
    if upper and marks_above:
        # If an accented capital is ever rendered directly without splitting, leave the capital untouched
        # (or only add dialytika above if Ϋ/Ϊ); all breathing/accent marks live in their own standalone glyph!
        px = {(0, 2), (0, 4)} if marks_above == {'\u0308'} else set()
    elif marks_above:
        px = mark_pixels(marks_above, 0, 3)
    else:
        px = set()
    gl = [list(r) for r in g]
    if '\u0345' in marks: px |= {(10, 3), (11, 3)}
    for (r, c) in px:
        if 0 <= r < 12 and 0 <= c < 8: gl[r][c] = '#'
    return [''.join(r) for r in gl]

LOW_LATIN = {}
