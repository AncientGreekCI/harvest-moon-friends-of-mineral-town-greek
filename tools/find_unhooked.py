# -*- coding: utf-8 -*-
import json
import re

script_data = json.load(open('greek_script.json', 'r', encoding='utf-8'))
hooked_addrs = set()
for m in script_data:
    for a in m['addrs']:
        hooked_addrs.add(int(a, 16))

lines = open('hm_greek_handover_package/data/hm_fomt_script_dump.tsv', 'r', encoding='utf-8').read().splitlines()

unhooked_genuine = []
for l in lines[1:]:
    p = l.split('\t')
    if len(p) < 8: continue
    addr = int(p[0], 16)
    kind = p[3]
    text = p[7]
    if addr >= 0x4FA000 or addr < 0x0E0000:
        continue
    if addr in hooked_addrs:
        continue
    
    clean = text.replace('{BOX}', '').replace('{END}', '').replace('{SP2}', ' ').strip()
    if not clean: continue
    if clean.startswith(('RIFF', 'SCR CODE', 'JUMP', 'STR ')): continue
    if clean in ('Error', 'bad_alloc'): continue
    
    # Check if text is genuine English words
    # At least one 2-letter word or standard punctuation
    words = re.findall(r'[A-Za-z]{2,}', clean)
    if not words: continue
    
    # Exclude obvious sound/pattern noise
    if sum(1 for c in clean.lower() if c in 'aeiouy') == 0:
        continue
    if len(clean) > 12 and sum(1 for c in clean.lower() if c in 'aeiouy') / len(clean) < 0.15:
        continue
    
    unhooked_genuine.append((addr, kind, clean, text))

print(f"Total unhooked genuine entries (0x0E0000..0x4FA000): {len(unhooked_genuine)}")
unique_texts = {}
for a, k, c, raw in unhooked_genuine:
    if c not in unique_texts:
        unique_texts[c] = []
    unique_texts[c].append(a)

print(f"Unique text strings: {len(unique_texts)}")

# Save to a file for review
with open('tools/unhooked_strings.json', 'w', encoding='utf-8') as f:
    json.dump([{'text': t, 'addrs': [f"{a:06X}" for a in addrs]} for t, addrs in unique_texts.items()], f, ensure_ascii=False, indent=2)

print("Saved to tools/unhooked_strings.json")
