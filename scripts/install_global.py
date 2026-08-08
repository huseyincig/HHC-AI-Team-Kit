#!/usr/bin/env python3
"""HHC'yi makineye bir kez kurar ve küçük OpenCode başlangıç entegrasyonunu kaydeder."""
from __future__ import annotations
import argparse, os, shutil, sys
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 9)

def runtime_root()->Path:
    if os.name=='nt': return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'HHC-AI-Team-Kit'/'current'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'hhc-ai-team-kit'/'current'
def opencode_root()->Path:
    return Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'opencode'
def check_python_version(vi=sys.version_info) -> None:
    """Python minimum sürümünü kontrol eder. Eksikse RuntimeError hatası üretir."""
    cur = (vi.major, vi.minor)
    if cur < MIN_PYTHON:
        raise RuntimeError(f'Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ gerekli, mevcut {cur[0]}.{cur[1]}.')
def copy_runtime(dst:Path):
    """Runtime'ı önce sibling staging'e kopyala; başarısız kopya mevcut sağlam runtime'ı silmesin."""
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.is_symlink():
        raise RuntimeError('Global HHC runtime yolu sembolik bağlantı olamaz.')
    stage=dst.with_name(dst.name+'.hhc-new')
    backup=dst.with_name(dst.name+'.hhc-old')
    for path in (stage,backup):
        if path.is_symlink(): path.unlink()
        elif path.exists(): shutil.rmtree(path)
    ignore=shutil.ignore_patterns('.git','.opencode','.pytest_cache','.hhc-bootstrap-venv','dist','tests','__pycache__','*.pyc','CHECKPOINT.md','HANDOFF.md','TASKS.md','opencode.jsonc','AGENTS.md')
    try:
        shutil.copytree(KIT,stage,ignore=ignore)
        if dst.exists(): os.replace(dst,backup)
        try:
            os.replace(stage,dst)
        except Exception:
            if backup.exists() and not dst.exists(): os.replace(backup,dst)
            raise
        if backup.exists(): shutil.rmtree(backup,ignore_errors=True)
    finally:
        if stage.exists(): shutil.rmtree(stage,ignore_errors=True)
def install_bootstrap(dst:Path):
    oc=opencode_root(); py=Path(sys.executable).resolve()
    for rel in ['commands/hhc-install.md','commands/hhc-reconfigure.md','commands/hhc-update.md','commands/hhc-status.md']:
        src=dst/'bootstrap'/rel; target=oc/rel; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(src.read_text(encoding='utf-8').replace('{{KIT_ROOT}}',str(dst)).replace('{{PYTHON}}',str(py)),encoding='utf-8',newline='')
    src=dst/'bootstrap/skills/hhc-project-bootstrap'; target=oc/'skills/hhc-project-bootstrap'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(src,target)
    for p in target.rglob('*'):
        if p.is_file(): p.write_text(p.read_text(encoding='utf-8').replace('{{KIT_ROOT}}',str(dst)).replace('{{PYTHON}}',str(py)),encoding='utf-8',newline='')
def main()->int:
    try:
        check_python_version()
    except RuntimeError as e:
        print(f'HHC-INSTALL-001: {e}', file=sys.stderr)
        return 2
    ap=argparse.ArgumentParser(); ap.add_argument('--install',action='store_true'); args=ap.parse_args()
    if not args.install: ap.error('--install gerekli')
    dst=runtime_root()
    try:
        copy_runtime(dst); install_bootstrap(dst)
    except (OSError,RuntimeError) as e:
        print(f'HHC-INSTALL-001: Global kurulum tamamlanamadı: {e}',file=sys.stderr)
        return 2
    print(f'HHC AI Team Kit kuruldu: {dst}')
    print(f'OpenCode başlangıç entegrasyonu: {opencode_root()}')
    print('Artık /hhc-install ile kurabilir, /hhc-reconfigure ile profil/rol/model ayarlarını sonradan değiştirebilir, /hhc-update ile güncelleyebilir, /hhc-status ile durumunuza bakabilirsiniz.')
    return 0
if __name__=='__main__': raise SystemExit(main())
