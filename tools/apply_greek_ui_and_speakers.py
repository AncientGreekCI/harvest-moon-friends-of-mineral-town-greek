# -*- coding: utf-8 -*-
"""
apply_greek_ui_and_speakers.py

Installs:
1. Greek font glyphs for single-byte codes (Greek uppercase A..X -> Α..Ω, lowercase a..y -> α..ω, accented vowels in 0x80..0x92).
2. Greek on-screen keyboard grid at 0x0E89B6.
3. Greek UI prompt strings for Name Entry menu (Your name, Farm name, Dog name, Is this OK?, Yes, No, etc.).
4. Missing opening cutscene lines (0x080FB2F4, 0x080FB520, 0x080FB534) and shop dialogue into greek_script.json and redirection table.
5. Greek speaker names in cutscenes (Mother, Father, Old Man, Girl, ???) and in the NPC Master Table (0x8104258).
"""

import os
import sys
import struct
import json

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('hm_greek_handover_package/tools')
import glyphs
import hmgreek

import unicodedata

def encode_greek_single_byte(s):
    """Map Greek string to our single-byte codes with polytonic normalization."""
    table = {
        # Capitals
        'Α': 'A', 'Β': 'B', 'Γ': 'C', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'F', 'Η': 'G', 'Θ': 'H',
        'Ι': 'I', 'Κ': 'J', 'Λ': 'K', 'Μ': 'L', 'Ν': 'M', 'Ξ': 'N', 'Ο': 'O', 'Π': 'P',
        'Ρ': 'Q', 'Σ': 'R', 'Τ': 'S', 'Υ': 'T', 'Φ': 'U', 'Χ': 'V', 'Ψ': 'W', 'Ω': 'X',
        # Lowercase
        'α': 'a', 'β': 'b', 'γ': 'c', 'δ': 'd', 'ε': 'e', 'ζ': 'f', 'η': 'g', 'θ': 'h',
        'ι': 'i', 'κ': 'j', 'λ': 'k', 'μ': 'l', 'ν': 'm', 'ξ': 'n', 'ο': 'o', 'π': 'p',
        'ρ': 'q', 'σ': 'r', 'ς': 's', 'τ': 't', 'υ': 'u', 'φ': 'v', 'χ': 'w', 'ψ': 'x', 'ω': 'y',
        # Accented vowels
        'ά': '\x80', 'έ': '\x81', 'ή': '\x82', 'ί': '\x83', 'ό': '\x84', 'ύ': '\x85', 'ώ': '\x86',
        'ᾶ': '\x87', 'ῆ': '\x88', 'ῖ': '\x89', 'ῦ': '\x8A', 'ῶ': '\x8B',
        'Ά': '\x8C', 'Έ': '\x8D', 'Ή': '\x8E', 'Ί': '\x8F', 'Ό': '\x90', 'Ύ': '\x91', 'Ώ': '\x92',
    }
    res = bytearray()
    for ch in s:
        norm = unicodedata.normalize('NFD', ch)
        base = norm[0]
        has_acute = any(c in norm for c in ('\u0301', '\u0341', '\u0300'))
        has_circ = any(c in norm for c in ('\u0342', '\u0303'))
        
        target_ch = ch
        if base.isupper():
            target_ch = base
        elif base in 'αεηιουω':
            if has_circ and base in 'αηιουω':
                target_ch = {'α':'ᾶ','η':'ῆ','ι':'ῖ','υ':'ῦ','ω':'ῶ'}.get(base, base)
            elif has_acute:
                target_ch = {'α':'ά','ε':'έ','η':'ή','ι':'ί','ο':'ό','υ':'ύ','ω':'ώ'}.get(base, base)
            else:
                target_ch = base

        if target_ch in table:
            res.append(ord(table[target_ch]))
        else:
            res.append(ord(target_ch) if ord(target_ch) < 256 else ord('?'))
    return bytes(res)

