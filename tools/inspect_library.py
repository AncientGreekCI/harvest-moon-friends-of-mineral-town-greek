# -*- coding: utf-8 -*-
import json

data = json.load(open('tools/unhooked_strings.json', 'r', encoding='utf-8'))
lib_strings = [d for d in data if 0x100000 <= int(d['addrs'][0], 16) < 0x110000]

print(f"Total in 0x100000..0x10FFFF: {len(lib_strings)}")
for i, d in enumerate(lib_strings[100:160], start=100):
    print(f"{i:2d}: [{d['addrs'][0]}] {d['text']!r}")
