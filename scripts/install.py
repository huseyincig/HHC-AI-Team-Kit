#!/usr/bin/env python3
"""HHC AI Team Kit için küçük proje kurucusu. Yalnız Python standart kütüphanesini kullanır."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
PRESET_DIR=KIT/'presets'
STATE_REL=Path('.opencode/hhc-team.json')
AUX_CONFIG_REL=Path('.opencode/opencode.jsonc')
PLAYWRIGHT_MCP_VERSION='0.0.78'
PRIMARY_ROLES={'manager','working-manager','solo-agent'}
LEGACY_PROFILE_MAP={'minimal':'basic','standard':'standard','high-assurance':'powerful','web-development':'standard','desktop-development':'standard','custom':'standard'}
PROFILE_NAMES={'basic','standard','powerful'}

class InstallError(RuntimeError): pass

def normalize_profile(name:str)->tuple[str,str|None]:
    raw=(name or 'standard').strip()
    if raw in PROFILE_NAMES:return raw,None
    if raw in LEGACY_PROFILE_MAP:return LEGACY_PROFILE_MAP[raw],raw
    raise InstallError(f'Bilinmeyen profil: {raw}')

def profile_policy_text(profile:str)->str:
    policies={
        'basic':('Basic','Maliyet ve bağlam ekonomisi önceliklidir. Ayrı uzmanı yalnız belirgin kalite/risk değeri varsa çağır; gerekli uzmanı sırf profil nedeniyle kapatma. Bağımsız işleri varsayılan olarak muhafazakâr yürüt, kritik risk dışında ikinci görüş alma ve deterministik kanıt yeterliyse dur.'),
        'standard':('Standard','Dengeli SMART çalışma uygula. Minimum gerekli ekiple başla; bağımsız ve değerli işleri paralel yürütebilirsin, QA/Security/Visual QA çağrılarını risk ve görev etkisine göre yap; kabul ölçütleri ve ilgili kanıt sağlanınca dur.'),
        'powerful':('Powerful','Kalite ve güvence önceliklidir. Bağımsız ve yüksek değerli işleri daha istekli paralelleştir; önemli veya kritik değişikliklerde ilgili bağımsız doğrulamayı daha erken kullan. Aynı rolü varsayılan olarak çoğaltma, aynı model+aynı bağlam+aynı istem ile yinelenen inceleme yapma; gerekli kalite kapıları geçtiğinde dur.')
    }
    title,body=policies[profile]
    return f'## Çalışma Profili: {title}\n\n{body}\n'

def inject_profile_policy(text:str,profile:str)->str:
    marker='\n# '
    pos=text.find(marker)
    if pos<0:return text
    line_end=text.find('\n',pos+2)
    if line_end<0:return text
    return text[:line_end+1]+'\n'+profile_policy_text(profile)+text[line_end+1:]

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

def inject_playwright_policy(text:str, *, role:str, enabled:bool)->str:
    """Playwright MCP araçlarını yalnız visual-qa'ya açar; diğer kurulu ajanlarda deny eder."""
    if not enabled: return text
    if not text.startswith('---\n'): raise InstallError('Rol dosyasında frontmatter bölümü yok.')
    end=text.find('\n---',4)
    if end<0: raise InstallError('Rol dosyasındaki frontmatter bölümü kapanmıyor.')
    head=text[4:end]
    if '\npermission:' not in '\n'+head:
        raise InstallError(f'{role} rolünde permission bölümü yok.')
    if role!='visual-qa': return text
    # Global config playwright_* deny eder; yalnız visual-qa agent override ile allow eder.
    head=head.replace('permission:\n', 'permission:\n  "playwright_*": allow\n', 1)
    return '---\n'+head+'\n---'+text[end+4:]

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

