#!/usr/bin/env python3
"""OpenCode model listesini salt-okunur keşfeder.

Öncelik:
1) OpenCode Desktop kullanıcı görünürlük state'i varsa `visibility == "show"` modelleri.
   Windows Desktop'ta bu, kullanıcının `/models` görünürlüğüyle doğrulanan yerel state'tir.
2) Desktop state yoksa/boşsa resmî `opencode models` CLI çıktısı.
3) CLI da kullanılamıyorsa, yalnız yapılandırıldığı doğrulanabilen provider'lara ait yerel
   cache girdileri + config'te açıkça tanımlı modeller BEST-EFFORT fallback olarak kullanılır.

Desktop state ve cache dosya biçimleri OpenCode public API'si değildir. Credential dosyaları
direkt okunmaz.
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess
from pathlib import Path

MODEL_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._/-]*$')
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def desktop_state_candidates() -> list[Path]:
    """OpenCode Desktop'ın kullanıcı state'i için bilinen yerel adayları döndürür.

    `opencode.global.dat` public/stable API değildir; yalnız salt-okunur BEST-EFFORT kaynak
    olarak kullanılır. Windows Desktop'ta APPDATA yolu gerçek `/models` görünürlüğüyle
    doğrulanmıştır.
    """
    out: list[Path] = []
    appdata = os.environ.get('APPDATA')
    if appdata:
        out.append(Path(appdata) / 'ai.opencode.desktop' / 'opencode.global.dat')
    return list(dict.fromkeys(p.expanduser() for p in out))


def desktop_visible_models(path: Path) -> list[str]:
    """Desktop state içindeki açıkça `show` işaretli provider/model çiftlerini çıkarır."""
    try:
        root = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(root, dict):
        return []
    model_state = root.get('model')
    if isinstance(model_state, str):
        try:
            model_state = json.loads(model_state)
        except json.JSONDecodeError:
            return []
    if not isinstance(model_state, dict):
        return []
    users = model_state.get('user')
    if not isinstance(users, list):
        return []
    found: set[str] = set()
    for item in users:
        if not isinstance(item, dict) or item.get('visibility') != 'show':
            continue
        provider = item.get('providerID')
        model = item.get('modelID')
        if not isinstance(provider, str) or not isinstance(model, str):
            continue
        value = f'{provider.strip()}/{model.strip()}'
        if MODEL_RE.match(value):
            found.add(value)
    return sorted(found)


def models_from_desktop_state() -> tuple[list[str], list[str]]:
    checked: list[str] = []
    for path in desktop_state_candidates():
        checked.append(str(path))
        if not path.is_file():
            continue
        models = desktop_visible_models(path)
        if models:
            return models, checked
    return [], checked


def cache_candidates() -> list[Path]:
    home = Path.home()
    roots: list[Path] = []
    if os.environ.get('XDG_CACHE_HOME'):
        roots.append(Path(os.environ['XDG_CACHE_HOME']))
    if os.name == 'nt' and os.environ.get('USERPROFILE'):
        roots.append(Path(os.environ['USERPROFILE']) / '.cache')
    roots.append(home / '.cache')
    out: list[Path] = []
    for root in roots:
        # UNDOCUMENTED / BEST-EFFORT: OpenCode public API değildir.
        out.extend([root / 'opencode' / 'models.json', root / 'opencode.json'])
    return list(dict.fromkeys(p.expanduser() for p in out))


def _strip_jsonc(text: str) -> str:
    """Basit JSONC yorumlarını string içeriklerini bozmadan kaldırır."""
    out=[]; i=0; in_string=False; escaped=False
    while i < len(text):
        c=text[i]
        if in_string:
            out.append(c)
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': in_string=False
            i+=1; continue
        if c=='"': in_string=True; out.append(c); i+=1; continue
        if c=='/' and i+1 < len(text) and text[i+1]=='/':
            i+=2
            while i < len(text) and text[i] not in '\r\n': i+=1
            continue
        if c=='/' and i+1 < len(text) and text[i+1]=='*':
            end=text.find('*/',i+2)
            i=len(text) if end<0 else end+2
            continue
        out.append(c); i+=1
    # OpenCode JSONC trailing comma kabul eder; stdlib json için temizle.
    return re.sub(r',\s*([}\]])', r'\1', ''.join(out))


def _load_jsonc(path: Path) -> dict:
    try:
        data=json.loads(_strip_jsonc(path.read_text(encoding='utf-8')))
        return data if isinstance(data,dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def config_candidates(project: Path) -> list[Path]:
    out=[]
    explicit=os.environ.get('OPENCODE_CONFIG')
    if explicit: out.append(Path(explicit).expanduser())
    xdg=Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
    out.extend([xdg/'opencode'/'opencode.json', xdg/'opencode'/'opencode.jsonc'])
    out.extend([project/'opencode.json', project/'opencode.jsonc'])
    return list(dict.fromkeys(p.resolve() if p.exists() else p for p in out))


def configured_from_files(project: Path) -> tuple[set[str], set[str]]:
    """Belgelendirilmiş config yüzeyinden provider kimlikleri ve açık model ID'leri çıkarır."""
    providers:set[str]=set(); models:set[str]=set()
    for path in config_candidates(project):
        if not path.is_file(): continue
        data=_load_jsonc(path)
        pmap=data.get('provider')
        if isinstance(pmap,dict):
            for provider_id, body in pmap.items():
                if not isinstance(provider_id,str): continue
                providers.add(provider_id)
                if isinstance(body,dict) and isinstance(body.get('models'),dict):
                    for model_id in body['models']:
                        value=f'{provider_id}/{model_id}'
                        if MODEL_RE.match(value): models.add(value)
        for key in ('model','small_model'):
            value=data.get(key)
            if isinstance(value,str) and MODEL_RE.match(value.strip()):
                value=value.strip(); models.add(value); providers.add(value.split('/',1)[0])
    return providers,models


