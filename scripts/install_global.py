#!/usr/bin/env python3
"""HHC'yi makineye bir kez kurar ve küçük OpenCode başlangıç entegrasyonunu kaydeder."""
from __future__ import annotations
import argparse, os, shutil, sys
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]

def runtime_root()->Path:
    if os.name=='nt': return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'HHC-AI-Team-Kit'/'current'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'hhc-ai-team-kit'/'current'
def opencode_root()->Path:
    return Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'opencode'
def copy_runtime(dst:Path):
    if dst.exists(): shutil.rmtree(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    ignore=shutil.ignore_patterns('.git','.opencode','.pytest_cache','.hhc-bootstrap-venv','dist','tests','__pycache__','*.pyc','CHECKPOINT.md','HANDOFF.md','TASKS.md','opencode.jsonc','AGENTS.md')
    shutil.copytree(KIT,dst,ignore=ignore)
def install_bootstrap(dst:Path):
    oc=opencode_root(); py=Path(sys.executable).resolve()
    for rel in ['commands/hhc-install.md','commands/hhc-install-remote.md','commands/hhc-reconfigure.md']:
        src=dst/'bootstrap'/rel; target=oc/rel; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(src.read_text(encoding='utf-8').replace('{{KIT_ROOT}}',str(dst)).replace('{{PYTHON}}',str(py)),encoding='utf-8')
    src=dst/'bootstrap/skills/hhc-project-bootstrap'; target=oc/'skills/hhc-project-bootstrap'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(src,target)
    for p in target.rglob('*'):
        if p.is_file(): p.write_text(p.read_text(encoding='utf-8').replace('{{KIT_ROOT}}',str(dst)).replace('{{PYTHON}}',str(py)),encoding='utf-8')
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--install',action='store_true'); args=ap.parse_args()
    if not args.install: ap.error('--install gerekli')
    dst=runtime_root(); copy_runtime(dst); install_bootstrap(dst)
    print(f'HHC AI Team Kit kuruldu: {dst}')
    print(f'OpenCode başlangıç entegrasyonu: {opencode_root()}')
    print('Artık /hhc-install ile kurabilir, /hhc-reconfigure ile profil/rol/model ayarlarını sonradan değiştirebilirsiniz.')
    return 0
if __name__=='__main__': raise SystemExit(main())
