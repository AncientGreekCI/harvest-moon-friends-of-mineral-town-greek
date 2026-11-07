# -*- coding: utf-8 -*-
import json

data = json.load(open('tools/unhooked_strings.json', 'r', encoding='utf-8'))
choices = [d for d in data if 0x2A0000 <= int(d['addrs'][0], 16) <= 0x4F0000]

with open('tools/choices_list.txt', 'w', encoding='utf-8') as f:
    for i, c in enumerate(choices):
        f.write(f"{i:3d}\t{c['addrs'][0]}\t{c['text']}\n")

print(f"Wrote {len(choices)} dialogue choices to tools/choices_list.txt")
