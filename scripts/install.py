#!/usr/bin/env python3
"""HHC AI Team Kit için küçük proje kurucusu. Yalnız Python standart kütüphanesini kullanır."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
PRESET_DIR=KIT/'presets'
STATE_REL=Path('.opencode/hhc-team.json')
SCOUT_CONFIG_REL=Path('.opencode/opencode.jsonc')
PRIMARY_ROLES={'manager','working-manager','solo-agent'}

class InstallError(RuntimeError): pass

def load_preset(name:str, seen=None)->dict:
    seen=seen or set()
    if name in seen: raise InstallError(f'Profil döngüsü: {name}')
    path=PRESET_DIR/f'{name}.json'
    if not path.is_file(): raise InstallError(f'Bilinmeyen profil: {name}')
    data=json.loads(path.read_text(encoding='utf-8')); seen.add(name)
    base={'roles':[],'skills':[],'commands':[]}
    if data.get('extends'): base=load_preset(data['extends'],seen)
    for key in ('roles','skills','commands'):
        base[key]=list(dict.fromkeys([*base.get(key,[]),*data.get(key,[])]))
    base.update({k:v for k,v in data.items() if k not in ('roles','skills','commands','extends')})
    return base

def safe_project(path:Path)->Path:
    expanded=path.expanduser()
    if expanded.is_symlink(): raise InstallError('Proje kökü sembolik bağlantı olamaz.')
    p=expanded.resolve(); p.mkdir(parents=True,exist_ok=True)
    return p

def available_roles()->list[str]: return sorted(x.stem for x in (KIT/'roles').glob('*.md'))

def specialist_roles_from_preset(preset_roles:list[str])->list[str]:
    return [r for r in preset_roles if r not in PRIMARY_ROLES]

def parse_custom_specialists(value:str|None)->list[str]:
    if not value: return []
    raw=list(dict.fromkeys(x.strip() for x in value.split(',') if x.strip()))
    known=set(available_roles())
    unknown=set(raw)-known
    if unknown: raise InstallError('Bilinmeyen rol: '+', '.join(sorted(unknown)))
    # rc.16 uyumluluğu: eski custom state/CLI manager veya working-manager içeriyorsa primary seçimini
    # team-mode/manager-mode belirler; bunları uzman listesinden sessizce çıkar.
    return [r for r in raw if r not in PRIMARY_ROLES]

def valid_model_id(model:str)->str:
    model=model.strip()
    if not model or '/' not in model or model.startswith('/') or model.endswith('/'):
        raise InstallError(f'Geçersiz model kimliği: {model!r}. Beklenen biçim sağlayıcı/model.')
    return model

def parse_models(values:list[str])->dict[str,str]:
    out={}
    for item in values:
        if '=' not in item: raise InstallError(f'--model biçimi rol=sağlayıcı/model olmalı: {item}')
        role,model=item.split('=',1); role=role.strip()
        if not role: raise InstallError(f'Geçersiz model eşlemesi: {item}')
        out[role]=valid_model_id(model)
    return out

def inject_scout_policy(text:str, enabled:bool)->str:
    if 'scout: allow' not in text:
        return text
    return text.replace('scout: allow', 'scout: allow' if enabled else 'scout: deny')

def inject_model(text:str, model:str|None)->str:
    if not model: return text
    if not text.startswith('---\n'): raise InstallError('Rol dosyasında frontmatter bölümü yok.')
    end=text.find('\n---',4)
    if end<0: raise InstallError('Rol dosyasındaki frontmatter bölümü kapanmıyor.')
    head=text[4:end]
    head=re.sub(r'^model\s*:.*$', '', head, flags=re.M).rstrip()
    return '---\n'+head+f'\nmodel: {model}\n---'+text[end+4:]

def sha_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def sha_file(path:Path)->str: return sha_bytes(path.read_bytes())

def load_state(project:Path)->dict|None:
    p=project/STATE_REL
    if not p.is_file(): return None
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError) as e: raise InstallError(f'Mevcut HHC durum dosyası okunamadı: {e}')

def rel(project:Path,path:Path)->str:return path.resolve().relative_to(project.resolve()).as_posix()

def write_file(src:Path,dst:Path,project:Path,*,overwrite:bool,dry:bool,text:str|None,written:list[str],preserved:list[str])->bool:
    if dst.exists() and not overwrite:
        expected=text.encode('utf-8') if text is not None else src.read_bytes()
        if dst.read_bytes()==expected:return True
        preserved.append(str(dst)); return False
    if dry:return True
    dst.parent.mkdir(parents=True,exist_ok=True)
    if text is None:shutil.copy2(src,dst)
    else:dst.write_text(text,encoding='utf-8',newline='')
    written.append(str(dst)); return True

def remove_empty_dirs(root:Path):
    if not root.exists():return
    for p in sorted((x for x in root.rglob('*') if x.is_dir()),key=lambda x:len(x.parts),reverse=True):
        try:p.rmdir()
        except OSError:pass

def generate_config(primary:str)->str:
    data={'$schema':'https://opencode.ai/config.json','default_agent':primary,'subagent_depth':1,'compaction':{'auto':True,'prune':True}}
    return json.dumps(data,ensure_ascii=False,indent=2)+'\n'

def generate_scout_config(model:str)->str:
    # OpenCode current runtime merges .opencode/opencode.json{,c} as a project config source.
    # Keep this HHC-owned layer minimal so an existing root opencode.json(c) stays untouched.
    data={'$schema':'https://opencode.ai/config.json','agent':{'scout':{'model':model}}}
    return json.dumps(data,ensure_ascii=False,indent=2)+'\n'

def main()->int:
    ap=argparse.ArgumentParser(description='HHC AI Team Kit proje kurulumu')
    ap.add_argument('--project-path',type=Path,default=Path('.'))
    ap.add_argument('--team-mode',choices=['single','multi'],default='multi',help='single=tek ana muhatap + uzman havuzu; multi=rol bazlı ekip')
    ap.add_argument('--preset',default='standard')
    ap.add_argument('--manager-mode',choices=['orchestrator','hands_on'],default='hands_on')
    ap.add_argument('--roles',help='Yalnız custom profil için uzman roller: coder,qa-reviewer gibi; primary otomatik eklenir')
    ap.add_argument('--shared-model',help='Seçili tüm ajanlara aynı sağlayıcı/model kimliğini ata')
    ap.add_argument('--model',action='append',default=[],help='rol=sağlayıcı/model; tekrar edilebilir')
    ap.add_argument('--scout',choices=['enabled','disabled'],help='Native OpenCode Scout kullanımı; yeni kurulumda varsayılan disabled')
    ap.add_argument('--scout-model',help='Scout enabled ise native scout için sağlayıcı/model')
    ap.add_argument('--reconfigure',action='store_true',help='Mevcut HHC ekibini güvenli biçimde yeniden yapılandır')
    ap.add_argument('--force',action='store_true',help='Çakışan HHC hedef dosyalarının üzerine yaz')
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    try:
        project=safe_project(args.project_path); preset=load_preset(args.preset); previous=load_state(project)
        if args.reconfigure and not previous: raise InstallError('Yeniden yapılandırılacak HHC kurulumu bulunamadı. Önce /hhc-install kullanın.')
        if args.shared_model and args.model: raise InstallError('--shared-model ile --model birlikte kullanılamaz.')
        explicit_models=parse_models(args.model); shared_model=valid_model_id(args.shared_model) if args.shared_model else None
        if args.scout is None:
            scout_enabled=bool(previous.get('scout_enabled',False)) if (args.reconfigure and previous) else False
        else:
            scout_enabled=args.scout=='enabled'
        if scout_enabled:
            inherited_scout=(previous or {}).get('scout_model') if args.reconfigure else None
            scout_model=valid_model_id(args.scout_model or inherited_scout or '') if (args.scout_model or inherited_scout) else None
            if not scout_model:
                raise InstallError('Scout etkinse --scout-model sağlayıcı/model zorunludur; manager modeline sessiz devralma yapılmaz.')
        else:
            if args.scout_model:
                raise InstallError('--scout-model yalnız --scout enabled ile kullanılabilir.')
            scout_model=None

        if args.preset=='custom':
            specialists=parse_custom_specialists(args.roles)
        else:
            if args.roles: raise InstallError('--roles yalnız custom profil ile kullanılabilir.')
            specialists=specialist_roles_from_preset(preset['roles'])

        if args.team_mode=='single':
            # Tek Ana Ajan = tek kullanıcı muhatabı. Profil uzmanları kurulmaya ve native Task ile çağrılmaya devam eder.
            primary='working-manager'; manager_mode='hands_on'
            roles=list(dict.fromkeys([primary,*specialists]))
            if explicit_models:
                raise InstallError('Tek Ana Ajan modunda rol bazlı --model kullanma; tek model için --shared-model kullan.')
            models={role:shared_model for role in roles} if shared_model else {}
        else:
            if args.preset=='custom' and not specialists:
                raise InstallError('Özel Çoklu Ajan ekibinde en az bir uzman rol seçilmelidir.')
            manager_mode=args.manager_mode
            primary='working-manager' if manager_mode=='hands_on' else 'manager'
            roles=list(dict.fromkeys([primary,*specialists]))
            if shared_model: models={role:shared_model for role in roles}
            else: models=dict(explicit_models)
            missing=set(models)-set(roles)
            if missing: raise InstallError('Seçili ekipte olmayan role model verildi: '+', '.join(sorted(missing)))

        model_policy='shared' if shared_model else ('per-role' if models else 'inherit')  # yalnız backward-compatible state; wizard bunu sormaz.
        skills=list(preset['skills']); commands=list(preset['commands'])
        prev_managed=set(previous.get('managed_files',[])) if previous else set()
        written=[]; preserved=[]; removed=[]; managed=[]; op=project/'.opencode'
        desired=[]
        for role in roles:
            src=KIT/'roles'/f'{role}.md'; dst=op/'agents'/src.name
            role_text=inject_model(src.read_text(encoding='utf-8'),models.get(role))
            if role in ('manager','working-manager'):
                role_text=inject_scout_policy(role_text,scout_enabled)
            desired.append((src,dst,role_text))
        for skill in skills:
            srcdir=KIT/'skills'/skill
            for src in srcdir.rglob('*'):
                if src.is_file(): desired.append((src,op/'skills'/skill/src.relative_to(srcdir),None))
        for command in commands:
            src=KIT/'commands'/f'{command}.md'; desired.append((src,op/'commands'/src.name,None))
        if scout_enabled:
            scout_cfg=project/SCOUT_CONFIG_REL
            scout_text=generate_scout_config(scout_model)
            scout_rel=rel(project,scout_cfg)
            if scout_cfg.exists() and scout_rel not in prev_managed and not args.force:
                raise InstallError('Scout modeli güvenle yazılamıyor: .opencode/opencode.jsonc kullanıcı tarafından yönetiliyor. Dosyayı korumak için kurulum durduruldu; Scout override alanını manuel birleştirin veya HHC-owned config kullanın.')
            desired.append((KIT/'VERSION',scout_cfg,scout_text))

        desired_rel={rel(project,dst) for _,dst,_ in desired}
        if args.reconfigure:
            for old in sorted(prev_managed-desired_rel):
                path=project/old
                if path.is_file():
                    if not args.dry_run:path.unlink()
                    removed.append(str(path))
        for src,dst,text in desired:
            r=rel(project,dst); overwrite=args.force or (args.reconfigure and r in prev_managed)
            owned=write_file(src,dst,project,overwrite=overwrite,dry=args.dry_run,text=text,written=written,preserved=preserved)
            if owned or r in prev_managed:managed.append(r)

        cfg=project/'opencode.jsonc'; cfg_created=False; cfg_hash=None; cfg_existed_before=cfg.exists(); cfg_action=None
        previous_cfg_created=bool(previous and previous.get('config_created_by_hhc')); previous_cfg_hash=(previous or {}).get('config_sha256')
        if cfg.exists():
            expected_cfg=generate_config(primary)
            if not previous and cfg.read_text(encoding='utf-8')==expected_cfg:
                previous_cfg_created=True; previous_cfg_hash=sha_file(cfg)
            can_update=args.force or (args.reconfigure and previous_cfg_created and previous_cfg_hash and sha_file(cfg)==previous_cfg_hash)
            if can_update:
                if not args.dry_run:cfg.write_text(generate_config(primary),encoding='utf-8',newline=''); written.append(str(cfg))
                cfg_created=True; cfg_action='updated-hhc-config'
            else:
                preserved.append(str(cfg)); cfg_created=bool(previous_cfg_created and previous_cfg_hash and sha_file(cfg)==previous_cfg_hash); cfg_action='preserved-existing-config'
        else:
            if not args.dry_run:cfg.write_text(generate_config(primary),encoding='utf-8',newline=''); written.append(str(cfg))
            cfg_created=True; cfg_action='created-hhc-config'
        if cfg.exists() and cfg_created and not args.dry_run:cfg_hash=sha_file(cfg)
        elif previous_cfg_hash and cfg_created:cfg_hash=previous_cfg_hash

        state={'schema_version':1,'kit_version':(KIT/'VERSION').read_text().strip(),'team_mode':args.team_mode,
               'preset':args.preset,'manager_mode':manager_mode,'primary_agent':primary,'roles':roles,'skills':skills,'commands':commands,
               'model_policy':model_policy,'shared_model':shared_model,'models':models,'scout_enabled':scout_enabled,'scout_model':scout_model,'managed_files':sorted(managed),
               'config_created_by_hhc':cfg_created,'config_sha256':cfg_hash}
        if not args.dry_run:
            state_path=project/STATE_REL; state_path.parent.mkdir(parents=True,exist_ok=True)
            state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline=''); remove_empty_dirs(op)
        config_result={'path':str(cfg),'action':cfg_action,'existed_before':cfg_existed_before,'managed_by_hhc':cfg_created,
                       'notice':('Mevcut opencode.jsonc korundu; HHC bu dosyadaki default_agent, subagent_depth veya compaction değerlerini değiştirmedi. Mevcut OpenCode yapılandırmanız geçerlidir.' if cfg_action=='preserved-existing-config' else None)}
        print(json.dumps({'status':'DRY_RUN' if args.dry_run else ('RECONFIGURED' if args.reconfigure else 'COMPLETE'),'project':str(project),
                          **{k:state[k] for k in ('team_mode','preset','manager_mode','primary_agent','roles','skills','commands','model_policy','shared_model','models','scout_enabled','scout_model')},
                          'config':config_result,'written':written,'removed':removed,'preserved_existing':list(dict.fromkeys(preserved))},ensure_ascii=False,indent=2))
        if preserved:print('NOT: HHC tarafından güvenle yönetilemeyen mevcut dosyalar korunmuştur.',file=sys.stderr)
        return 0
    except (OSError,ValueError,json.JSONDecodeError,InstallError) as e:
        print(f'HHC-INSTALL-001: {e}',file=sys.stderr); return 2
if __name__=='__main__':raise SystemExit(main())
