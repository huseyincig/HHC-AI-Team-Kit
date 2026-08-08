#!/usr/bin/env python3
"""HHC AI Team Kit için küçük yapısal doğrulayıcı."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]
ERR=[]
def err(msg): ERR.append(msg)

def load(name):
    p=KIT/'presets'/f'{name}.json'
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: err(f'{p}: {e}'); return {}

def merge(name,seen=None):
    seen=seen or set()
    if name in seen: err(f'profil döngüsü: {name}'); return {'roles':[],'skills':[],'commands':[]}
    seen.add(name); d=load(name); out={'roles':[],'skills':[],'commands':[]}
    if d.get('extends'): out=merge(d['extends'],seen)
    for k in out: out[k]=list(dict.fromkeys(out[k]+d.get(k,[])))
    return out

profiles={p.stem for p in (KIT/'presets').glob('*.json')}
if profiles!={'basic','standard','powerful'}: err(f'ana profiller yalnız basic/standard/powerful olmalı, bulundu: {sorted(profiles)}')
resolved={}
for p in sorted((KIT/'presets').glob('*.json')):
    d=merge(p.stem); resolved[p.stem]=d
    raw=load(p.stem)
    policy=raw.get('policy',{})
    for key in ('specialist_threshold','parallelism','independent_review','priority'):
        if key not in policy: err(f'{p.name}: eksik policy alanı {key}')
    for role in d['roles']:
        f=KIT/'roles'/f'{role}.md'
        if not f.is_file(): err(f'{p.name}: eksik rol {role}')
    for skill in d['skills']:
        f=KIT/'skills'/skill/'SKILL.md'
        if not f.is_file(): err(f'{p.name}: eksik beceri {skill}')
    for cmd in d['commands']:
        f=KIT/'commands'/f'{cmd}.md'
        if not f.is_file(): err(f'{p.name}: eksik komut {cmd}')

if all(k in resolved for k in ('basic','standard','powerful')):
    base=resolved['standard']
    for name in ('basic','powerful'):
        for key in ('roles','skills','commands'):
            if resolved[name][key]!=base[key]: err(f'{name}: profil kadroyu/capability havuzunu değiştirmemeli ({key})')

for f in (KIT/'roles').glob('*.md'):
    t=f.read_text(encoding='utf-8')
    if not t.startswith('---\n') or '\nmode:' not in t or '\ndescription:' not in t: err(f'{f}: geçersiz frontmatter')
    if re.search(r'^model\s*:',t,re.M): err(f'{f}: ürün rolü modelden bağımsız olmalıdır')
    if 'hhc_' in t or '.opencode/hhc' in t: err(f'{f}: eski HHC çalışma zamanı referansı')

for legacy in ('minimal','web-development','desktop-development','high-assurance','custom'):
    if (KIT/'presets'/f'{legacy}.json').exists(): err(f'legacy profil ana preset olarak paketlenmemeli: {legacy}')

if not (KIT/'scripts/project_characteristics.py').is_file(): err('project_characteristics.py eksik')

for f in KIT.rglob('*'):
    if not f.is_file() or any(x in f.parts for x in ('.git','.opencode')): continue
    if '.hhc-bootstrap-venv' in f.parts: err(f'repoya eklenmiş başlangıç sanal ortamı bulunmamalıdır: {f}')

if ERR:
    print('VALIDATION FAIL'); [print('- '+x) for x in ERR]; sys.exit(1)
print('VALIDATION PASS')
print(f'roles={len(list((KIT/"roles").glob("*.md")))} skills={len(list((KIT/"skills").glob("*/SKILL.md")))} presets={len(list((KIT/"presets").glob("*.json")))} commands={len(list((KIT/"commands").glob("*.md")))}')
