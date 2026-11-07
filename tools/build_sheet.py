"""Build the translation sheet from the script dump. Usage: python build_sheet.py hm_fomt_script_dump.tsv"""
import sys, re, json, collections
SRC = sys.argv[1] if len(sys.argv) > 1 else 'hm_fomt_script_dump.tsv'
SCENE_GAP = 400          # bytes of non-text between strings that starts a new scene
rows = [l.rstrip('\n').split('\t') for l in open(SRC, encoding='utf-8')][1:]
R = [dict(addr=int(r[0], 16), n=int(r[2]), kind=r[3], text=r[7]) for r in rows if r[3] in ('dialogue', 'multiline')]
def flat(t):
    t = t.replace('{BOX}', '').replace('{END}', ' <p> ').replace('{SP2}', ' ').replace('\\n', ' ').replace('\\r', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    return re.sub(r'(<p>\s*)+$', '', t).strip()
for r in R: r['en'] = flat(r['text'])
scene = 0
for i, r in enumerate(R):
    if i and r['addr'] - (R[i-1]['addr'] + R[i-1]['n']) > SCENE_GAP: scene += 1
    r['scene'] = scene
units = {}; order = []
for i, r in enumerate(R):
    if not r['en']: continue
    if r['en'] in units:
        units[r['en']]['addrs'].append('%06X' % r['addr']); continue
    prev = [x['en'] for x in R[max(0, i-3):i] if x['scene'] == r['scene'] and x['en']]
    nxt = [x['en'] for x in R[i+1:i+3] if x['scene'] == r['scene'] and x['en']]
    u = dict(id='m%05d' % (len(units) + 1), addrs=['%06X' % r['addr']], scene=r['scene'], en=r['en'],
             has_box=r['text'].startswith('{BOX}'), has_end=r['text'].rstrip().endswith('{END}'),
             ctx_prev=prev, ctx_next=nxt)
    units[r['en']] = u; order.append(u)
with open('translation_sheet.jsonl', 'w', encoding='utf-8') as f:
    for u in order: f.write(json.dumps(u, ensure_ascii=False) + '\n')
print('units', len(order), 'scenes', scene + 1, 'addresses', sum(len(u['addrs']) for u in order))
