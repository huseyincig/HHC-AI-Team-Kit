#!/usr/bin/env python3
"""HHC için küçük, deterministik ve çok-etiketli proje özelliği algılayıcısı."""
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path

CHARACTERISTICS=(
    'browser_ui','desktop_ui','backend','cli','library','database','wordpress','containerized','mobile'
)
PRUNE={'.git','node_modules','vendor','.venv','venv','dist','build','target','.next','.cache','.pytest_cache'}


def _read(path:Path, limit:int=256_000)->str:
    try:
        return path.read_text(encoding='utf-8',errors='ignore')[:limit]
    except OSError:
        return ''


def _package_json(root:Path)->dict:
    p=root/'package.json'
    if not p.is_file(): return {}
    try:return json.loads(_read(p))
    except json.JSONDecodeError:return {}


def _walk_names(root:Path, max_files:int=4000, max_depth:int=5)->set[str]:
    names=set(); base_depth=len(root.parts); count=0
    for cur,dirs,files in os.walk(root):
        curp=Path(cur); depth=len(curp.parts)-base_depth
        dirs[:]=[d for d in dirs if d not in PRUNE and not d.startswith('.hhc-bootstrap')]
        if depth>=max_depth: dirs[:]=[]
        for d in dirs:
            names.add(d.lower()); count+=1
            if count>=max_files:return names
        for f in files:
            names.add(f.lower()); count+=1
            if count>=max_files:return names
    return names


