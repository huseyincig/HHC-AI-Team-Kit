#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
DIST_DIRS=['roles','skills','commands','presets','scripts','bootstrap']
DIST_FILES=['VERSION','README.md','README.en.md','KURULUM.md','INSTALLATION.md','SECURITY.md','CONTRIBUTING.md','LICENSE','THIRD_PARTY_NOTICES.md','CHANGELOG.md','HHC-KUR.cmd','HHC-KUR.sh','.gitignore']
SOURCE_DIRS=[*DIST_DIRS,'tests']
SOURCE_FILES=[*DIST_FILES,'pytest.ini','requirements-dev.txt','.gitattributes']
# Kişisel/geliştirme ortamı dosyaları hiçbir paylaşılabilir arşive girmez.
FORBIDDEN_ROOTS={'.opencode','opencode.jsonc','AGENTS.md'}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(65536),b''):h.update(c)
    return h.hexdigest()

def collect(dirs, files):
    out={}
    for d in dirs:
        base=KIT/d
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if not p.is_file():
                continue
            rel=p.relative_to(KIT)
            if '__pycache__' in rel.parts or p.suffix=='.pyc' or '.pytest_cache' in rel.parts:
                continue
            if rel.parts and rel.parts[0] in FORBIDDEN_ROOTS:
                continue
            out[str(rel)]=p
    for n in files:
        if n in FORBIDDEN_ROOTS:
            continue
        p=KIT/n
        if p.is_file(): out[n]=p
    return out

def write_zip(path, entries):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as f:
        for n,p in sorted(entries.items()): f.write(p,n)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=KIT/'dist')
    ap.add_argument('--source-out',type=Path,help='Temiz SOURCE arşivini yazılacak dizin; kişisel .opencode/opencode.jsonc/AGENTS.md dahil edilmez')
    a=ap.parse_args()
    version=(KIT/'VERSION').read_text().strip()

    e=collect(DIST_DIRS,DIST_FILES)
    a.out.mkdir(parents=True,exist_ok=True)
    z=a.out/f'HHC-AI-Team-Kit-{version}.zip'
    write_zip(z,e)
    m={'kit_name':'HHC AI Team Kit','version':version,'archive':z.name,'archive_sha256':sha(z),'file_count':len(e),'files':{n:sha(p) for n,p in sorted(e.items())}}
    (a.out/f'RELEASE-MANIFEST-{version}.json').write_text(json.dumps(m,indent=2)+'\n')
    print(f'PAKET: {z}\nDOSYA SAYISI: {len(e)}\nSHA256: {m["archive_sha256"]}')

    if a.source_out:
        se=collect(SOURCE_DIRS,SOURCE_FILES)
        sz=a.source_out/f'HHC-AI-Team-Kit-{version}-SOURCE.zip'
        write_zip(sz,se)
        print(f'SOURCE: {sz}\nSOURCE DOSYA SAYISI: {len(se)}\nSOURCE SHA256: {sha(sz)}')

if __name__=='__main__': main()
