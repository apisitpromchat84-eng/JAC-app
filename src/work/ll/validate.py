# usage: python3 validate.py NN   -> checks /home/claude/ll/out_NN.json against in_NN.json
import json, re, sys
n = sys.argv[1]
inp = json.load(open(f'/home/claude/ll/in_{n}.json'))
try: out = json.load(open(f'/home/claude/ll/out_{n}.json'))
except Exception as e: print('JSON ERROR', e); sys.exit(1)
KANJI = r'[㐀-鿿豈-﫿々〆ヵヶ]'
RUBY = re.compile(r'(' + KANJI + r'+)\{([ぁ-ゖー・]+)\}')
errs = []
byid = {o.get('id'): o for o in out}
for q in inp:
    o = byid.get(q['id'])
    if not o: errs.append(f"{q['id']}: missing"); continue
    for k in ('sth', 'ath', 'th'):
        if not isinstance(o.get(k), str) or len(o[k].strip()) < 8: errs.append(f"{q['id']}: {k} empty/too short")
    if o.get('ans') not in (1,2,3,4): errs.append(f"{q['id']}: ans must be 1-4"); continue
    q['ans'] = o['ans']
    if not isinstance(o.get('stem_f'), str) or not isinstance(o.get('opts_f'), list) or len(o['opts_f']) != len(q['opts']): errs.append(f"{q['id']}: stem_f/opts_f missing"); continue
    for k, v in [('stem_f', o['stem_f'])] + [(f'opts_f[{i}]', t) for i, t in enumerate(o['opts_f'])]:
        bad = re.findall(KANJI + '+', RUBY.sub('', v))
        if bad: errs.append(f"{q['id']} {k}: kanji without reading {{}}: {' '.join(sorted(set(bad)))}")
        plainf = RUBY.sub(r'\1', v); orig = re.sub(r'\([ぁ-ゖー]+\)', '', q['stem'] if k == 'stem_f' else q['opts'][int(k[7])])
        if not o.get('edit_note') and plainf.replace(' ', '') != orig.replace(' ', ''): errs.append(f"{q['id']} {k}: Japanese text changed (only readings may change): {plainf} ≠ {orig}")
    oth = o.get('oth')
    if not isinstance(oth, list) or len(oth) != len(q['opts']): errs.append(f"{q['id']}: oth must have {len(q['opts'])} items"); oth = []
    for i, t in enumerate(oth):
        if i + 1 == q['ans'] and t != '': errs.append(f"{q['id']}: oth[{i}] is the answer, must be \"\"")
        if i + 1 != q['ans'] and (not isinstance(t, str) or len(t) < 6): errs.append(f"{q['id']}: oth[{i}] empty")
    for k, v in [('sth', o.get('sth', '')), ('ath', o.get('ath', '')), ('th', o.get('th', ''))] + [(f'oth[{i}]', t) for i, t in enumerate(oth)]:
        if not isinstance(v, str) or v == '': continue
        rest = RUBY.sub('', v)
        bad = re.findall(KANJI + '+', rest)
        if bad: errs.append(f"{q['id']} {k}: kanji without reading {{}}: {' '.join(sorted(set(bad)))[:80]}")
        if re.search(r'\{[^}]*[^ぁ-ゖー・}][^}]*\}', v): errs.append(f"{q['id']} {k}: reading braces must contain hiragana only")
        if re.search(r'ข้อ\s*[1-4１-４]|ตัวเลือก(ที่)?\s*[1-4１-４]|choice\s*[1-4]|option\s*[1-4]|[1-4１-４]\s*番', v, re.I): errs.append(f"{q['id']} {k}: cites an option number")
        tags = set(re.findall(r'</?([a-zA-Z]+)', v)) - {'b', 'br'}
        if tags: errs.append(f"{q['id']} {k}: tags not allowed {tags}")
        if not re.search(r'[฀-๿]', v): errs.append(f"{q['id']} {k}: no Thai")
print(f'{len(out)} items, {len(errs)} problems'); [print(' -', e) for e in errs[:60]]
sys.exit(1 if errs else 0)