def models_from_cli(project: Path, refresh: bool = False) -> list[str]:
    exe=shutil.which('opencode')
    if not exe: return []
    try:
        cmd=[exe,'models']
        if refresh: cmd.append('--refresh')
        p=subprocess.run(cmd,cwd=project,capture_output=True,text=True,timeout=30 if refresh else 15)
    except (OSError, subprocess.TimeoutExpired): return []
    if p.returncode!=0: return []
    found=[]
    for raw in (p.stdout or '').splitlines():
        value=raw.strip()
        if MODEL_RE.match(value): found.append(value)
    return sorted(dict.fromkeys(found))


def auth_list_text(project: Path) -> str:
    """Credential dosyasını okumadan resmî CLI üzerinden authenticated provider görünümünü alır."""
    exe=shutil.which('opencode')
    if not exe: return ''
    try:
        p=subprocess.run([exe,'auth','list'],cwd=project,capture_output=True,text=True,timeout=10)
    except (OSError,subprocess.TimeoutExpired): return ''
    return ANSI_RE.sub('',(p.stdout or '')+'\n'+(p.stderr or '')) if p.returncode==0 else ''


def collect_models(node, provider_hint: str|None=None, out:set[str]|None=None)->set[str]:
    """UNDOCUMENTED cache JSON'undan aday provider/model kimliklerini toplar; UI filtresi sonra uygulanır."""
    if out is None: out=set()
    if isinstance(node,str):
        value=node.strip()
        if MODEL_RE.match(value): out.add(value)
        return out
    if isinstance(node,list):
        for item in node: collect_models(item,provider_hint,out)
        return out
    if not isinstance(node,dict): return out
    direct=node.get('id')
    if isinstance(direct,str) and MODEL_RE.match(direct.strip()): out.add(direct.strip())
    provider=node.get('provider') or node.get('providerID') or node.get('provider_id') or provider_hint
    model=node.get('model') or node.get('modelID') or node.get('model_id')
    if isinstance(provider,str) and isinstance(model,str):
        value=f'{provider}/{model}'
        if MODEL_RE.match(value): out.add(value)
    models=node.get('models')
    node_provider=node.get('id') if isinstance(node.get('id'),str) and '/' not in node.get('id') else provider_hint
    if isinstance(models,dict) and node_provider:
        for model_id,body in models.items():
            if isinstance(model_id,str):
                value=f'{node_provider}/{model_id}'
                if MODEL_RE.match(value): out.add(value)
            collect_models(body,node_provider,out)
    for key,value in node.items():
        if key in {'models','id','provider','providerID','provider_id','model','modelID','model_id'}: continue
        hint=provider_hint
        if isinstance(key,str) and re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$',key): hint=key
        collect_models(value,hint,out)
    return out


