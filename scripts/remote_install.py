#!/usr/bin/env python3
"""Git kod deposunu güvenli biçimde klonlar ve aynı yerel kurucuyu çağırır."""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--destination',type=Path)
    ap.add_argument('--team-mode',choices=['single','multi'],default='multi'); ap.add_argument('--preset',default='standard')
    ap.add_argument('--manager-mode',choices=['orchestrator','hands_on'],default='hands_on'); ap.add_argument('--roles')
    ap.add_argument('--shared-model'); ap.add_argument('--model',action='append',default=[])
    ap.add_argument('--scout',choices=['enabled','disabled']); ap.add_argument('--scout-model')
    ap.add_argument('--playwright',choices=['enabled','disabled']); ap.add_argument('--project-characteristic',action='append',default=[],choices=['browser_ui','desktop_ui','backend','cli','library','database','wordpress','containerized','mobile']); ap.add_argument('--validate-model-capabilities',action='store_true')
    ap.add_argument('--model-metadata-file',type=Path,help='Test/offline doğrulama için models.dev api.json uyumlu metadata dosyası')
    args=ap.parse_args()
    repo=args.repo.strip()
    if not repo or repo.startswith('-'): print('HHC-REMOTE-001: Geçersiz kod deposu adresi.',file=sys.stderr); return 2
    name=repo.rstrip('/').rsplit('/',1)[-1]
    if name.endswith('.git'): name=name[:-4]
    if ':' in name and '/' not in repo: name=name.rsplit(':',1)[-1]
    dest=(args.destination or Path.cwd()/name).resolve()
    if dest.exists() and any(dest.iterdir()): print(f'HHC-REMOTE-002: Hedef klasör boş değil: {dest}',file=sys.stderr); return 2
    env=os.environ.copy(); env['GIT_TERMINAL_PROMPT']='0'
    probe=subprocess.run(['git','ls-remote',repo],env=env,text=True,capture_output=True)
    if probe.returncode!=0:
        print('HHC-REMOTE-003: Kod deposu erişimi doğrulanamadı. Git/SSH/Credential Manager kimlik doğrulamasını kontrol edin.',file=sys.stderr); return probe.returncode or 2
    clone=subprocess.run(['git','clone','--',repo,str(dest)],env=env)
    if clone.returncode!=0:return clone.returncode
    cmd=[sys.executable,str(KIT/'scripts/install.py'),'--project-path',str(dest),'--team-mode',args.team_mode,'--preset',args.preset,'--manager-mode',args.manager_mode]
    if args.roles:cmd += ['--roles',args.roles]
    if args.shared_model:cmd += ['--shared-model',args.shared_model]
    for m in args.model:cmd += ['--model',m]
    if args.scout:cmd += ['--scout',args.scout]
    if args.scout_model:cmd += ['--scout-model',args.scout_model]
    if args.playwright:cmd += ['--playwright',args.playwright]
    for c in args.project_characteristic:cmd += ['--project-characteristic',c]
    if args.validate_model_capabilities:cmd += ['--validate-model-capabilities']
    if args.model_metadata_file:cmd.extend(['--model-metadata-file',str(args.model_metadata_file)])
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
