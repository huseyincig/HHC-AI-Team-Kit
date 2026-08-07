#!/usr/bin/env python3
"""HHC model capability/maliyet danışmanı.

OpenCode model keşfini değiştirmez. models.dev metadata erişilebilirse seçim aşamasında
rol uyumluluğu ve maliyet/context bilgisi üretir; erişilemezse UNKNOWN ile güvenli şekilde
devam eder. Runtime model router değildir.
"""
from __future__ import annotations
import argparse, json, os, urllib.request
from pathlib import Path

from model_discovery import discover, MODEL_RE

DEFAULT_URL='https://models.dev/api.json'

ROLE_PROFILES={
    'manager': {'required':['tool_call'], 'preferred':['reasoning','context']},
    'working-manager': {'required':['tool_call'], 'preferred':['reasoning','context']},
    'architect': {'required':[], 'preferred':['reasoning','context','tool_call']},
    'repository-explorer': {'required':['tool_call'], 'preferred':['low_cost','context']},
    'coder': {'required':['tool_call'], 'preferred':['reasoning','context']},
    'qa-reviewer': {'required':[], 'preferred':['reasoning','tool_call']},
    'security-reviewer': {'required':[], 'preferred':['reasoning','tool_call','context']},
    'visual-qa': {'required':['tool_call','image_input'], 'preferred':['context']},
    'scout': {'required':['tool_call'], 'preferred':['low_cost','context','reasoning']},
}


def _read_json_url(url:str, timeout:float=4.0)->dict:
    req=urllib.request.Request(url,headers={'User-Agent':'HHC-AI-Team-Kit/model-advisor'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=json.loads(r.read().decode('utf-8'))
    return data if isinstance(data,dict) else {}


def load_catalog(path:Path|None=None)->tuple[dict,str|None,str|None]:
    try:
        if path:
            data=json.loads(path.read_text(encoding='utf-8'))
            return (data if isinstance(data,dict) else {}),str(path),None
        url=os.environ.get('HHC_MODELS_DEV_URL',DEFAULT_URL)
        return _read_json_url(url),url,None
    except Exception as e:
        return {},None,f'{type(e).__name__}: {e}'


def metadata_for(catalog:dict, model_ref:str)->dict|None:
    if '/' not in model_ref:return None
    provider,model_id=model_ref.split('/',1)
    p=catalog.get(provider)
    if not isinstance(p,dict): return None
    models=p.get('models')
    if not isinstance(models,dict): return None
    m=models.get(model_id)
    return m if isinstance(m,dict) else None


def normalize(meta:dict|None)->dict:
    if not isinstance(meta,dict):
        return {'known':False,'tool_call':None,'reasoning':None,'image_input':None,'attachment':None,
                'context':None,'output_limit':None,'cost_input':None,'cost_output':None,'status':None}
    modalities=meta.get('modalities') if isinstance(meta.get('modalities'),dict) else {}
    inputs=modalities.get('input') if isinstance(modalities.get('input'),list) else None
    image_input=('image' in inputs) if inputs is not None else None
    limit=meta.get('limit') if isinstance(meta.get('limit'),dict) else {}
    cost=meta.get('cost') if isinstance(meta.get('cost'),dict) else {}
    return {
        'known':True,
        'tool_call':meta.get('tool_call') if isinstance(meta.get('tool_call'),bool) else None,
        'reasoning':meta.get('reasoning') if isinstance(meta.get('reasoning'),bool) else None,
        'image_input':image_input,
        'attachment':meta.get('attachment') if isinstance(meta.get('attachment'),bool) else None,
        'context':limit.get('context') if isinstance(limit.get('context'),(int,float)) else None,
        'output_limit':limit.get('output') if isinstance(limit.get('output'),(int,float)) else None,
        'cost_input':cost.get('input') if isinstance(cost.get('input'),(int,float)) else None,
        'cost_output':cost.get('output') if isinstance(cost.get('output'),(int,float)) else None,
        'status':meta.get('status') if isinstance(meta.get('status'),str) else None,
    }


def classify(role:str, norm:dict)->dict:
    profile=ROLE_PROFILES.get(role,{'required':[],'preferred':[]})
    missing=[]; unknown=[]
    for cap in profile['required']:
        value=norm.get(cap)
        if value is False: missing.append(cap)
        elif value is None: unknown.append(cap)
    if missing: level='INCOMPATIBLE'
    elif unknown or not norm.get('known'): level='WARNING'
    else:
        preferred_hits=0
        for cap in profile['preferred']:
            if cap=='low_cost':
                if isinstance(norm.get('cost_input'),(int,float)) and isinstance(norm.get('cost_output'),(int,float)): preferred_hits+=1
            elif cap=='context':
                if isinstance(norm.get('context'),(int,float)) and norm['context']>=128000: preferred_hits+=1
            elif norm.get(cap) is True: preferred_hits+=1
        level='RECOMMENDED' if preferred_hits>=max(1,len(profile['preferred'])//2) else 'COMPATIBLE'
    score=0
    if level!='INCOMPATIBLE': score+=100
    if norm.get('tool_call') is True: score+=20
    if norm.get('reasoning') is True: score+=10
    if norm.get('image_input') is True and role=='visual-qa': score+=30
    if isinstance(norm.get('context'),(int,float)): score+=min(20,int(norm['context']/100000))
    if isinstance(norm.get('cost_input'),(int,float)) and isinstance(norm.get('cost_output'),(int,float)):
        score+=max(0,20-int(norm['cost_input']+norm['cost_output']))
    if norm.get('status')=='deprecated': score-=100
    return {'classification':level,'missing_required':missing,'unknown_required':unknown,'score':score,'profile':profile}


def advise(models:list[str],roles:list[str],catalog:dict)->dict:
    by_role={}
    for role in roles:
        rows=[]
        for ref in models:
            norm=normalize(metadata_for(catalog,ref)); result=classify(role,norm)
            rows.append({'model':ref,**norm,**result})
        rows.sort(key=lambda x:(x['classification']=='INCOMPATIBLE',-x['score'],x['model']))
        by_role[role]=rows
    return by_role


def main()->int:
    ap=argparse.ArgumentParser(description='HHC role-model capability ve maliyet danışmanı')
    ap.add_argument('--project-path',type=Path,default=Path('.'))
    ap.add_argument('--role',action='append',default=[])
    ap.add_argument('--model',action='append',default=[])
    ap.add_argument('--refresh',action='store_true')
    ap.add_argument('--metadata-file',type=Path)
    args=ap.parse_args()
    roles=args.role or sorted(ROLE_PROFILES)
    unknown=set(roles)-set(ROLE_PROFILES)
    if unknown:
        print(json.dumps({'ok':False,'error':'Bilinmeyen rol: '+', '.join(sorted(unknown))},ensure_ascii=False)); return 2
    discovered=discover(args.project_path,refresh=args.refresh) if not args.model else {'ok':True,'models':args.model,'source':'explicit'}
    models=[m for m in discovered.get('models',[]) if isinstance(m,str) and MODEL_RE.match(m)]
    catalog,source,error=load_catalog(args.metadata_file)
    result={'ok':bool(models),'models':models,'model_source':discovered.get('source'),'metadata_source':source,
            'metadata_available':bool(catalog),'metadata_error':error,'roles':advise(models,roles,catalog),
            'notice':('models.dev metadata alınamadı; model seçimi engellenmez, capability bilgisi UNKNOWN/WARNING kabul edilir.' if not catalog else None)}
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
