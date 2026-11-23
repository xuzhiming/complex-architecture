# writes params_table.md: every parameter, value, source (measured from sheet / inferred), and whether the compare loop tuned it
import json, os
H = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(H, 'params.json')))
P0 = json.load(open(os.path.join(H, 'params_initial.json'))) if os.path.exists(os.path.join(H, 'params_initial.json')) else P
MEAS = json.load(open(os.path.join(H, 'sources.json')))["measured from sheet"]
def rows(d, pre=''):
    out = []
    for k, v in d.items():
        key = pre + k
        if isinstance(v, dict): out += rows(v, key + '.')
        elif isinstance(v, list) and v and isinstance(v[0], dict) and 'name' in v[0]:
            for it in v: out += [(f"{key}.{it['name']}", {kk: vv for kk, vv in it.items() if kk != 'name'})]
        else: out.append((key, v))
    return out
def get(d, key):
    for p in key.split('.'):
        if isinstance(d, list): d = next((x for x in d if isinstance(x, dict) and x.get('name') == p), None)
        elif isinstance(d, dict): d = d.get(p)
        if d is None: return None
    return {k: v for k, v in d.items() if k != 'name'} if isinstance(d, dict) else d
def source(k):
    return 'measured from sheet' if any(k == s or k.startswith(s + '.') for s in MEAS) else 'inferred'
R = [r for r in rows(P) if not r[0].startswith('style.')]   # v14: render-look settings (style.*) are not geometry; see CHANGES_v14.md
L = ['# Parameter table', '',
     'Every dimension used by `build.py` comes from `params.json` (metres; +Z up, front = -Y). '
     f"Scale: the sheets have no dimension lines, so the reference-pixel scale ({P['meta']['scale_m_per_ref_px']} m/px) was fixed from the tower storey pitch "
     '(~26 px per 4.5 m storey) and sanity-checked against a 1.75 m person; the compare loop aligns silhouettes by scaling each reference bbox to `global.H_total`.', '',
     '**measured from sheet** = read off the elevation / plan crops at that scale. **inferred** = design assumption (interior layout, code-typical sizes, faces not visible on the sheets). '
     '**tuned** = changed by the auto-compare loop (start value in brackets; start file `params_initial.json`).', '',
     '| parameter | value | source | tuned |', '|---|---|---|---|']
nm = nt = 0
for k, v in R:
    if k.startswith('meta.'): continue
    v0 = get(P0, k); t = '' if v0 == v else f'yes (from {json.dumps(v0)})'
    s = source(k); nm += s.startswith('measured'); nt += bool(t)
    vs = json.dumps(v); vs = vs if len(vs) < 160 else vs[:157] + '...'
    L.append(f'| `{k}` | `{vs}` | {s} | {t} |')
L += ['', f'{len(R) - 5} parameters: {nm} measured from sheet, {len(R) - 5 - nm} inferred, {nt} tuned by the compare loop.']
open(os.path.join(H, 'params_table.md'), 'w').write('\n'.join(L) + '\n')
print('params_table.md:', len(R) - 5, 'params,', nm, 'measured,', nt, 'tuned')