def cache_model_candidates(path: Path)->list[str]:
    try: data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,UnicodeDecodeError,json.JSONDecodeError): return []
    return sorted(collect_models(data))


def _provider_mentioned(text: str, provider: str)->bool:
    return bool(re.search(r'(?<![A-Za-z0-9._-])'+re.escape(provider)+r'(?![A-Za-z0-9._-])',text,re.I))


def fallback_models(project: Path)->tuple[list[str],list[str],set[str]]:
    configured_providers, explicit_models=configured_from_files(project)
    checked=[]; candidates:set[str]=set(explicit_models)
    cache_models:set[str]=set()
    for path in cache_candidates():
        checked.append(str(path))
        if path.is_file(): cache_models.update(cache_model_candidates(path))
    cache_providers={m.split('/',1)[0] for m in cache_models}
    auth_text=auth_list_text(project)
    authenticated={p for p in cache_providers if _provider_mentioned(auth_text,p)}
    active=configured_providers|authenticated
    # Kritik güvenlik/UX kuralı: aktifliği doğrulanamayan cache provider'larını UI'a sızdırma.
    candidates.update(m for m in cache_models if m.split('/',1)[0] in active)
    return sorted(candidates),checked,active


def discover(project: Path, refresh: bool=False)->dict:
    project=project.expanduser().resolve()
    desktop,checked_desktop=models_from_desktop_state()
    if desktop:
        return {'ok':True,'source':'opencode-desktop-state','source_kind':'desktop-user-visibility-state',
                'documented':False,'best_effort':True,'refreshed':False,'project':str(project),
                'models':desktop,'count':len(desktop),'checked':checked_desktop,
                'notice':'OpenCode Desktop yerel state içindeki visibility=show model tercihleri kullanıldı. Bu dosya public/stable OpenCode API değildir; salt-okunur kullanılır.'}
    cli_cmd='opencode models --refresh' if refresh else 'opencode models'
    cli=models_from_cli(project,refresh=refresh)
    if cli:
        return {'ok':True,'source':'opencode-cli','source_kind':'official-cli','documented':True,'best_effort':False,
                'refreshed':refresh,'project':str(project),'models':cli,'count':len(cli),'checked':[*checked_desktop,cli_cmd]}
    models,checked_cache,active=fallback_models(project)
    checked=[*checked_desktop,cli_cmd,*checked_cache]
    if models:
        return {'ok':True,'source':'configured-fallback','source_kind':'best-effort-config-cache','documented':False,
                'best_effort':True,'refreshed':refresh,'project':str(project),'models':models,'count':len(models),
                'active_providers':sorted(active),'checked':checked,
                'notice':'OpenCode CLI model listesi alınamadı; yalnız yapılandırıldığı/bağlı olduğu doğrulanabilen provider verileri BEST-EFFORT fallback olarak kullanıldı. Cache formatı UNDOCUMENTED durumdadır.'}
    return {'ok':False,'source':None,'source_kind':None,'documented':False,'best_effort':False,
            'refreshed':refresh,'project':str(project),'models':[],'count':0,'checked':checked,
            'message':'Bu proje için kullanılabilir OpenCode model listesi bulunamadı. Provider bağlantısını/config yapılandırmasını kontrol edin veya tam provider/model kimliğini elle girin.'}


def main()->int:
    ap=argparse.ArgumentParser(description='Mevcut proje için OpenCode model listesini keşfet')
    ap.add_argument('--project-path',type=Path,default=Path('.'))
    ap.add_argument('--refresh',action='store_true',help='Resmî `opencode models --refresh` komutunu açıkça çalıştır')
    args=ap.parse_args()
    print(json.dumps(discover(args.project_path,refresh=args.refresh),ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