def main():
    rom_path = 'pilot.gba'
    rom = bytearray(open(rom_path, 'rb').read())
    print(f"Loaded ROM: {rom_path} ({len(rom)} bytes)")

    # -------------------------------------------------------------
    # 1. Install Greek Glyphs for Single-Byte Characters
    # -------------------------------------------------------------
    # Available unreferenced slots in 0x4F90CC: 369..486 (118 slots)
    BASE_ADDR = 0x4F90CC
    START_GLYPH_IDX = 369

    clean_rom_path = 'Harvest Moon - Friends of Mineral Town (USA).gba'
    clean_rom = open(clean_rom_path, 'rb').read()

    def rom_glyph(c):
        i = struct.unpack_from('<h', clean_rom, 0x4FA7A0 + 2 * ord(c))[0]
        return [format(b, '08b').replace('0', '.').replace('1', '#') for b in clean_rom[BASE_ADDR + i * 12: BASE_ADDR + i * 12 + 12]]

    caps = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
    lows = 'αβγδεζηθικλμνξοπρστυφχψω'
    accs = 'άέήίόύώᾶῆῖῦῶΆΈΉΊΌΎΏ'
    all_greek = list(caps) + list(lows) + ['ς'] + list(accs)

    cur_idx = START_GLYPH_IDX
    char_to_glyph_idx = {}
    for ch in all_greek:
        g = glyphs.build_glyph(ch, rom_glyph)
        assert g is not None, f"Could not build glyph for {ch}"
        g_bytes = glyphs.rows_to_bytes(g)
        off = BASE_ADDR + cur_idx * 12
        rom[off:off + 12] = g_bytes
        char_to_glyph_idx[ch] = cur_idx
        cur_idx += 1

    print(f"Installed {len(all_greek)} single-byte Greek glyphs at indices {START_GLYPH_IDX}..{cur_idx - 1} (ROM {hex(BASE_ADDR + START_GLYPH_IDX*12)}..{hex(BASE_ADDR + cur_idx*12)})")

    # Update 0x4FA7A0 single-byte lookup table
    # Map 'A'..'X' (0x41..0x58) -> caps
    for i, ch in enumerate(caps):
        code = 0x41 + i
        g_idx = char_to_glyph_idx[ch]
        struct.pack_into('<h', rom, 0x4FA7A0 + code * 2, g_idx)

    # Map 'a'..'y' (0x61..0x79) -> lows and final sigma
    low_order = list(lows[:18]) + ['ς'] + list(lows[18:])
    for i, ch in enumerate(low_order):
        code = 0x61 + i
        g_idx = char_to_glyph_idx[ch]
        struct.pack_into('<h', rom, 0x4FA7A0 + code * 2, g_idx)

    # Map accented vowels 0x80..0x92
    for i, ch in enumerate(accs):
        code = 0x80 + i
        g_idx = char_to_glyph_idx[ch]
        struct.pack_into('<h', rom, 0x4FA7A0 + code * 2, g_idx)

    print("Updated 0x4FA7A0 single-byte table for Greek capitals, lowercase, and accented vowels.")

    # -------------------------------------------------------------
    # 2. Update On-Screen Keyboard Grid at 0x0E89B6
    # -------------------------------------------------------------
    # Grid size: 6 rows of 30 characters each + 1 byte padding (stride 31)
    grid_off = 0xE89B6
    # Row 0: Α..Ο (15 chars) -> 'A B C D E F G H I J K L M N O '
    # Row 1: Π..Ω (9 chars) + . , ; ! ? - (6 chars) = 15 chars
    # Row 2: α..ο (15 chars) -> 'a b c d e f g h i j k l m n o '
    # Row 3: π..ω, ς (10 chars) + ' : ~ / * (5 chars) = 15 chars
    # Row 4: 0..9 (10 chars) + + - x ~ / (5 chars) = 15 chars
    # Row 5: < > ( ) & ! ? ...
    row0 = b"A B C D E F G H I J K L M N O \x00"
    row1 = b"P Q R S T U V W X . , ; ! ? - \x00"
    row2 = b"a b c d e f g h i j k l m n o \x00"
    row3 = b"p q r s t u v w x y ' : ~ / * \x00"
    row4 = b"0 1 2 3 4 5 6 7 8 9 + = % & # \x00"
    row5 = b"< > ( ) \" _ \x80 \x81 \x82 \x83 \x84 \x85 \x86 \x87 \x88 \x00"

    assert len(row0) == 31 and len(row1) == 31 and len(row2) == 31 and len(row3) == 31 and len(row4) == 31 and len(row5) == 31
    rom[grid_off + 0*31 : grid_off + 1*31] = row0
    rom[grid_off + 1*31 : grid_off + 2*31] = row1
    rom[grid_off + 2*31 : grid_off + 3*31] = row2
    rom[grid_off + 3*31 : grid_off + 4*31] = row3
    rom[grid_off + 4*31 : grid_off + 5*31] = row4
    rom[grid_off + 5*31 : grid_off + 6*31] = row5
    print("Updated on-screen keyboard grid at 0x0E89B6 to Greek letters and punctuation.")

    # -------------------------------------------------------------
    # 3. Update Name Entry Menu Prompts & Seasons
    # -------------------------------------------------------------
    # Using single-byte Greek encoding so they render seamlessly with 0x4FA7A0
    menu_strings = {
        0xE8958: (16, "Τὸ ὄνομά σου"),
        0xE8968: (16, "Γενέθλια"),
        0xE8978: (16, "Τὸ τοῦ ἀγροῦ"),
        0xE8988: (16, "Τὸ τοῦ κυνός"),
        0xE8998: (12, "Καλῶς ἔχει;"),
        0xE89A4: (4,  "Ναί"),
        0xE89A8: (4,  "Οὔ"),
        0xE8BF4: (8,  "Ὄνομα"),
        0xE8BFC: (24, "                  Τέλος"),
        0xE8C2C: (24, "Ὀρθὸν τὸ ὄνομα;"),
        0xE8C44: (4,  "Ναί"),
        0xE8C48: (4,  "Οὔ"),
        0xE8934: (8,  "Σόν"),
        0xE893C: (8,  "Ἀγροῦ"),
        0xE8944: (8,  "Κυνός"),
        0xE8674: (8,  "Σφάλμα"),
        0xE86A8: (8,  "Βίβλος"),
        0xE86B0: (8,  "Σῷζε"),
        0xE86B8: (8,  "Φέρε"),
        0xE86C4: (8,  "Μέρος 1"),
        0xE86CC: (8,  "Μέρος 2"),
        0xE86EC: (4,  "Ναί"),
        0xE86F0: (4,  "Οὔ"),
        0xE874C: (8,  "Ἔτη"),
        0xE8758: (8,  " Ἡμ."),
        0xE8768: (8,  " Ἀγρός"),
        0xE8770: (12, "Ἀνάγνωθι"),
        0xE877C: (16, "Γράφε ἐν βίβλῳ."),
        0xE878C: (24, "Οὐδὲν γεγραμμένον."),
        0xE890C: (8,  "Φέρειν;"),
        0xE8914: (12, "Μεταγραφή;"),
    }

    for off, (max_len, greek_str) in menu_strings.items():
        encoded = encode_greek_single_byte(greek_str) + b'\x00'
        assert len(encoded) <= max_len, f"String '{greek_str}' ({len(encoded)} bytes) exceeds max length {max_len} at {hex(off)}"
        # Clear slot with nulls then write encoded null-terminated string
        rom[off:off + max_len] = b'\x00' * max_len
        rom[off:off + len(encoded)] = encoded

    # Season names for status & birthday screens (stride 7 at 0xF04EE)
    seasons = [
        (0xF04EE, 7, "Ἔαρ"),
        (0xF04F5, 7, "Θέρος"),
        (0xF04FC, 7, "Φθιν."),
        (0xF0503, 7, "Χειμών"),
    ]
    for off, max_len, s_name in seasons:
        encoded = encode_greek_single_byte(s_name) + b'\x00'
        assert len(encoded) <= max_len
        rom[off:off + max_len] = b'\x00' * max_len
        rom[off:off + len(encoded)] = encoded

    # Days of the week table at 0xF050F (stride 5 bytes: Sun..Sat)
    days_of_week = [
        (0xF050F + 0*5, 5, "Κυρ."),
        (0xF050F + 1*5, 5, "Δευ."),
        (0xF050F + 2*5, 5, "Τρί."),
        (0xF050F + 3*5, 5, "Τετ."),
        (0xF050F + 4*5, 5, "Πέμ."),
        (0xF050F + 5*5, 5, "Παρ."),
        (0xF050F + 6*5, 5, "Σάβ."),
    ]
    for off, max_len, d_name in days_of_week:
        encoded = encode_greek_single_byte(d_name) + b'\x00'
        assert len(encoded) <= max_len
        rom[off:off + max_len] = b'\x00' * max_len
        rom[off:off + len(encoded)] = encoded

    # 8-byte stride season tables across other screens (0xFB85C, 0xFB9A0, 0xFDA40, 0xFFCC0, 0x104938)
    season_8byte_tables = [0xFB85C, 0xFB9A0, 0xFDA40, 0xFFCC0, 0x104938]
    season_names_8b = ["Ἔαρ", "Θέρος", "Φθινόπ.", "Χειμών"]
    for tbl_off in season_8byte_tables:
        for s_idx, s_name in enumerate(season_names_8b):
            off = tbl_off + s_idx * 8
            encoded = encode_greek_single_byte(s_name) + b'\x00'
            rom[off:off + 8] = b'\x00' * 8
            rom[off:off + len(encoded)] = encoded

    # -------------------------------------------------------------
    # 3b. Birthday Calendar Selection Screen at 0x0FBD18
    # -------------------------------------------------------------
    # 0xFBD18: 'Are you sure?\x00\x00\x00' (16 bytes)
    # 0xFBD28: 'Yes\x00' (4 bytes)
    # 0xFBD2C: 'No\x00\x00' (4 bytes)
    # 0xFBD44..0xFBD73: 6-char Wide strings for Spring, Summer, Fall, Winter:
    #   'Spring': 'S\x00p\x00r\x00i\x00n\x00g\x00'
    #   'Summer': 'S\x00u\x00m\x00m\x00e\x00r\x00'
    #   'Fall  ': 'F\x00a\x00l\x00l\x00 \x00 \x00'
    #   'Winter': 'W\x00i\x00n\x00t\x00e\x00r\x00'
    # 0xFBD76: 8-char Wide string for 'Birthday': 'B\x00i\x00r\x00t\x00h\x00d\x00a\x00y\x00'
    
    cal_sure = encode_greek_single_byte("Ὀρθῶς ἔχει;") + b'\x00'
    rom[0xFBD18:0xFBD28] = cal_sure.ljust(16, b'\x00')
    
    cal_yes = encode_greek_single_byte("Ναί") + b'\x00'
    rom[0xFBD28:0xFBD2C] = cal_yes.ljust(4, b'\x00')
    
    cal_no = encode_greek_single_byte("Οὔ") + b'\x00'
    rom[0xFBD2C:0xFBD30] = cal_no.ljust(4, b'\x00')

    def make_wide_single_byte(s, length):
        enc = encode_greek_single_byte(s)
        # Pad with spaces if needed
        enc = enc.ljust(length, b' ')[:length]
        res = bytearray()
        for b in enc:
            res.append(b)
            res.append(0)
        return bytes(res)

    # 4 seasons (6 characters each, stride 12 bytes)
    rom[0xFBD44:0xFBD50] = make_wide_single_byte("Ἔαρ", 6)
    rom[0xFBD50:0xFBD5C] = make_wide_single_byte("Θέρος", 6)
    rom[0xFBD5C:0xFBD68] = make_wide_single_byte("Φθιν.", 6)
    rom[0xFBD68:0xFBD74] = make_wide_single_byte("Χειμών", 6)

    # Birthday header (8 characters, 16 bytes at 0xFBD76)
    rom[0xFBD76:0xFBD86] = make_wide_single_byte("Γενέθλια", 8)

    print("Updated birthday calendar screen strings at 0x0FBD18 (Are you sure?, Yes, No, 4 Seasons, Birthday).")

    print(f"Updated {len(menu_strings)} name entry prompts and {len(seasons)} season strings.")

    print(f"Updated {len(menu_strings)} name entry and system menu prompt strings.")

    # -------------------------------------------------------------
    # 4. Update Speaker Names (Prologue & NPC Master Table)
    # -------------------------------------------------------------
    # Cutscene literal pool pointers
    # In prologue cutscene:
    # 0x5F788, 0x5F800, 0x5F868, 0x5F97C -> Mother (0x080FB234)
    # 0x5F7C4, 0x5F824, 0x5F8A4, 0x5F91C -> Father (0x080FB27C)
    # 0x5F83C, 0x5F8E0, 0x5F958, 0x5FA84, 0x5FAC0, 0x5FAE4, 0x5FB7C, 0x5FBAC -> Old Man (0x080FB300)
    # 0x5F9AC -> ??? (0x080FB51C)
    # 0x5F9F4, 0x5FA30, 0x5FA54, 0x5FB14, 0x5FB50 -> Girl (0x080FB53C)
    
    # Store speaker name strings in free space around 0x780B00
    SPEAKER_STRINGS_BASE = 0x780B00
    cur_speaker_off = SPEAKER_STRINGS_BASE

    def write_speaker_str(text):
        nonlocal cur_speaker_off
        encoded = encode_greek_single_byte(text) + b'\x00'
        off = cur_speaker_off
        rom[off:off + len(encoded)] = encoded
        cur_speaker_off += len(encoded)
        while cur_speaker_off % 4 != 0:
            rom[cur_speaker_off] = 0
            cur_speaker_off += 1
        return 0x08000000 + off

    ptr_mother = write_speaker_str("Μήτηρ")
    ptr_father = write_speaker_str("Πατήρ")
    ptr_oldman = write_speaker_str("Γέρων")
    ptr_mystery = write_speaker_str(";;;")
    ptr_girl   = write_speaker_str("Κόρη")

    # Patch cutscene literal pools
    for off in [0x5F788, 0x5F800, 0x5F868, 0x5F97C]:
        struct.pack_into('<I', rom, off, ptr_mother)
    for off in [0x5F7C4, 0x5F824, 0x5F8A4, 0x5F91C]:
        struct.pack_into('<I', rom, off, ptr_father)
    for off in [0x5F83C, 0x5F8E0, 0x5F958, 0x5FA84, 0x5FAC0, 0x5FAE4, 0x5FB7C, 0x5FBAC]:
        struct.pack_into('<I', rom, off, ptr_oldman)
    struct.pack_into('<I', rom, 0x5F9AC, ptr_mystery)
    for off in [0x5F9F4, 0x5FA30, 0x5FA54, 0x5FB14, 0x5FB50]:
        struct.pack_into('<I', rom, off, ptr_girl)

    print("Patched prologue cutscene literal pools with Greek speaker names (Μήτηρ, Πατήρ, Γέρων, ;;;, Κόρη).")

    # NPC Master Table at 0x8104258
    npc_names = {
        1: "Λιλλία",
        2: "Ῥῖκος",
        3: "Ποπούρα",
        4: "Βαρλῆς",
        5: "Μαΐα",
        6: "Σαϊβάρας",
        7: "Γραῖος",
        8: "Δούξ",
        9: "Μάννα",
        10: "Βασίλειος",
        11: "Ἄννα",
        12: "Μαρία",
        13: "Θωμᾶς",
        14: "Ἄρρις",
        15: "Ἑλένη",
        16: "Στοῦ",
        17: "Ἰωσήφ",
        18: "Σάσα",
        19: "Καρίνα",
        20: "Ἰατρός",
        21: "Ἔλλη",
        22: "Κάρτερ",
        23: "Κλίφ",
        24: "Δοῦγος",
        25: "Ἄννα",
        26: "Κάϊ",
        27: "Γότζης",
        28: "Ζάκχος",
        29: "Οὐών",
        30: "Γεύστης",
        31: "Θεά",
        32: "Κάππα",
        33: "Λοῦ",
        34: "Λύ",
        36: "Σταΐδ",
        37: "Νάππυ",
        38: "Βόλδ",
        39: "Σέφ",
        40: "Ἄκουα",
        41: "Ὅγγυ",
        42: "Τίμιδ",
    }

    npc_tbl_off = 0x104258
    for npc_id, greek_name in npc_names.items():
        ptr = write_speaker_str(greek_name)
        struct.pack_into('<I', rom, npc_tbl_off + npc_id * 8, ptr)

    print(f"Patched NPC Master Table at 0x8104258 with {len(npc_names)} Greek NPC speaker names.")

    # Save output ROM
    open('pilot.gba', 'wb').write(rom)
    open('Harvest Moon - Friends of Mineral Town (Greek Pilot).gba', 'wb').write(rom)
    print("Saved updated ROMs.")

    # Generate updated IPS patch across all target paths
    orig_rom = open('Harvest Moon - Friends of Mineral Town (USA).gba', 'rb').read()
    import insert_text
    ips_data = insert_text.create_ips(orig_rom, rom)
    
    ips_destinations = [
        'hm_fomt_greek.ips',
        'patches/hm_fomt_greek.ips',
        'patches/hm_fomt_greek_pilot.ips',
        'hm_greek_handover_package/patches/hm_fomt_greek.ips',
        'hm_greek_handover_package/patches/hm_fomt_greek_pilot.ips',
    ]
    for p in ips_destinations:
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        open(p, 'wb').write(ips_data)
        print(f"Synchronized complete IPS patch: {p} ({len(ips_data)} bytes)")

if __name__ == '__main__':
    main()