def generate_aux_config(scout_model:str|None, playwright_enabled:bool)->str:
    # OpenCode project .opencode/opencode.json{,c} katmanını merge eder. HHC-owned yüzeyi minimal tut.
    data={'$schema':'https://opencode.ai/config.json'}
    if scout_model:
        data['agent']={'scout':{'model':scout_model}}
    if playwright_enabled:
        data['permission']={'playwright_*':'deny'}
        data['mcp']={'playwright':{'type':'local','command':['npx',f'@playwright/mcp@{PLAYWRIGHT_MCP_VERSION}'],'enabled':True}}
    return json.dumps(data,ensure_ascii=False,indent=2)+'\n'

def validate_model_capabilities(models:dict[str,str], scout_model:str|None, metadata_file:Path|None)->list[dict]:
    """Güvenilir metadata varsa açık zorunlu capability eksiklerini bloklar; UNKNOWN yalnız uyarıdır."""
    from model_advisor import load_catalog, metadata_for, normalize, classify
    catalog,source,error=load_catalog(metadata_file)
    warnings=[]
    if not catalog:
        return [{'role':'*','model':None,'type':'metadata-unavailable','message':error or 'models.dev metadata kullanılamıyor'}]
    checks=dict(models)
    if scout_model: checks['scout']=scout_model
    for role,model in checks.items():
        result=classify(role,normalize(metadata_for(catalog,model)))
        if result['classification']=='INCOMPATIBLE':
            raise InstallError(f'{role} için {model} zorunlu capability eksik: '+', '.join(result['missing_required']))
        if result['classification']=='WARNING':
            warnings.append({'role':role,'model':model,'type':'unknown-capability','unknown_required':result['unknown_required'],'metadata_source':source})
    return warnings

