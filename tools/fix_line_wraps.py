# -*- coding: utf-8 -*-
import json
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append('hm_greek_handover_package/tools')
import hmgreek

data = json.load(open('greek_script.json', 'r', encoding='utf-8'))
WIDTH = 28
LINES = 3

def wrap_words(words, width=WIDTH):
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w) if cur else w
        if hmgreek.cell_width(trial) <= width:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# Check how many messages currently have ANY line > 28
bad_msgs = []
for m in data:
    has_bad = False
    for box in m.get('boxes', []):
        for line in box:
            if hmgreek.cell_width(line) > WIDTH:
                has_bad = True
                break
        if has_bad: break
    if has_bad:
        bad_msgs.append(m)

print(f"Total messages in greek_script.json: {len(data)}")
print(f"Messages with lines > 28 chars: {len(bad_msgs)}")

# Re-wrap all messages and check
rebuilt = 0
for m in data:
    orig_boxes = m.get('boxes', [])
    has_bad = any(hmgreek.cell_width(line) > WIDTH for box in orig_boxes for line in box)
    if not has_bad:
        continue
    
    # Re-wrap each page/box
    new_boxes = []
    for box in orig_boxes:
        full_text = ' '.join(box)
        wlines = wrap_words(full_text.split())
        for i in range(0, len(wlines), LINES):
            new_boxes.append(wlines[i:i+LINES])
    
    m['boxes'] = new_boxes
    
    # Re-encode hex bytes for the message
    # Format matches ingest.py
    data_bytes = bytearray()
    # Check if original hex started with 0x0c
    orig_bytes = bytes.fromhex(m['hex'])
    has_box = (len(orig_bytes) > 0 and orig_bytes[0] == 0x0C)
    has_end = (len(orig_bytes) > 0 and orig_bytes[-1] == 0x05)
    
    if has_box:
        data_bytes.append(0x0C)
    for bi, box in enumerate(new_boxes):
        if bi:
            data_bytes += b'\x05\x0c'
        data_bytes += b'\r\n'.join(hmgreek.encode_line(l) for l in box)
    if has_end:
        data_bytes.append(0x05)
    
    m['hex'] = bytes(data_bytes).hex()
    m['size'] = len(data_bytes)
    rebuilt += 1

print(f"Rebuilt {rebuilt} messages with strict width <= {WIDTH}.")

# Verify no lines > 28 remain!
remaining_bad = 0
for m in data:
    for box in m.get('boxes', []):
        for line in box:
            if hmgreek.cell_width(line) > WIDTH:
                remaining_bad += 1

print(f"Remaining bad lines > 28 chars: {remaining_bad}")
assert remaining_bad == 0

# Save updated greek_script.json
with open('greek_script.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print("Saved updated greek_script.json!")
