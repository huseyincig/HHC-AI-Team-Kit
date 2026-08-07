#!/usr/bin/env python3
"""Sadeleştirilmiş kit için küçük yapısal doğrulayıcı."""
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
for p in sorted((KIT/'presets').glob('*.json')):
    d=merge(p.stem)
    for role in d['roles']:
        f=KIT/'roles'/f'{role}.md'
        if not f.is_file(): err(f'{p.name}: eksik rol {role}')
    for skill in d['skills']:
        f=KIT/'skills'/skill/'SKILL.md'
        if not f.is_file(): err(f'{p.name}: eksik beceri {skill}')
    for cmd in d['commands']:
        f=KIT/'commands'/f'{cmd}.md'
        if not f.is_file(): err(f'{p.name}: eksik komut {cmd}')
for f in (KIT/'roles').glob('*.md'):
    t=f.read_text(encoding='utf-8')
    if not t.startswith('---\n') or '\nmode:' not in t or '\ndescription:' not in t: err(f'{f}: geçersiz frontmatter')
    if re.search(r'^model\s*:',t,re.M): err(f'{f}: ürün rolü modelden bağımsız olmalıdır')
    if 'hhc_' in t or '.opencode/hhc' in t: err(f'{f}: eski HHC çalışma zamanı referansı')
for f in KIT.rglob('*'):
    if not f.is_file() or any(x in f.parts for x in ('.git','.opencode')): continue
    # Önbellek/sanal ortam dosyaları çalışma sırasında oluşabilir; sürüm paketleyici bunları pakete eklemez.
    if '.hhc-bootstrap-venv' in f.parts: err(f'repoya eklenmiş başlangıç sanal ortamı bulunmamalıdır: {f}')
if ERR:
    print('VALIDATION FAIL'); [print('- '+x) for x in ERR]; sys.exit(1)
print('VALIDATION PASS')
print(f'roles={len(list((KIT/"roles").glob("*.md")))} skills={len(list((KIT/"skills").glob("*/SKILL.md")))} presets={len(list((KIT/"presets").glob("*.json")))} commands={len(list((KIT/"commands").glob("*.md")))}')