def detect_project_characteristics(root:Path, forced:list[str]|None=None, legacy_profile:str|None=None)->dict:
    root=root.expanduser().resolve(); scores={k:0 for k in CHARACTERISTICS}; evidence={k:[] for k in CHARACTERISTICS}
    def hit(key:str, points:int, why:str):
        scores[key]+=points
        if why not in evidence[key]: evidence[key].append(why)

    names=_walk_names(root)
    pkg=_package_json(root)
    deps={**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})} if isinstance(pkg,dict) else {}
    depnames={str(x).lower() for x in deps}

    frontend={'react','react-dom','vue','@angular/core','svelte','next','nuxt','vite','astro','solid-js','@remix-run/react'}
    if depnames & frontend: hit('browser_ui',2,'package.json frontend bağımlılıkları')
    if 'index.html' in names and ({'vite.config.js','vite.config.ts','vite.config.mjs','next.config.js','next.config.mjs','next.config.ts'} & names):
        hit('browser_ui',2,'HTML + frontend yapılandırması')
    if (root/'wwwroot').is_dir(): hit('browser_ui',1,'wwwroot dizini')

    desktopdeps={'electron','@tauri-apps/api','@tauri-apps/cli'}
    if depnames & desktopdeps: hit('desktop_ui',2,'desktop JavaScript bağımlılığı')
    if 'tauri.conf.json' in names or 'tauri.conf.json5' in names: hit('desktop_ui',2,'Tauri yapılandırması')

    csproj_text='\n'.join(_read(p) for p in list(root.glob('*.csproj'))[:20])
    if not csproj_text:
        csproj_text='\n'.join(_read(p) for p in list(root.glob('*/*.csproj'))[:20])
    cslow=csproj_text.lower()
    if any(x in cslow for x in ('<usewpf>true','<usewindowsforms>true','avalonia','microsoft.ui.xaml','maui')):
        hit('desktop_ui',2,'.NET masaüstü UI işareti')
    if 'microsoft.net.sdk.web' in cslow:
        hit('backend',2,'.NET Web SDK')
        if (root/'wwwroot').is_dir(): hit('browser_ui',1,'.NET web statik içerik dizini')
    if '<outputtype>exe' in cslow and scores['desktop_ui']==0: hit('cli',2,'.NET console executable')
    if '<outputtype>library' in cslow: hit('library',2,'.NET library output')

    backend_js={'express','fastify','koa','@nestjs/core','hapi','elysia'}
    if depnames & backend_js: hit('backend',2,'package.json backend bağımlılıkları')
    if isinstance(pkg,dict) and pkg.get('bin'): hit('cli',2,'package.json bin alanı')
    if isinstance(pkg,dict) and any(pkg.get(k) for k in ('main','module','types','exports')) and not pkg.get('bin'):
        hit('library',1,'package.json library giriş alanları')

    pyproject=_read(root/'pyproject.toml').lower()
    if any(x in pyproject for x in ('django','fastapi','flask','starlette')): hit('backend',2,'Python web/backend bağımlılığı')
    if re.search(r'\[(project\.scripts|tool\.poetry\.scripts)\]',pyproject): hit('cli',2,'Python CLI script tanımı')

    composer=_read(root/'composer.json').lower()
    if any(x in composer for x in ('laravel/framework','symfony/framework-bundle')): hit('backend',2,'PHP backend framework bağımlılığı')
    if 'wordpress' in composer: hit('wordpress',1,'Composer WordPress işareti')

    if (root/'wp-content').exists() or (root/'wp-config.php').is_file():
        hit('wordpress',2,'WordPress dizin/yapılandırması'); hit('browser_ui',2,'WordPress browser-facing proje')
    elif any('plugin name:' in _read(p,16_000).lower() for p in list(root.glob('*.php'))[:30]):
        hit('wordpress',2,'WordPress eklenti başlığı'); hit('browser_ui',1,'WordPress eklenti UI olasılığı')

    if (root/'Dockerfile').is_file() or (root/'docker-compose.yml').is_file() or (root/'docker-compose.yaml').is_file() or (root/'compose.yml').is_file() or (root/'compose.yaml').is_file():
        hit('containerized',2,'Docker/Compose yapılandırması')
    compose='\n'.join(_read(root/x).lower() for x in ('docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml'))
    if any(x in compose for x in ('postgres','mysql','mariadb','mongodb','redis')): hit('database',2,'Compose veri servisi')

    if 'androidmanifest.xml' in names or 'pubspec.yaml' in names or any(x.endswith('.xcodeproj') for x in names): hit('mobile',2,'mobil proje manifesti')
    if depnames & {'react-native','expo'}: hit('mobile',2,'mobil JavaScript bağımlılığı')

    if {'migrations','migration'} & {p.name.lower() for p in root.iterdir() if p.is_dir()}:
        hit('database',1,'migration dizini')
    orm_markers={'prisma','sequelize','typeorm','drizzle-orm','mongoose','sqlalchemy','django'}
    if depnames & orm_markers or any(x in pyproject for x in ('sqlalchemy','django','psycopg','pymysql')):
        hit('database',1,'ORM/veritabanı bağımlılığı')

    if (root/'Cargo.toml').is_file() and (root/'src/main.rs').is_file(): hit('cli',1,'Rust binary entrypoint')
    if (root/'Cargo.toml').is_file() and (root/'src/lib.rs').is_file(): hit('library',2,'Rust library entrypoint')
    if (root/'go.mod').is_file() and any((root/x).is_file() for x in ('main.go','cmd/main.go')): hit('cli',1,'Go executable entrypoint')

    legacy={'web-development':'browser_ui','desktop-development':'desktop_ui'}
    if legacy_profile in legacy: hit(legacy[legacy_profile],2,f'legacy profile migration: {legacy_profile}')
    for key in forced or []:
        if key not in CHARACTERISTICS: raise ValueError(f'Bilinmeyen proje özelliği: {key}')
        hit(key,2,'kullanıcı gelişmiş override')

    # Tek zayıf ipucu yerine iki puanlık güçlü veya birden fazla bağımsız sinyal gerekir.
    detected={k:{'detected':scores[k]>=2,'score':scores[k],'evidence':evidence[k]} for k in CHARACTERISTICS}
    return detected


def main()->int:
    ap=argparse.ArgumentParser(description='HHC proje özelliklerini çok-etiketli ve deterministik algılar')
    ap.add_argument('--project-path',type=Path,default=Path('.'))
    ap.add_argument('--force',action='append',default=[],choices=CHARACTERISTICS,help='Gelişmiş kullanım: özelliği açıkça ekle')
    ap.add_argument('--legacy-profile')
    args=ap.parse_args()
    print(json.dumps(detect_project_characteristics(args.project_path,args.force,args.legacy_profile),ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
