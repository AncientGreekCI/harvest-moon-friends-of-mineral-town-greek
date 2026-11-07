# -*- coding: utf-8 -*-
import json

data = json.load(open('tools/unhooked_strings.json', 'r', encoding='utf-8'))

categories = {
    'system_menus': [], # 0x0E8000 .. 0x0E8FFF
    'items_and_tools': [], # 0x0E9000 .. 0x0EEFFF
    'dialogue_and_choices': [], # 0x2A0000 .. 0x3F0000
    'library_and_tv': [], # 0x100000 .. 0x11FFFF
    'other': [],
}

for d in data:
    first_addr = int(d['addrs'][0], 16)
    if 0x0E8000 <= first_addr <= 0x0E8FFF:
        categories['system_menus'].append(d)
    elif 0x0E9000 <= first_addr <= 0x0F0000:
        categories['items_and_tools'].append(d)
    elif 0x100000 <= first_addr <= 0x120000:
        categories['library_and_tv'].append(d)
    elif 0x2A0000 <= first_addr <= 0x4F0000:
        categories['dialogue_and_choices'].append(d)
    else:
        categories['other'].append(d)

for cat, items in categories.items():
    print(f"Category '{cat}': {len(items)} unique strings")
    for sample in items[:5]:
        print(f"   [{sample['addrs'][0]}] {sample['text']!r}")
