"""Split translation_sheet.jsonl into Gemini batches (consecutive messages, <=MAXU units / <=MAXC chars)."""
import json, os
MAXU, MAXC = 80, 10000
U = [json.loads(l) for l in open('translation_sheet.jsonl', encoding='utf-8')]
os.makedirs('batches', exist_ok=True)
batches = []; cur = []; chars = 0
for u in U:
    if cur and (len(cur) >= MAXU or chars + len(u['en']) > MAXC):
        batches.append(cur); cur = []; chars = 0
    cur.append(u); chars += len(u['en'])
if cur: batches.append(cur)
for i, b in enumerate(batches, 1):
    first = b[0]
    obj = dict(batch=i, context_before=first['ctx_prev'], units=[dict(id=u['id'], scene=u['scene'], en=u['en']) for u in b])
    json.dump(obj, open('batches/batch_%03d.json' % i, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(batches), 'batches')
