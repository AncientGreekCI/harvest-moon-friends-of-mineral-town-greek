"""Validate + format Gemini output.  python ingest.py gemini_output.jsonl [translation_sheet.jsonl]
Gemini output: JSON lines (or a JSON list) of {"id": "m00367", "el": "polytonic text with {N:?} tokens and <p> page marks"}.
Produces greek_script.json (game bytes per message) and prints a report. Writes nothing to the ROM."""
import sys, json, re, collections
from hmgreek import normalize, TOKEN, cell_width, encode_line
WIDTH = 28          # cells per line (engine limit: column index <= 0x1B)
LINES = 3           # lines per text box
NAME_CELLS = 6      # cells reserved for a {N:x} slot (assumption - check the real name length)
def load(path):
    t = open(path, encoding='utf-8').read().strip()
    if t.startswith('['): return json.loads(t)
    return [json.loads(l) for l in t.splitlines() if l.strip()]
def wrap(words):
    lines, cur = [], ''
    for w in words:
        if cell_width(w, NAME_CELLS) > WIDTH: raise ValueError('word longer than %d cells: %s' % (WIDTH, w))
        trial = (cur + ' ' + w) if cur else w
        if cell_width(trial, NAME_CELLS) <= WIDTH: cur = trial
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
def format_message(el, unit):
    warn = []
    el = normalize(el)
    el = re.sub(r'\s*\n\s*', ' ', el).strip()
    src_tok = collections.Counter(TOKEN.findall(unit['en'])); got_tok = collections.Counter(TOKEN.findall(el))
    if src_tok != got_tok: warn.append('TOKENS differ: source %s vs output %s' % (dict(src_tok), dict(got_tok)))
    pages_text = [p.strip() for p in re.split(r'\s*<p>\s*', el) if p.strip()]
    if len(pages_text) != unit['en'].count('<p>') + 1: warn.append('page marks: source %d, output %d' % (unit['en'].count('<p>') + 1, len(pages_text)))
    boxes = []
    for p in pages_text:
        lines = wrap(p.split())
        for i in range(0, len(lines), LINES): boxes.append(lines[i:i + LINES])
    data = bytearray()
    if unit.get('has_box', True): data.append(0x0C)
    for bi, box in enumerate(boxes):
        if bi: data += b'\x05\x0c'
        data += b'\r\n'.join(encode_line(l) for l in box)
    if unit.get('has_end', True): data.append(0x05)
    return bytes(data), boxes, warn
if __name__ == '__main__':
    out = [o for o in load(sys.argv[1]) if 'id' in o]; sheet = {}
    for l in open(sys.argv[2] if len(sys.argv) > 2 else 'translation_sheet.jsonl', encoding='utf-8'):
        u = json.loads(l); sheet[u['id']] = u
    res = []; errs = 0; extra = 0
    for o in out:
        u = sheet.get(o['id'])
        if not u: print('UNKNOWN id', o['id']); errs += 1; continue
        try:
            b, boxes, warn = format_message(o['el'], u)
        except ValueError as e:
            print('ERROR', o['id'], e); errs += 1; continue
        en_boxes = u['en'].count('<p>') + 1
        if len(boxes) > en_boxes: extra += 1; warn.append('%d boxes vs %d in English' % (len(boxes), en_boxes))
        for w in warn: print('WARN', o['id'], w)
        res.append(dict(id=o['id'], addrs=u['addrs'], hex=b.hex(), size=len(b), boxes=boxes))
    json.dump(res, open('greek_script.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok: %d messages, %d errors, %d with extra boxes, %d bytes total' % (len(res), errs, extra, sum(r['size'] for r in res)))