def main()->int:
    ap=argparse.ArgumentParser(description='HHC AI Team Kit proje kurulumu')
    ap.add_argument('--project-path',type=Path,default=Path('.'))
    ap.add_argument('--team-mode',choices=['single','multi'],default='multi',help='single=tek ana muhatap + uzman havuzu; multi=rol bazlı ekip')
    ap.add_argument('--preset',default='standard',help='Çalışma profili: basic, standard (varsayılan), powerful. Eski profil adları migration için kabul edilir.')
    ap.add_argument('--manager-mode',choices=['orchestrator','hands_on'],default='hands_on')
    ap.add_argument('--roles',help='Gelişmiş ayar: kurulacak uzman rolleri sınırla; normal profiller tüm temel uzmanları erişilebilir tutar')
    ap.add_argument('--shared-model',help='Seçili tüm ajanlara aynı sağlayıcı/model kimliğini ata')
    ap.add_argument('--model',action='append',default=[],help='rol=sağlayıcı/model; tekrar edilebilir')
    ap.add_argument('--scout',choices=['enabled','disabled'],help='Native OpenCode Scout kullanımı; yeni kurulumda varsayılan disabled')
    ap.add_argument('--scout-model',help='Scout enabled ise native scout için sağlayıcı/model')
    ap.add_argument('--playwright',choices=['enabled','disabled'],help='browser_ui proje özelliği varsa opt-in Playwright MCP; varsayılan disabled')
    ap.add_argument('--project-characteristic',action='append',default=[],choices=['browser_ui','desktop_ui','backend','cli','library','database','wordpress','containerized','mobile'],help='Gelişmiş ayar: otomatik algılanan proje özelliğine açık sinyal ekle')
    ap.add_argument('--validate-model-capabilities',action='store_true',help='models.dev metadata ile açık zorunlu capability eksiklerini doğrula')
    ap.add_argument('--model-metadata-file',type=Path,help='Test/offline doğrulama için models.dev api.json uyumlu metadata dosyası')
    ap.add_argument('--reconfigure',action='store_true',help='Mevcut HHC ekibini güvenli biçimde yeniden yapılandır')
    ap.add_argument('--update',action='store_true',help="Mevcut state'i koruyarak proje dosyalarını yeni kit ile sessizce senkronla (interaktif değil).")
    ap.add_argument('--force',action='store_true',help='Çakışan HHC hedef dosyalarının üzerine yaz')
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    if args.update and args.reconfigure: raise InstallError('--update ve --reconfigure birlikte kullanılamaz.')
    reconfigure_like=args.reconfigure or args.update
    try:
        project=safe_project(args.project_path); previous=load_state(project)
        profile,legacy_profile=normalize_profile(args.preset)
        preset=load_preset(profile)
        from project_characteristics import detect_project_characteristics
        previous_legacy=(previous or {}).get('preset') if previous else None
        characteristics=detect_project_characteristics(project,args.project_characteristic,legacy_profile or previous_legacy)
        if reconfigure_like and not previous: raise InstallError('--update/--reconfigure mevcut HHC state\'i gerektirir. Önce /hhc-install.')
        if args.update:
            current=(KIT/'VERSION').read_text().strip()
            if previous.get('kit_version')==current:
                print(json.dumps({'status':'UP_TO_DATE','kit_version':current,'project':str(project)}))
                return 0
        if args.shared_model and args.model: raise InstallError('--shared-model ile --model birlikte kullanılamaz.')
        explicit_models=parse_models(args.model); shared_model=valid_model_id(args.shared_model) if args.shared_model else None
        if args.update:
            scout_enabled=bool(previous.get('scout_enabled',False))
            playwright_enabled=bool(previous.get('playwright_enabled',False))
            scout_model=previous.get('scout_model')
        else:
            if args.scout is None:
                scout_enabled=bool(previous.get('scout_enabled',False)) if (reconfigure_like and previous) else False
            else:
                scout_enabled=args.scout=='enabled'
            if args.playwright is None:
                playwright_enabled=bool(previous.get('playwright_enabled',False)) if (reconfigure_like and previous) else False
            else:
                playwright_enabled=args.playwright=='enabled'
            browser_ui=bool(characteristics.get('browser_ui',{}).get('detected'))
            if playwright_enabled and not browser_ui:
                raise InstallError('Playwright MCP yalnız browser_ui proje özelliği doğrulandığında etkinleştirilebilir. Gerekirse gelişmiş --project-characteristic browser_ui override kullanın.')

            if scout_enabled:
                inherited_scout=(previous or {}).get('scout_model') if reconfigure_like else None
                scout_model=valid_model_id(args.scout_model or inherited_scout or '') if (args.scout_model or inherited_scout) else None
                if not scout_model:
                    raise InstallError('Scout etkinse --scout-model sağlayıcı/model zorunludur; manager modeline sessiz devralma yapılmaz.')
            else:
                if args.scout_model:
                    raise InstallError('--scout-model yalnız --scout enabled ile kullanılabilir.')
                scout_model=None

        if not args.update:
            default_specialists=specialist_roles_from_preset(preset['roles'])
            if args.roles:
                specialists=parse_custom_specialists(args.roles)
                if not specialists: raise InstallError('Gelişmiş --roles override en az bir uzman içermelidir.')
            elif legacy_profile=='custom' and previous is None:
                raise InstallError('Legacy custom profil yeni kurulumda Advanced Configuration olarak kullanılır; --roles ile uzmanları açıkça belirtin.')
            elif reconfigure_like and previous and (previous.get('advanced_roles') or previous.get('preset')=='custom'):
                specialists=list(previous.get('advanced_roles') or [r for r in previous.get('roles',[]) if r not in PRIMARY_ROLES])
            else:
                specialists=default_specialists

            team_mode=args.team_mode
            if args.team_mode=='single':
                # Tek Ana Ajan = tek kullanıcı muhatabı. Profil uzmanları kurulmaya ve native Task ile çağrılmaya devam eder.
                primary='working-manager'; manager_mode='hands_on'
                roles=list(dict.fromkeys([primary,*specialists]))
                if explicit_models:
                    raise InstallError('Tek Ana Ajan modunda rol bazlı --model kullanma; tek model için --shared-model kullan.')
                models={role:shared_model for role in roles} if shared_model else {}
            else:
                manager_mode=args.manager_mode
                primary='working-manager' if manager_mode=='hands_on' else 'manager'
                roles=list(dict.fromkeys([primary,*specialists]))
                if shared_model: models={role:shared_model for role in roles}
                else: models=dict(explicit_models)
                missing=set(models)-set(roles)
                if missing: raise InstallError('Seçili ekipte olmayan role model verildi: '+', '.join(sorted(missing)))

            model_warnings=validate_model_capabilities(models,scout_model,args.model_metadata_file) if args.validate_model_capabilities else []
            model_policy='shared' if shared_model else ('per-role' if models else 'inherit')  # yalnız backward-compatible state; wizard bunu sormaz.
            skills=list(preset['skills']); commands=list(preset['commands'])
        else:
            profile,legacy_profile=normalize_profile(previous.get('profile') or previous.get('preset','standard'))
            preset=load_preset(profile)
            characteristics=detect_project_characteristics(project,[],legacy_profile or previous.get('preset'))
            team_mode=previous.get('team_mode','multi'); manager_mode=previous.get('manager_mode')
            primary=previous.get('primary_agent') or ('working-manager' if team_mode=='single' or previous.get('manager_mode','hands_on')=='hands_on' else 'manager')
            # Legacy solo-agent/single normalizasyonu: rc.16 state'inde primary_agent='solo-agent'
            # veya team_mode='single' ise 1.2.0'da working-manager + hands_on olmalı.
            if primary=='solo-agent' or team_mode=='single':
                primary='working-manager'; manager_mode='hands_on'
            advanced_roles=list(previous.get('advanced_roles',[]))
            if not advanced_roles and previous.get('preset')=='custom':
                advanced_roles=[r for r in previous.get('roles',[]) if r not in PRIMARY_ROLES]
            specialists=advanced_roles or specialist_roles_from_preset(preset['roles'])
            roles=list(dict.fromkeys([primary,*specialists]))
            models={k:v for k,v in dict(previous.get('models',{})).items() if k in roles}; shared_model=previous.get('shared_model')
            if shared_model: models={role:shared_model for role in roles}
            model_policy=previous.get('model_policy','inherit')
            model_warnings=previous.get('model_warnings',[])
            skills=list(preset['skills']); commands=list(preset['commands'])
        prev_managed=set(previous.get('managed_files',[])) if previous else set()
        written=[]; preserved=[]; removed=[]; managed=[]; op=project/'.opencode'
        desired=[]
        for role in roles:
            src=KIT/'roles'/f'{role}.md'; dst=op/'agents'/src.name
            role_text=inject_model(src.read_text(encoding='utf-8'),models.get(role))
            if role in ('manager','working-manager'):
                role_text=inject_profile_policy(role_text,profile)
                role_text=inject_scout_policy(role_text,scout_enabled)
            role_text=inject_playwright_policy(role_text,role=role,enabled=playwright_enabled)
            desired.append((src,dst,role_text))
        for skill in skills:
            srcdir=KIT/'skills'/skill
            for src in srcdir.rglob('*'):
                if src.is_file(): desired.append((src,op/'skills'/skill/src.relative_to(srcdir),None))
        for command in commands:
            src=KIT/'commands'/f'{command}.md'; desired.append((src,op/'commands'/src.name,None))
        if scout_enabled or playwright_enabled:
            aux_cfg=project/AUX_CONFIG_REL
            aux_text=generate_aux_config(scout_model if scout_enabled else None,playwright_enabled)
            aux_rel=rel(project,aux_cfg)
            if aux_cfg.exists() and aux_rel not in prev_managed and not args.force:
                raise InstallError('HHC native Scout/Playwright config katmanı güvenle yazılamıyor: .opencode/opencode.jsonc kullanıcı tarafından yönetiliyor. Dosyayı korumak için kurulum durduruldu.')
            desired.append((KIT/'VERSION',aux_cfg,aux_text))

        desired_rel={rel(project,dst) for _,dst,_ in desired}
        if reconfigure_like:
            for old in sorted(prev_managed-desired_rel):
                path=project/old
                if path.is_file():
                    if not args.dry_run:path.unlink()
                    removed.append(str(path))
        for src,dst,text in desired:
            r=rel(project,dst); overwrite=args.force or (reconfigure_like and r in prev_managed)
            owned=write_file(src,dst,project,overwrite=overwrite,dry=args.dry_run,text=text,written=written,preserved=preserved)
            if owned or r in prev_managed:managed.append(r)

        cfg=project/'opencode.jsonc'; cfg_created=False; cfg_hash=None; cfg_existed_before=cfg.exists(); cfg_action=None
        previous_cfg_created=bool(previous and previous.get('config_created_by_hhc')); previous_cfg_hash=(previous or {}).get('config_sha256')
        if cfg.exists():
            expected_cfg=generate_config(primary)
            if not previous and cfg.read_text(encoding='utf-8')==expected_cfg:
                previous_cfg_created=True; previous_cfg_hash=sha_file(cfg)
            can_update=args.force or (reconfigure_like and previous_cfg_created and previous_cfg_hash and sha_file(cfg)==previous_cfg_hash)
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

        advanced_roles=list(specialists) if args.roles or (previous and (previous.get('advanced_roles') or previous.get('preset')=='custom')) else []
        state={'schema_version':2,'kit_version':(KIT/'VERSION').read_text().strip(),'team_mode':team_mode,
               'preset':profile,'profile':profile,'profile_policy':preset.get('policy',{}),'manager_mode':manager_mode,'primary_agent':primary,'roles':roles,'advanced_roles':advanced_roles,'skills':skills,'commands':commands,
               'project_characteristics':characteristics,'model_policy':model_policy,'shared_model':shared_model,'models':models,'scout_enabled':scout_enabled,'scout_model':scout_model,'playwright_enabled':playwright_enabled,'model_warnings':model_warnings,'managed_files':sorted(managed),
               'config_created_by_hhc':cfg_created,'config_sha256':cfg_hash}
        if not args.dry_run:
            state_path=project/STATE_REL; state_path.parent.mkdir(parents=True,exist_ok=True)
            state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline=''); remove_empty_dirs(op)
        config_result={'path':str(cfg),'action':cfg_action,'existed_before':cfg_existed_before,'managed_by_hhc':cfg_created,
                       'notice':('Mevcut opencode.jsonc korundu; HHC bu dosyadaki default_agent, subagent_depth veya compaction değerlerini değiştirmedi. Mevcut OpenCode yapılandırmanız geçerlidir.' if cfg_action=='preserved-existing-config' else None)}
        print(json.dumps({'status':'DRY_RUN' if args.dry_run else ('UPDATED' if args.update else ('RECONFIGURED' if args.reconfigure else 'COMPLETE')),'project':str(project),
                          **{k:state[k] for k in ('team_mode','preset','profile','profile_policy','manager_mode','primary_agent','roles','advanced_roles','skills','commands','project_characteristics','model_policy','shared_model','models','scout_enabled','scout_model','playwright_enabled','model_warnings')},
                          'config':config_result,'written':written,'removed':removed,'preserved_existing':list(dict.fromkeys(preserved))},ensure_ascii=False,indent=2))
        if preserved:print('NOT: HHC tarafından güvenle yönetilemeyen mevcut dosyalar korunmuştur.',file=sys.stderr)
        return 0
    except (OSError,ValueError,json.JSONDecodeError,InstallError) as e:
        print(f'HHC-INSTALL-001: {e}',file=sys.stderr); return 2
if __name__=='__main__':raise SystemExit(main())
