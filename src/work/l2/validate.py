# usage: python3 validate.py X   -> checks /home/claude/l2/out_X.json
import json, re, sys, os
n = sys.argv[1]
try: out = json.load(open(f'/home/claude/l2/out_{n}.json'))
except Exception as e: print('JSON ERROR', e); sys.exit(1)
K = r'[㐀-鿿豈-﫿々〆ヵヶ]'
RUBY = re.compile(r'(' + K + r'+)\{([ぁ-ゖー・]+)\}')
CATS = {'l_kikai','l_denki','l_kankan','l_dougu','l_anzen','l_kanri','l_chikuro'}
errs = []; ids = set()
for o in out:
    i = o.get('id', '?')
    if i in ids: errs.append(f'{i}: duplicate id')
    ids.add(i)
    if o.get('cat') not in CATS: errs.append(f'{i}: bad cat')
    if not re.fullmatch(r'L[567] P\d{3}(-\d{3})?', o.get('src', '')): errs.append(f'{i}: src must look like "L5 P118" (printed page)')
    if o.get('ans') not in (1, 2, 3, 4): errs.append(f'{i}: ans 1-4'); continue
    if not isinstance(o.get('opts_f'), list) or len(o['opts_f']) != 4: errs.append(f'{i}: need 4 opts_f'); continue
    if len(set(RUBY.sub(r'\1', x) for x in o['opts_f'])) != 4: errs.append(f'{i}: options not distinct')
    oth = o.get('oth')
    if not isinstance(oth, list) or len(oth) != 4: errs.append(f'{i}: oth must have 4'); oth = ['']*4
    for k in ('sth', 'ath', 'th'):
        if not isinstance(o.get(k), str) or len(o[k]) < 8: errs.append(f'{i}: {k} missing')
    for j, t in enumerate(oth):
        if j + 1 == o['ans'] and t != '': errs.append(f'{i}: oth[{j}] is the answer, must be ""')
        if j + 1 != o['ans'] and (not isinstance(t, str) or len(t) < 6): errs.append(f'{i}: oth[{j}] empty')
    if o.get('img'):
        if not os.path.exists('/home/claude/l2/' + o['img']): errs.append(f'{i}: img file missing')
        c = o.get('crop')
        if c is not None and not (isinstance(c, list) and len(c) == 4 and all(0 <= x <= 1 for x in c) and c[0] < c[2] and c[1] < c[3]): errs.append(f'{i}: crop must be [x0,y0,x1,y1] fractions')
    fields = [('stem_f', o.get('stem_f', ''))] + [(f'opts_f[{j}]', t) for j, t in enumerate(o['opts_f'])] + [(k, o.get(k, '')) for k in ('sth', 'ath', 'th')] + [(f'oth[{j}]', t) for j, t in enumerate(oth)]
    for k, v in fields:
        if not isinstance(v, str) or v == '': continue
        bad = re.findall(K + '+', RUBY.sub('', v))
        if bad: errs.append(f'{i} {k}: kanji without reading: {" ".join(sorted(set(bad)))[:60]}')
        if re.search(r'\{[^}]*[^ぁ-ゖー・}][^}]*\}', v): errs.append(f'{i} {k}: braces must hold hiragana only')
        if k not in ('stem_f',) and not k.startswith('opts_f') and re.search(r'ข้อ\s*[1-4]|ตัวเลือก(ที่)?\s*[1-4]|[1-4]\s*番', v): errs.append(f'{i} {k}: cites option number')
        tags = set(re.findall(r'</?([a-zA-Z]+)', v)) - {'b', 'br'}
        if tags: errs.append(f'{i} {k}: tags {tags}')
        if (k in ('sth', 'ath', 'th') or k.startswith('oth')) and not re.search(r'[฀-๿]', v): errs.append(f'{i} {k}: no Thai')
    if re.search(r'[฀-๿]', o.get('stem_f', '') + ''.join(o['opts_f'])): errs.append(f'{i}: Thai inside Japanese stem/options')
print(f'{len(out)} items, {len(errs)} problems'); [print(' -', e) for e in errs[:80]]
sys.exit(1 if errs else 0)
