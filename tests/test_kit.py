import json, os, subprocess, sys, zipfile

import pytest
from pathlib import Path
KIT=Path(__file__).resolve().parents[1]
def run(*args): return subprocess.run([sys.executable,*map(str,args)],text=True,capture_output=True)
def test_validate(): assert run(KIT/'scripts/validate.py').returncode==0
def test_clean_install(tmp_path):
    p=tmp_path/'app'; r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal'); assert r.returncode==0, r.stderr
    assert (p/'.opencode/agents/working-manager.md').is_file(); assert (p/'.opencode/agents/coder.md').is_file(); assert (p/'opencode.jsonc').is_file(); assert not (p/'.opencode/hhc').exists()
def test_model_optional_and_explicit(tmp_path):
    p=tmp_path/'app'; r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--model','coder=provider/model'); assert r.returncode==0
    assert 'model: provider/model' in (p/'.opencode/agents/coder.md').read_text(encoding='utf-8'); assert '\nmodel:' not in (p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
def test_existing_config_preserved(tmp_path):
    p=tmp_path/'app'; p.mkdir(); (p/'opencode.jsonc').write_text('{"model":"x/y"}')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal'); assert r.returncode==0;     assert (p/'opencode.jsonc').read_text(encoding='utf-8')=='{"model":"x/y"}'
def test_idempotent(tmp_path):
    p=tmp_path/'app'; assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0; before={x.relative_to(p):x.read_bytes() for x in p.rglob('*') if x.is_file()}; assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0; after={x.relative_to(p):x.read_bytes() for x in p.rglob('*') if x.is_file()}; assert before==after
def test_release_clean(tmp_path):
    r=run(KIT/'scripts/release-build.py','--out',tmp_path); assert r.returncode==0, r.stderr
    z=next(tmp_path.glob('*.zip'))
    with zipfile.ZipFile(z) as f:
        names=f.namelist(); assert not any(n.startswith('.git/') or n.startswith('.opencode/') or '__pycache__' in n or '.hhc-bootstrap-venv' in n or n.startswith('tests/') for n in names)


def test_custom_roles(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','custom','--roles','coder,qa-reviewer')
    assert r.returncode==0, r.stderr
    assert (p/'.opencode/agents/working-manager.md').is_file()
    assert (p/'.opencode/agents/coder.md').is_file()
    assert (p/'.opencode/agents/qa-reviewer.md').is_file()
    assert not (p/'.opencode/agents/architect.md').exists()


def test_roles_are_advanced_override_not_profile_only(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard','--roles','coder,qa-reviewer')
    assert r.returncode==0, r.stderr
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['profile']=='standard'
    assert state['advanced_roles']==['coder','qa-reviewer']
    assert state['roles']==['working-manager','coder','qa-reviewer']

def test_single_main_agent_keeps_profile_specialists_and_shared_model(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--team-mode','single','--preset','web-development','--shared-model','provider/shared')
    assert r.returncode==0, r.stderr
    agents={x.stem for x in (p/'.opencode/agents').glob('*.md')}
    assert {'working-manager','architect','repository-explorer','coder','qa-reviewer','visual-qa'} <= agents
    assert 'solo-agent' not in agents
    for name in agents:
        assert 'model: provider/shared' in (p/f'.opencode/agents/{name}.md').read_text(encoding='utf-8')
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['team_mode']=='single' and state['primary_agent']=='working-manager'
    assert state['manager_mode']=='hands_on' and state['model_policy']=='shared'


def test_single_custom_adds_working_manager_automatically(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--team-mode','single','--preset','custom','--roles','coder,visual-qa','--shared-model','provider/shared')
    assert r.returncode==0, r.stderr
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['roles']==['working-manager','coder','visual-qa']


def test_custom_multi_requires_at_least_one_specialist(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--team-mode','multi','--preset','custom')
    assert r.returncode!=0


def test_shared_model_applies_to_all_multi_agents(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--shared-model','provider/shared')
    assert r.returncode==0, r.stderr
    for name in ('working-manager','coder','qa-reviewer'):
        assert 'model: provider/shared' in (p/f'.opencode/agents/{name}.md').read_text(encoding='utf-8')


def test_shared_and_per_role_models_are_mutually_exclusive(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--shared-model','provider/shared','--model','coder=provider/other')
    assert r.returncode!=0


def test_reconfigure_profile_changes_policy_not_roster_and_keeps_user_files(tmp_path):
    p=tmp_path/'app'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0
    user=p/'.opencode/agents/my-private-agent.md'; user.write_text('kullanıcı dosyası',encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','basic','--manager-mode','orchestrator','--shared-model','provider/team')
    assert r.returncode==0, r.stderr
    assert user.read_text(encoding='utf-8')=='kullanıcı dosyası'
    assert (p/'.opencode/agents/architect.md').exists()
    assert (p/'.opencode/agents/security-reviewer.md').exists()
    assert (p/'.opencode/agents/manager.md').exists()
    assert not (p/'.opencode/agents/working-manager.md').exists()
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['profile']=='basic' and state['preset']=='basic'
    assert state['manager_mode']=='orchestrator'

def test_reconfigure_requires_state(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','minimal')
    assert r.returncode!=0


def test_existing_user_collision_not_claimed_as_hhc_managed(tmp_path):
    p=tmp_path/'app'; target=p/'.opencode/agents/coder.md'; target.parent.mkdir(parents=True); target.write_text('özel coder',encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert '.opencode/agents/coder.md' not in state['managed_files']
    assert target.read_text(encoding='utf-8')=='özel coder'


def test_global_bootstrap_contains_reconfigure(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME',str(tmp_path/'config'))
    monkeypatch.setenv('XDG_DATA_HOME',str(tmp_path/'data'))
    r=run(KIT/'scripts/install_global.py','--install')
    assert r.returncode==0, r.stderr
    root=tmp_path/'config/opencode/commands'
    assert (root/'hhc-install.md').is_file()
    assert (root/'hhc-reconfigure.md').is_file()
    text=(root/'hhc-install.md').read_text(encoding='utf-8')
    assert 'Çalışma profili — ilk gerçek kullanıcı kararı' in text
    assert 'Basic' in text and 'Standard' in text and 'Powerful' in text
    assert 'normal kullanıcıya SORMA' in text and '--team-mode multi --manager-mode hands_on' in text
    assert 'model_advisor.py' in text and 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in text

def test_adopts_identical_pre_state_install_for_future_reconfigure(tmp_path):
    p=tmp_path/'app'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0
    state=p/'.opencode/hhc-team.json'; state.unlink()
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    data=json.loads(state.read_text(encoding='utf-8'))
    assert '.opencode/agents/architect.md' in data['managed_files']
    assert data['config_created_by_hhc'] is True
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','basic')
    assert r.returncode==0, r.stderr
    # Profile is policy-only: specialist availability remains intact.
    assert (p/'.opencode/agents/architect.md').exists()
    assert (p/'.opencode/agents/security-reviewer.md').exists()

def test_legacy_custom_requires_explicit_advanced_roles_on_new_install(tmp_path):
    p=tmp_path/'multi'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','custom')
    assert r.returncode!=0
    p2=tmp_path/'with-roles'
    r=run(KIT/'scripts/install.py','--project-path',p2,'--preset','custom','--roles','coder','--shared-model','provider/shared')
    assert r.returncode==0, r.stderr
    state=json.loads((p2/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['profile']=='standard'
    assert state['advanced_roles']==['coder']

def test_model_discovery_cache_only_exposes_configured_provider(tmp_path, monkeypatch):
    home=tmp_path/'home'; cache=home/'.cache'; cache.mkdir(parents=True)
    project=tmp_path/'project'; project.mkdir()
    (project/'opencode.json').write_text(json.dumps({'provider': {'provider-a': {}}}))
    (cache/'opencode.json').write_text(json.dumps({
        'provider-a': {'id':'provider-a','models': {'model-x': {'name':'X'}}},
        'provider-b': {'id':'provider-b','models': {'model-y': {'name':'Y'}}}
    }))
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('USERPROFILE',str(home)); monkeypatch.setenv('PATH',''); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py','--project-path',project)
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['source']=='configured-fallback' and data['best_effort'] is True
    assert data['models']==['provider-a/model-x']
    assert 'provider-b/model-y' not in data['models']


def test_model_discovery_does_not_dump_unconfigured_cache_catalog(tmp_path, monkeypatch):
    home=tmp_path/'home'; cache=home/'.cache'; cache.mkdir(parents=True)
    project=tmp_path/'project'; project.mkdir()
    (cache/'opencode.json').write_text(json.dumps({'provider-a': {'id':'provider-a','models': {'x':{},'y':{}}}}))
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('USERPROFILE',str(home)); monkeypatch.setenv('PATH',''); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py','--project-path',project)
    data=json.loads(r.stdout)
    assert data['ok'] is False and data['models']==[]


def test_model_discovery_empty_does_not_fail_or_loop(tmp_path, monkeypatch):
    home=tmp_path/'home'; home.mkdir()
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('USERPROFILE',str(home)); monkeypatch.setenv('PATH',''); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py')
    assert r.returncode==0
    data=json.loads(r.stdout)
    assert data['ok'] is False and data['models']==[]


def test_adaptive_routing_skill_is_installed_and_lightweight(tmp_path):
    skill=(KIT/'skills/task-classification/SKILL.md').read_text(encoding='utf-8')
    assert 'Minimum routing' in skill
    assert 'Çalışma profili' in skill and 'ajan kadrosu değildir' in skill
    assert 'Kararı değiştirmeyecek bilinmeyeni araştırma' in skill
    assert 'Context taşıma; referans taşı' in skill
    assert len(skill.encode('utf-8')) < 7000
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','basic')
    assert r.returncode==0, r.stderr
    assert (p/'.opencode/skills/task-classification/SKILL.md').is_file()

def test_manager_uses_minimum_team_not_fixed_pipeline():
    for name in ('manager','working-manager'):
        text=(KIT/f'roles/{name}.md').read_text(encoding='utf-8')
        low=text.lower()
        assert 'minimum' in low
        assert 'ihtiyaç' in low and 'genişlet' in low
        assert 'task-classification' in text
        assert 'profil' in low
        assert ('kadro' in low or 'bütün uzmanları' in low or 'sabit pipeline' in low)

def test_small_tasks_do_not_force_specialists():
    text=(KIT/'skills/task-classification/SKILL.md').read_text(encoding='utf-8')
    assert 'typo' in text.lower() or 'deterministik küçük değişiklik' in text.lower()
    assert 'zorunlu değildir' in text
    manager=(KIT/'roles/working-manager.md').read_text(encoding='utf-8')
    assert 'Küçük, açık ve lokal işleri doğrudan uygula' in manager


def test_security_and_visual_triggers_are_conditional():
    sec=(KIT/'roles/security-reviewer.md').read_text(encoding='utf-8')
    vis=(KIT/'roles/visual-qa.md').read_text(encoding='utf-8')
    assert 'gerçekten etkileniyorsa' in sec
    assert 'güvenlik sınırı yoksa' in sec
    assert 'gerçekten değiştiyse' in vis
    assert 'Backend-only' in vis


def test_repository_handoff_is_reference_first():
    text=(KIT/'roles/repository-explorer.md').read_text(encoding='utf-8')
    assert 'dosya/sembol' in text
    assert 'Büyük kod blokları' in text
    assert 'tüm grep çıktısı' in text


def test_qa_starts_from_diff_and_does_not_repeat_repository_scan():
    text=(KIT/'roles/qa-reviewer.md').read_text(encoding='utf-8')
    assert 'Kabul kriteri, diff' in text
    assert 'sebepsiz sıfırdan tekrarlama' in text
    assert 'deterministik' in text.lower()


def test_loop_breaker_is_progress_based_and_native():
    skill=(KIT/'skills/task-classification/SKILL.md').read_text(encoding='utf-8')
    assert 'yeni bilgi veya gerçek ilerleme' in skill
    assert 'doom_loop' in skill
    assert 'maksimum 2 retry' not in skill.lower()
    # Eski özel task/workflow/loop runtime'ı geri gelmemeli.
    forbidden={'task-runtime.py','workflow.py','validate-evidence.py'}
    assert not any((KIT/'scripts'/name).exists() for name in forbidden)


def test_role_prompts_remain_model_independent_and_no_dynamic_task_metadata():
    for f in (KIT/'roles').glob('*.md'):
        text=f.read_text(encoding='utf-8')
        assert '\nmodel:' not in text
        low=text.lower()
        assert 'task id:' not in low and 'task_id:' not in low
        assert 'bugünün tarihi' not in low


def test_profiles_are_policy_only_and_share_capability_pool():
    names=('basic','standard','powerful')
    data=[json.loads((KIT/f'presets/{name}.json').read_text(encoding='utf-8')) for name in names]
    assert {p.stem for p in (KIT/'presets').glob('*.json')}==set(names)
    for d in data:
        assert 'task-classification' in d['skills']
        assert {'manager','architect','repository-explorer','coder','qa-reviewer','visual-qa','security-reviewer'} <= set(d['roles'])
        assert len(d['skills'])==13
        assert set(d['policy'])=={'specialist_threshold','parallelism','independent_review','priority'}
    assert data[0]['roles']==data[1]['roles']==data[2]['roles']
    assert data[0]['skills']==data[1]['skills']==data[2]['skills']

def test_legacy_solo_agent_is_not_shipped_and_team_mode_is_not_main_ux():
    assert not (KIT/'roles/solo-agent.md').exists()
    wizard=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    assert 'Tek Ana Ajan / Çoklu Ajan' in wizard
    assert 'normal kullanıcıya SORMA' in wizard
    assert 'legacy `--team-mode single`' in wizard or 'legacy `single|multi`' in wizard

def test_prompt_budget_does_not_explode():
    role_bytes=sum(f.stat().st_size for f in (KIT/'roles').glob('*.md'))
    skill_bytes=sum(f.stat().st_size for f in (KIT/'skills').glob('*/SKILL.md'))
    # Koruma eşiği yalnız dramatik şişmeyi yakalar; kalite için birkaç KB artışa izin verir.
    assert role_bytes < 30000
    assert skill_bytes < 25000


def _fake_opencode(bin_dir: Path, body: str):
    """Create a fake opencode executable. body is Python code (cross-platform).
    
    On Unix, writes a #!/usr/bin/env python3 script as 'opencode'.
    On Windows, writes a Python stub + 'opencode.cmd' launcher.
    The Python code receives sys.argv; it should print model lines to stdout.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        stub = bin_dir / '_opencode_stub.py'
        stub.write_text(body, encoding='utf-8')
        exe = bin_dir / 'opencode.cmd'
        exe.write_text(f'@"{sys.executable}" "%~dp0_opencode_stub.py" %*\r\n', encoding='utf-8')
    else:
        exe = bin_dir / 'opencode'
        exe.write_text(f'#!{sys.executable}\n' + body, encoding='utf-8')
        exe.chmod(0o755)
    return exe


def test_model_discovery_prefers_official_cli(tmp_path, monkeypatch):
    bindir=tmp_path/'bin'
    _fake_opencode(bindir, "print('provider-cli/model-a')\nprint('provider-cli/model-b')\n")
    home=tmp_path/'home'; cache=home/'.cache'; cache.mkdir(parents=True)
    (cache/'opencode.json').write_text(json.dumps({'id':'cache/model-c'}))
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('PATH',str(bindir)); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['source']=='opencode-cli'
    assert data['source_kind']=='official-cli' and data['documented'] is True and data['best_effort'] is False
    assert data['models']==['provider-cli/model-a','provider-cli/model-b']


def test_model_discovery_cache_is_marked_best_effort(tmp_path, monkeypatch):
    home=tmp_path/'home'; cache=home/'.cache'; cache.mkdir(parents=True)
    project=tmp_path/'project'; project.mkdir()
    (project/'opencode.json').write_text(json.dumps({'provider': {'provider-cache': {}}}))
    (cache/'opencode.json').write_text(json.dumps({'id':'provider-cache/model-x'}))
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('USERPROFILE',str(home)); monkeypatch.setenv('PATH',''); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py','--project-path',project)
    data=json.loads(r.stdout)
    assert data['source']=='configured-fallback'
    assert data['source_kind']=='best-effort-config-cache'
    assert data['documented'] is False and data['best_effort'] is True
    assert 'UNDOCUMENTED'.lower() in data['notice'].lower() or 'best-effort' in data['notice'].lower()


def test_model_discovery_refresh_is_explicit_only(tmp_path, monkeypatch):
    bindir=tmp_path/'bin'; log=tmp_path/'calls.log'
    _fake_opencode(bindir, f"import sys\nwith open({log.as_posix()!r},'a') as f:\n    f.write(' '.join(sys.argv[1:])+'\\n')\nprint('provider/model-x')\n")
    monkeypatch.setenv('PATH',str(bindir)); monkeypatch.setenv('HOME',str(tmp_path/'home')); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py'); assert r.returncode==0
    assert log.read_text(encoding='utf-8').strip()=='models'
    data=json.loads(r.stdout); assert data['refreshed'] is False
    r=run(KIT/'scripts/model_discovery.py','--refresh'); assert r.returncode==0
    assert log.read_text().splitlines()==['models','models --refresh']
    data=json.loads(r.stdout); assert data['refreshed'] is True and data['checked'][0]=='opencode models --refresh'


def test_existing_config_result_explicitly_reports_preservation(tmp_path):
    p=tmp_path/'app'; p.mkdir(); cfg=p/'opencode.jsonc'; cfg.write_text('{"model":"x/y"}')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert cfg.read_text(encoding='utf-8')=='{"model":"x/y"}'
    assert data['config']['action']=='preserved-existing-config'
    assert data['config']['existed_before'] is True
    assert 'değiştirmedi' in data['config']['notice']


def test_new_config_uses_native_minimum_without_reserved(tmp_path):
    p=tmp_path/'app'; r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    cfg=json.loads((p/'opencode.jsonc').read_text(encoding='utf-8'))
    assert cfg['subagent_depth']==1
    assert cfg['compaction']=={'auto':True,'prune':True}
    assert 'reserved' not in cfg['compaction'] and 'reserved' not in cfg
    data=json.loads(r.stdout)
    assert data['config']['action']=='created-hhc-config'


def test_manager_keeps_specialists_available_but_routes_conditionally():
    text=(KIT/'roles/manager.md').read_text(encoding='utf-8')
    assert 'çağrılabilir' in text
    assert 'Çalışma profilini sabit pipeline veya rol kadrosu olarak yorumlama' in text
    for role in ('architect','repository-explorer','coder','qa-reviewer','visual-qa','security-reviewer'):
        assert f'{role}: allow' in text

def test_lsp_is_native_deterministic_validation_not_new_framework():
    coder=(KIT/'roles/coder.md').read_text(encoding='utf-8')
    qa=(KIT/'roles/qa-reviewer.md').read_text(encoding='utf-8')
    cls=(KIT/'skills/task-classification/SKILL.md').read_text(encoding='utf-8')
    assert 'OpenCode LSP' in coder and 'OpenCode LSP' in qa
    assert 'LSP diagnostic' in cls
    forbidden=('lsp-wrapper.py','lsp-runtime.py','diagnostic-framework.py')
    assert not any((KIT/'scripts'/x).exists() for x in forbidden)


def test_global_wizard_documents_refresh_and_best_effort(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME',str(tmp_path/'config'))
    monkeypatch.setenv('XDG_DATA_HOME',str(tmp_path/'data'))
    r=run(KIT/'scripts/install_global.py','--install'); assert r.returncode==0, r.stderr
    text=(tmp_path/'config/opencode/commands/hhc-install.md').read_text(encoding='utf-8')
    assert 'UNDOCUMENTED / BEST-EFFORT' in text
    assert 'model_discovery.py' in text and '--refresh' in text
    assert 'otomatik çalıştırılmamalı' in text


def test_rc16_does_not_add_rejected_native_complexity(tmp_path):
    for f in (KIT/'roles').glob('*.md'):
        text=f.read_text(encoding='utf-8')
        assert '\nsteps:' not in text
        assert '\ndoom_loop:' not in text
    assert not (KIT/'plugins').exists()
    assert not (KIT/'mcp').exists()
    assert not (KIT/'tools').exists()


def test_profile_is_first_and_team_mode_is_smart_default():
    text=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    assert text.index('## 1. Çalışma profili') < text.index('## 2. Proje özelliklerini otomatik çıkar')
    assert 'Basic' in text and 'Standard' in text and 'Powerful' in text
    assert 'normal kullanıcıya SORMA' in text
    assert '--team-mode multi --manager-mode hands_on' in text
    assert 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in text

def test_user_visible_role_labels_are_turkish():
    text=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    for label in ('Çalışan Yönetici','Orkestratör','Mimar','Depo Gezgini','Kodlayıcı','Kalite İnceleyici','Görsel QA','Güvenlik İnceleyici'):
        assert label in text

def test_rc17_single_mode_keeps_task_capability():
    p=(KIT/'roles/working-manager.md').read_text(encoding='utf-8')
    assert 'architect: allow' in p and 'coder: allow' in p and 'qa-reviewer: allow' in p
    assert 'task: deny' not in p


def test_rc17_manager_capability_fallback_rule():
    for name in ('manager','working-manager'):
        text=(KIT/f'roles/{name}.md').read_text(encoding='utf-8')
        assert 'native araçları ve yetenekleriyle' in text
        assert 'güvenilir biçimde mevcut ekiple' in text
        assert '/hhc-reconfigure' in text


def test_reconfigure_uses_same_new_decision_tree():
    text=(KIT/'bootstrap/commands/hhc-reconfigure.md').read_text(encoding='utf-8')
    assert 'aynı karar ağacını' in text
    assert 'Basic / Standard / Powerful' in text
    assert 'Legacy profile' in text or 'Legacy' in text

def test_rc17_single_reconfigure_migrates_legacy_solo_owned_file(tmp_path):
    p=tmp_path/'app'
    # Eski rc.16 solo state/dosyasını minimal biçimde simüle et.
    agent=p/'.opencode/agents/solo-agent.md'; agent.parent.mkdir(parents=True)
    agent.write_text('legacy solo agent')
    state={'schema_version':1,'kit_version':'1.1.0-rc.16','team_mode':'single','preset':'minimal','manager_mode':None,
           'primary_agent':'solo-agent','roles':['solo-agent'],'skills':[],'commands':[],'model_policy':'shared',
           'shared_model':'provider/old','models':{'solo-agent':'provider/old'},'managed_files':['.opencode/agents/solo-agent.md'],
           'config_created_by_hhc':False,'config_sha256':None}
    (p/'.opencode/hhc-team.json').write_text(json.dumps(state))
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--team-mode','single','--preset','minimal','--shared-model','provider/new')
    assert r.returncode==0, r.stderr
    assert not agent.exists()
    assert (p/'.opencode/agents/working-manager.md').is_file() and (p/'.opencode/agents/coder.md').is_file()


def test_model_discovery_cache_can_use_authenticated_provider_without_reading_credentials(tmp_path, monkeypatch):
    bindir=tmp_path/'bin'
    _fake_opencode(bindir,
        "import sys\n"
        "if len(sys.argv)>1 and sys.argv[1]=='models':\n"
        "    sys.exit(1)\n"
        "if len(sys.argv)>2 and sys.argv[1]=='auth' and sys.argv[2]=='list':\n"
        "    print('provider-auth oauth')\n"
        "    sys.exit(0)\n"
        "sys.exit(1)\n"
    )
    home=tmp_path/'home'; cache=home/'.cache'; cache.mkdir(parents=True)
    project=tmp_path/'project'; project.mkdir()
    (cache/'opencode.json').write_text(json.dumps({
        'provider-auth': {'id':'provider-auth','models': {'model-a': {}}},
        'provider-unused': {'id':'provider-unused','models': {'model-b': {}}}
    }))
    monkeypatch.setenv('HOME',str(home)); monkeypatch.setenv('USERPROFILE',str(home)); monkeypatch.setenv('PATH',str(bindir)); monkeypatch.setenv('APPDATA','')
    r=run(KIT/'scripts/model_discovery.py','--project-path',project)
    data=json.loads(r.stdout)
    assert data['models']==['provider-auth/model-a']
    assert data['active_providers']==['provider-auth']


def test_reconfigure_multi_model_flow_is_role_complete():
    text=(KIT/'bootstrap/commands/hhc-reconfigure.md').read_text(encoding='utf-8')
    assert 'Kurulu ekipte N rol varsa N ayrı model kararı alınmalıdır.' in text
    assert 'bir rolün modelini diğerine sessizce kopyalama' in text

def test_rc18_source_and_dist_exclude_personal_opencode_files(tmp_path):
    out=tmp_path/'dist'; source=tmp_path/'source'
    r=run(KIT/'scripts/release-build.py','--out',out,'--source-out',source)
    assert r.returncode==0, r.stderr
    import zipfile
    for z in (out/f'HHC-AI-Team-Kit-{(KIT/"VERSION").read_text(encoding="utf-8").strip()}.zip', source/f'HHC-AI-Team-Kit-{(KIT/"VERSION").read_text(encoding="utf-8").strip()}-SOURCE.zip'):
        with zipfile.ZipFile(z) as f:
            names=set(f.namelist())
        assert 'AGENTS.md' not in names
        assert 'opencode.jsonc' not in names
        assert not any(n=='.opencode' or n.startswith('.opencode/') for n in names)



def test_rc19_model_discovery_prefers_desktop_visibility_show(tmp_path, monkeypatch):
    appdata=tmp_path/'AppData'/'Roaming'
    state_dir=appdata/'ai.opencode.desktop'; state_dir.mkdir(parents=True)
    model_state={
        'user':[
            {'providerID':'opencode','modelID':'mimo-v2.5-free','visibility':'hide'},
            {'providerID':'opencode','modelID':'mimo-v2.5-pro','visibility':'show'},
            {'providerID':'deepseek','modelID':'v4-pro','visibility':'show'},
            {'providerID':'deepseek','modelID':'v4-pro','visibility':'show'},
            {'providerID':'bad provider','modelID':'x','visibility':'show'},
        ]
    }
    (state_dir/'opencode.global.dat').write_text(json.dumps({'model':json.dumps(model_state)}),encoding='utf-8')
    bindir=tmp_path/'bin'; _fake_opencode(bindir,"print('cli/model-should-not-win')\n")
    monkeypatch.setenv('APPDATA',str(appdata)); monkeypatch.setenv('PATH',str(bindir)); monkeypatch.setenv('HOME',str(tmp_path/'home'))
    r=run(KIT/'scripts/model_discovery.py')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['source']=='opencode-desktop-state'
    assert data['source_kind']=='desktop-user-visibility-state'
    assert data['documented'] is False and data['best_effort'] is True
    assert data['models']==['deepseek/v4-pro','opencode/mimo-v2.5-pro']
    assert 'opencode/mimo-v2.5-free' not in data['models']
    assert data['count']==2


def test_rc19_desktop_empty_or_invalid_falls_back_to_cli(tmp_path, monkeypatch):
    appdata=tmp_path/'AppData'/'Roaming'
    state_dir=appdata/'ai.opencode.desktop'; state_dir.mkdir(parents=True)
    (state_dir/'opencode.global.dat').write_text(json.dumps({'model':json.dumps({'user':[{'providerID':'x','modelID':'hidden','visibility':'hide'}]})}),encoding='utf-8')
    bindir=tmp_path/'bin'; _fake_opencode(bindir,"print('provider-cli/model-a')\n")
    monkeypatch.setenv('APPDATA',str(appdata)); monkeypatch.setenv('PATH',str(bindir)); monkeypatch.setenv('HOME',str(tmp_path/'home'))
    r=run(KIT/'scripts/model_discovery.py')
    data=json.loads(r.stdout)
    assert data['source']=='opencode-cli'
    assert data['models']==['provider-cli/model-a']


def test_rc19_desktop_model_state_can_be_object_not_only_string(tmp_path, monkeypatch):
    appdata=tmp_path/'AppData'/'Roaming'
    state_dir=appdata/'ai.opencode.desktop'; state_dir.mkdir(parents=True)
    state={'model':{'user':[{'providerID':'p','modelID':'m','visibility':'show'}]}}
    (state_dir/'opencode.global.dat').write_text(json.dumps(state),encoding='utf-8')
    monkeypatch.setenv('APPDATA',str(appdata)); monkeypatch.setenv('PATH',''); monkeypatch.setenv('HOME',str(tmp_path/'home'))
    r=run(KIT/'scripts/model_discovery.py')
    data=json.loads(r.stdout)
    assert data['models']==['p/m']


def test_rc19_bootstrap_documents_desktop_show_source_and_keeps_role_complete_flow():
    for rel in ('bootstrap/commands/hhc-install.md','bootstrap/commands/hhc-reconfigure.md','bootstrap/skills/hhc-project-bootstrap/SKILL.md'):
        text=(KIT/rel).read_text(encoding='utf-8')
        assert 'opencode.global.dat' in text
        assert 'visibility' in text and 'show' in text
    install=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    assert 'her kurulu HHC rolü için ayrı model cevabı topla' in install
    assert 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in install


def test_symlink_project_root_rejected(tmp_path):
    real=tmp_path/'real'; real.mkdir()
    link=tmp_path/'link'
    try:
        os.symlink(real,link,target_is_directory=True)
    except (OSError,AttributeError):
        pytest.skip('symlink not available on this platform/permission')
    r=run(KIT/'scripts/install.py','--project-path',link,'--preset','minimal')
    assert r.returncode!=0, f'unexpected success; stderr={r.stderr}'


def test_python_version_check_rejects_below_minimum():
    import types
    scripts = str(KIT/'scripts')
    sys.path.insert(0, scripts)
    try:
        from install_global import check_python_version, MIN_PYTHON
        # Eski sürüm -> raise
        old = types.SimpleNamespace(major=3, minor=8)
        with pytest.raises(RuntimeError):
            check_python_version(old)
        # Tam minimum -> ok
        min_ok = types.SimpleNamespace(major=MIN_PYTHON[0], minor=MIN_PYTHON[1])
        check_python_version(min_ok)  # raise yok
        # Yeni sürüm -> ok
        new = types.SimpleNamespace(major=3, minor=12)
        check_python_version(new)
    finally:
        sys.path.remove(scripts)


def test_release_manifest_is_version_suffixed(tmp_path):
    out=tmp_path/'dist'
    r=run(KIT/'scripts/release-build.py','--out',out)
    assert r.returncode==0, r.stderr
    version=(KIT/'VERSION').read_text().strip()
    manifest=out/f'RELEASE-MANIFEST-{version}.json'
    assert manifest.is_file()
    m=json.loads(manifest.read_text(encoding='utf-8'))
    assert m['version']==version
    assert m['archive']==f'HHC-AI-Team-Kit-{version}.zip'
    assert not (out/'RELEASE-MANIFEST.json').is_file()


def test_hands_on_rejects_manager_role_model_after_rc16_compat_removal(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--team-mode','multi','--manager-mode','hands_on','--preset','minimal','--model','manager=provider/x')
    assert r.returncode!=0, r.stderr


def test_native_scout_routing_is_explicit_and_readonly_external_only(tmp_path):
    for role in ('manager','working-manager'):
        text=(KIT/f'roles/{role}.md').read_text(encoding='utf-8')
        assert 'scout: allow' in text
        assert 'Harici dokümantasyon' in text and 'upstream implementasyon' in text
        assert '`repository-explorer` alanında tut' in text
        assert 'bugünün verileriyle, gerçek ve güncel kaynaklara dayanarak' in text
        assert 'resmî/birincil kaynağı öncelemesini' in text
        assert 'doğrulanan gerçek + kaynak + sürüm/tarih + görev etkisi' in text
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    installed=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert 'scout: deny' in installed  # opt-in: varsayılan kapalı


def test_background_parallelism_is_stable_but_dependency_guarded():
    for role in ('manager','working-manager'):
        text=(KIT/f'roles/{role}.md').read_text(encoding='utf-8')
        assert 'Task `background` akışıyla' in text
        assert 'Background işi poll etme' in text
        assert 'Bağımlı işler' in text and 'sıralı kalır' in text
        assert 'seçeneğini gerçekten sunuyorsa' not in text

def test_command_context_isolation_is_only_on_heavy_review():
    review=(KIT/'commands/team-review.md').read_text(encoding='utf-8')
    status=(KIT/'commands/team-status.md').read_text(encoding='utf-8')
    assert 'agent: qa-reviewer' in review
    assert 'subtask: true' in review
    assert 'subtask: true' not in status


def test_scout_remains_native_but_has_opt_in_model_surface():
    assert not (KIT/'roles/scout.md').exists()
    assert not (KIT/'skills/scout').exists()
    install=(KIT/'scripts/install.py').read_text(encoding='utf-8')
    assert "PRIMARY_ROLES={'manager','working-manager','solo-agent'}" in install
    assert '--scout-model' in install and "choices=['enabled','disabled']" in install


def test_scout_disabled_by_default_has_no_override_and_denies_task(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    assert not (p/'.opencode/opencode.jsonc').exists()
    manager=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert 'scout: deny' in manager and 'scout: allow' not in manager
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['scout_enabled'] is False and state['scout_model'] is None


def test_scout_enabled_writes_independent_native_model_override(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal',
          '--model','working-manager=provider/expensive','--model','coder=provider/coder','--model','qa-reviewer=provider/qa',
          '--scout','enabled','--scout-model','provider/cheap-research')
    assert r.returncode==0, r.stderr
    cfg=json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))
    assert cfg['agent']['scout']['model']=='provider/cheap-research'
    assert cfg['agent']['scout']['model']!='provider/expensive'
    manager=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert 'model: provider/expensive' in manager and 'scout: allow' in manager
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['scout_enabled'] is True and state['scout_model']=='provider/cheap-research'


def test_scout_enabled_requires_explicit_model(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--scout','enabled')
    assert r.returncode!=0
    assert 'scout-model' in r.stderr.lower()


def test_scout_model_rejected_when_disabled(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--scout','disabled','--scout-model','provider/x')
    assert r.returncode!=0


def test_scout_reconfigure_enable_change_disable_preserves_other_models(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal',
          '--model','working-manager=provider/mgr','--model','coder=provider/coder','--model','qa-reviewer=provider/qa','--scout','disabled')
    assert r.returncode==0, r.stderr
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','minimal',
          '--model','working-manager=provider/mgr','--model','coder=provider/coder','--model','qa-reviewer=provider/qa',
          '--scout','enabled','--scout-model','provider/research-1')
    assert r.returncode==0, r.stderr
    assert json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))['agent']['scout']['model']=='provider/research-1'
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','minimal',
          '--model','working-manager=provider/mgr','--model','coder=provider/coder','--model','qa-reviewer=provider/qa',
          '--scout','enabled','--scout-model','provider/research-2')
    assert r.returncode==0, r.stderr
    assert json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))['agent']['scout']['model']=='provider/research-2'
    assert 'model: provider/coder' in (p/'.opencode/agents/coder.md').read_text(encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','minimal',
          '--model','working-manager=provider/mgr','--model','coder=provider/coder','--model','qa-reviewer=provider/qa','--scout','disabled')
    assert r.returncode==0, r.stderr
    assert not (p/'.opencode/opencode.jsonc').exists()
    assert 'scout: deny' in (p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')


def test_scout_layer_preserves_existing_root_config(tmp_path):
    p=tmp_path/'app'; p.mkdir()
    root=p/'opencode.jsonc'; root.write_text('{\n  // user config\n  "model": "provider/user",\n  "mcp": {"custom": {"enabled": false}}\n}\n',encoding='utf-8')
    before=root.read_text(encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--scout','enabled','--scout-model','provider/research')
    assert r.returncode==0, r.stderr
    assert root.read_text(encoding='utf-8')==before
    assert json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))['agent']['scout']['model']=='provider/research'


def test_scout_layer_refuses_to_overwrite_user_dot_opencode_config(tmp_path):
    p=tmp_path/'app'; target=p/'.opencode/opencode.jsonc'; target.parent.mkdir(parents=True)
    target.write_text('{"agent":{"other":{"model":"provider/user"}}}',encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--scout','enabled','--scout-model','provider/research')
    assert r.returncode!=0
    assert target.read_text(encoding='utf-8')=='{"agent":{"other":{"model":"provider/user"}}}'


def test_bootstrap_scout_opt_in_and_separate_model_documented():
    install=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    reconf=(KIT/'bootstrap/commands/hhc-reconfigure.md').read_text(encoding='utf-8')
    assert 'Scout — proje bazında opt-in' in install
    assert 'profile bağlı değildir' in install
    assert 'Scout modeli' in install and 'ayrıca' in install
    assert 'scout_enabled' in reconf and 'Scout / Dış Araştırma' in reconf

# rc.19 SMART model selection + opt-in Playwright MCP

def _models_dev_fixture(path: Path):
    data={
        'provider': {
            'models': {
                'good': {'tool_call':True,'reasoning':True,'attachment':True,'modalities':{'input':['text','image'],'output':['text']},'limit':{'context':256000,'output':32000},'cost':{'input':0.2,'output':0.8}},
                'text-only': {'tool_call':True,'reasoning':True,'attachment':False,'modalities':{'input':['text'],'output':['text']},'limit':{'context':128000,'output':16000},'cost':{'input':0.1,'output':0.3}},
                'no-tools': {'tool_call':False,'reasoning':True,'modalities':{'input':['text'],'output':['text']},'limit':{'context':128000,'output':16000}},
                'unknown': {'reasoning':True,'limit':{'context':128000,'output':16000}}
            }
        }
    }
    path.write_text(json.dumps(data),encoding='utf-8')
    return path


def test_model_advisor_classifies_capabilities_and_cost(tmp_path):
    meta=_models_dev_fixture(tmp_path/'models.json')
    r=run(KIT/'scripts/model_advisor.py','--metadata-file',meta,'--role','visual-qa','--model','provider/good','--model','provider/text-only')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout); rows={x['model']:x for x in data['roles']['visual-qa']}
    assert rows['provider/good']['classification'] in {'RECOMMENDED','COMPATIBLE'}
    assert rows['provider/good']['image_input'] is True and rows['provider/good']['cost_input']==0.2
    assert rows['provider/text-only']['classification']=='INCOMPATIBLE'
    assert 'image_input' in rows['provider/text-only']['missing_required']


def test_model_capability_validation_blocks_explicit_missing_tool_call(tmp_path):
    p=tmp_path/'app'; meta=_models_dev_fixture(tmp_path/'models.json')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--model','working-manager=provider/no-tools','--validate-model-capabilities','--model-metadata-file',meta)
    assert r.returncode!=0
    assert 'tool_call' in r.stderr


def test_model_capability_validation_unknown_warns_but_does_not_fail(tmp_path):
    p=tmp_path/'app'; meta=_models_dev_fixture(tmp_path/'models.json')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal','--model','working-manager=provider/unknown','--validate-model-capabilities','--model-metadata-file',meta)
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['model_warnings'] and data['model_warnings'][0]['type']=='unknown-capability'


def test_visual_qa_validation_blocks_text_only_model(tmp_path):
    p=tmp_path/'app'; meta=_models_dev_fixture(tmp_path/'models.json')
    args=[KIT/'scripts/install.py','--project-path',p,'--preset','web-development','--model','visual-qa=provider/text-only','--validate-model-capabilities','--model-metadata-file',meta]
    r=run(*args)
    assert r.returncode!=0 and 'image_input' in r.stderr


def test_web_playwright_opt_in_is_project_local_and_visual_qa_scoped(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','web-development','--playwright','enabled')
    assert r.returncode==0, r.stderr
    cfg=json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))
    assert cfg['mcp']['playwright']['type']=='local'
    assert cfg['mcp']['playwright']['command']==['npx','@playwright/mcp@0.0.78']
    assert cfg['permission']['playwright_*']=='deny'
    visual=(p/'.opencode/agents/visual-qa.md').read_text(encoding='utf-8')
    manager=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert '"playwright_*": allow' in visual
    assert '"playwright_*": allow' not in manager
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['playwright_enabled'] is True


def test_playwright_default_disabled_and_non_web_cannot_enable(tmp_path):
    p=tmp_path/'web'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','web-development').returncode==0
    assert not (p/'.opencode/opencode.jsonc').exists()
    p2=tmp_path/'desktop'
    r=run(KIT/'scripts/install.py','--project-path',p2,'--preset','desktop-development','--playwright','enabled')
    assert r.returncode!=0


def test_playwright_reconfigure_disable_preserves_root_user_mcp(tmp_path):
    p=tmp_path/'app'; p.mkdir()
    root_cfg=p/'opencode.jsonc'; root_cfg.write_text('{"mcp":{"user-tool":{"type":"remote","url":"https://example.invalid/mcp"}}}',encoding='utf-8')
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','web-development','--playwright','enabled').returncode==0
    assert (p/'.opencode/opencode.jsonc').exists()
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','web-development','--playwright','disabled')
    assert r.returncode==0, r.stderr
    assert not (p/'.opencode/opencode.jsonc').exists()
    assert 'user-tool' in root_cfg.read_text(encoding='utf-8')


def test_playwright_and_scout_share_minimal_hhc_owned_aux_config(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','web-development','--scout','enabled','--scout-model','provider/research','--playwright','enabled')
    assert r.returncode==0, r.stderr
    cfg=json.loads((p/'.opencode/opencode.jsonc').read_text(encoding='utf-8'))
    assert cfg['agent']['scout']['model']=='provider/research'
    assert 'playwright' in cfg['mcp']
    assert not (KIT/'roles/scout.md').exists()


def test_model_advisor_metadata_unavailable_is_nonfatal(tmp_path):
    missing=tmp_path/'missing.json'
    r=run(KIT/'scripts/model_advisor.py','--metadata-file',missing,'--role','manager','--model','provider/x')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['metadata_available'] is False
    row=data['roles']['manager'][0]
    assert row['classification']=='WARNING' and row['tool_call'] is None


def test_model_advisor_never_invents_missing_cost(tmp_path):
    meta=tmp_path/'models.json'
    meta.write_text(json.dumps({'provider':{'models':{'x':{'tool_call':True,'reasoning':True,'modalities':{'input':['text'],'output':['text']},'limit':{'context':128000,'output':16000}}}}}),encoding='utf-8')
    r=run(KIT/'scripts/model_advisor.py','--metadata-file',meta,'--role','manager','--model','provider/x')
    assert r.returncode==0
    row=json.loads(r.stdout)['roles']['manager'][0]
    assert row['cost_input'] is None and row['cost_output'] is None


# ── /hhc-update tests ──

def test_update_bumps_kit_version_and_preserves_config(tmp_path):
    p=tmp_path/'app'
    # Önce standard kurulum yap
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    # State'teki kit_version'ı eski yap
    state_path=p/'.opencode/hhc-team.json'
    state=json.loads(state_path.read_text(encoding='utf-8'))
    original_config_action=json.loads(r.stdout)['config']['action']
    state['kit_version']='1.0.0'
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # --update çalıştır
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['status']=='UPDATED'
    new_state=json.loads(state_path.read_text(encoding='utf-8'))
    assert new_state['kit_version']==(KIT/'VERSION').read_text().strip()
    assert new_state['preset']=='standard'
    assert set(new_state['roles'])==set(state['roles'])


def test_update_up_to_date_short_circuits(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    # Aynı sürümle --update → UP_TO_DATE
    before_state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    before_files={x.relative_to(p):x.read_bytes() for x in p.rglob('*') if x.is_file()}
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, r.stderr
    data=json.loads(r.stdout)
    assert data['status']=='UP_TO_DATE'
    after_state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert after_state==before_state
    after_files={x.relative_to(p):x.read_bytes() for x in p.rglob('*') if x.is_file()}
    assert after_files==before_files


def test_update_requires_state(tmp_path):
    p=tmp_path/'app'
    p.mkdir()
    # State yok → hata
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode!=0


def test_update_rejects_with_reconfigure(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    r=run(KIT/'scripts/install.py','--project-path',p,'--update','--reconfigure')
    assert r.returncode!=0


def test_update_legacy_custom_migrates_to_advanced_and_preserves_specialists(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','custom','--roles','coder,qa-reviewer')
    assert r.returncode==0, r.stderr
    state_path=p/'.opencode/hhc-team.json'; state=json.loads(state_path.read_text(encoding='utf-8'))
    # Simulate a legacy custom state from the previous kit.
    state['kit_version']='1.1.1'; state['preset']='custom'; state.pop('profile',None); state.pop('advanced_roles',None)
    state_path.write_text(json.dumps(state),encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, r.stderr
    new_state=json.loads(state_path.read_text(encoding='utf-8'))
    assert new_state['profile']=='standard' and new_state['preset']=='standard'
    assert new_state['advanced_roles']==['coder','qa-reviewer']
    assert set(new_state['roles'])=={'working-manager','coder','qa-reviewer'}

def test_update_legacy_minimal_migrates_to_basic_and_expands_capability_pool(tmp_path):
    p=tmp_path/'app'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0
    user=p/'.opencode/agents/user.md'; user.write_text('keep',encoding='utf-8')
    state_path=p/'.opencode/hhc-team.json'; state=json.loads(state_path.read_text(encoding='utf-8'))
    state['kit_version']='1.1.1'; state['preset']='minimal'; state.pop('profile',None); state['roles']=['working-manager','coder','qa-reviewer']
    state_path.write_text(json.dumps(state),encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, r.stderr
    new=json.loads(state_path.read_text(encoding='utf-8'))
    assert new['profile']=='basic'
    assert (p/'.opencode/agents/architect.md').exists()
    assert (p/'.opencode/agents/security-reviewer.md').exists()
    assert user.read_text(encoding='utf-8')=='keep'

def test_update_scout_playwright_state_preserved(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','web-development',
          '--scout','enabled','--scout-model','provider/research',
          '--playwright','enabled')
    assert r.returncode==0, r.stderr
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['scout_enabled'] is True and state['scout_model']=='provider/research'
    assert state['playwright_enabled'] is True
    state['kit_version']='1.0.0'
    (p/'.opencode/hhc-team.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, r.stderr
    new_state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert new_state['scout_enabled'] is True
    assert new_state['scout_model']=='provider/research'
    assert new_state['playwright_enabled'] is True
    # .opencode/opencode.jsonc hala mevcut
    assert (p/'.opencode/opencode.jsonc').exists()


def test_global_bootstrap_contains_update(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME',str(tmp_path/'config'))
    monkeypatch.setenv('XDG_DATA_HOME',str(tmp_path/'data'))
    r=run(KIT/'scripts/install_global.py','--install')
    assert r.returncode==0, r.stderr
    root=tmp_path/'config/opencode/commands'
    assert (root/'hhc-update.md').is_file()
    text=(root/'hhc-update.md').read_text(encoding='utf-8')
    assert '--update' in text
    assert 'UP_TO_DATE' in text
    assert 'UPDATED' in text
    assert 'sessiz' in text
    assert 'update_global.py' in text
    assert 'OFFLINE' in text
    assert 'RATE_LIMITED' in text
    assert '--no-remote' in text
    # Placeholder replace doğrulaması
    assert '{{KIT_ROOT}}' not in text
    assert '{{PYTHON}}' not in text


# ── update_global tests ──

import hashlib, shutil, zipfile
from pathlib import Path

def _import_update_global():
    scripts = str(KIT / 'scripts')
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import update_global
    return update_global

def _ug_setup(monkeypatch, tmp_path, version='1.1.1'):
    """Common setup for update_global tests: imports module, creates current/ with VERSION."""
    ug = _import_update_global()
    current = tmp_path / 'current'
    current.mkdir(parents=True, exist_ok=True)
    (current / 'VERSION').write_text(version, encoding='utf-8')
    monkeypatch.setattr(ug, 'runtime_root', lambda: current)
    monkeypatch.setattr(ug, 'install_bootstrap', lambda dst: None)
    return ug, current

def _make_fake_release(tmp_path, version, extra_files=None):
    """Create minimal kit zip+manifest at tmp_path. Returns (manifest_dict, zip_path)."""
    files = {
        'VERSION': version,
        'README.md': f'# HHC Kit v{version}\n',
        'roles/manager.md': f'# Manager v{version}\n',
    }
    if extra_files:
        files.update(extra_files)

    staging = tmp_path / 'staging'
    for rel, text in files.items():
        p = staging / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    manifest_files = {}
    for rel in sorted(files):
        p = staging / rel
        manifest_files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    zip_path = tmp_path / f'HHC-AI-Team-Kit-{version}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(files):
            zf.write(staging / rel, rel)

    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()

    manifest = {
        'kit_name': 'HHC AI Team Kit',
        'version': version,
        'archive': f'HHC-AI-Team-Kit-{version}.zip',
        'archive_sha256': zip_sha,
        'file_count': len(files),
        'files': manifest_files,
    }
    (tmp_path / f'RELEASE-MANIFEST-{version}.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest, zip_path

def _fake_release_api(tag_name):
    """Return a fake GitHub releases/latest API response."""
    return {
        'tag_name': tag_name,
        'assets': [
            {'name': f'RELEASE-MANIFEST-{tag_name}.json',
             'browser_download_url': f'https://example.com/releases/{tag_name}/manifest.json'},
            {'name': f'HHC-AI-Team-Kit-{tag_name}.zip',
             'browser_download_url': f'https://example.com/releases/{tag_name}/update.zip'},
        ],
    }

def _patch_network_full_flow(monkeypatch, ug, release_api, manifest, zip_path, zip_sha):
    """Monkeypatch _fetch_json and _download for a full update flow."""
    def fake_fetch(url, token=None, timeout=30):
        if 'releases/latest' in (url or ''):
            return release_api, None
        else:
            return manifest, None

    def fake_download(url, dest, timeout=30):
        shutil.copy2(zip_path, dest)
        return zip_sha, None

    monkeypatch.setattr(ug, '_fetch_json', fake_fetch)
    monkeypatch.setattr(ug, '_download', fake_download)


def test_update_global_newer_release_updates_current(tmp_path, monkeypatch, capsys):
    """Newer remote (1.1.2) → UPDATED, current/VERSION==1.1.2, bootstrap refreshed."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    release_dir = tmp_path / 'release'
    release_dir.mkdir()
    manifest, zip_path = _make_fake_release(release_dir, '1.1.2')

    _patch_network_full_flow(monkeypatch, ug,
                             _fake_release_api('v1.1.2'),
                             manifest, zip_path, manifest['archive_sha256'])
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'UPDATED'
    assert result['current_version'] == '1.1.2'
    assert result['swapped_files'] >= 2  # VERSION + README + roles/manager
    assert (current / 'VERSION').read_text(encoding='utf-8').strip() == '1.1.2'
    # Verify content actually changed
    for rel in manifest['files']:
        if rel == 'VERSION':
            continue
        p = current / rel
        assert p.is_file(), f'Missing: {rel}'
        content = p.read_text(encoding='utf-8')
        assert '1.1.2' in content, f'{rel} not updated'


def test_update_global_equal_release_no_op(tmp_path, monkeypatch, capsys):
    """Equal version → UP_TO_DATE, current/ unchanged, idempotent on 2nd run."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    before_files = {}
    for p in current.rglob('*'):
        if p.is_file():
            before_files[str(p.relative_to(current))] = p.read_bytes()

    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (_fake_release_api('v1.1.1'), None))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'UP_TO_DATE'
    assert result['current_version'] == '1.1.1'

    # Idempotent: no files changed
    after_files = {}
    for p in current.rglob('*'):
        if p.is_file():
            after_files[str(p.relative_to(current))] = p.read_bytes()
    assert before_files == after_files

    # Second run → same result
    exit_code2 = ug.main()
    out2, _ = capsys.readouterr()
    assert exit_code2 == 0
    assert json.loads(out2)['status'] == 'UP_TO_DATE'


def test_update_global_older_release_no_downgrade(tmp_path, monkeypatch, capsys):
    """Older remote → UP_TO_DATE, current/ unchanged (no downgrade)."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.2')

    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (_fake_release_api('v1.1.0'), None))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'UP_TO_DATE'
    assert result['current_version'] == '1.1.2'
    assert (current / 'VERSION').read_text(encoding='utf-8').strip() == '1.1.2'


def test_update_global_offline_falls_back_local(tmp_path, monkeypatch, capsys):
    """Network unavailable → OFFLINE, exit 0, current/ untouched."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'URLError: connection refused'))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'OFFLINE'
    assert result['current_version'] == '1.1.1'
    assert (current / 'VERSION').read_text(encoding='utf-8').strip() == '1.1.1'


def test_update_global_no_releases_falls_back_local(tmp_path, monkeypatch, capsys):
    """404 from API → NO_RELEASES, exit 0."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'HTTP 404: Not Found'))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'NO_RELEASES'
    assert result['current_version'] == '1.1.1'


def test_update_global_checksum_mismatch_refuses_install(tmp_path, monkeypatch, capsys):
    """Zip sha256 mismatch → ERROR, current/ untouched, exit 0."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    release_dir = tmp_path / 'release'
    release_dir.mkdir()
    manifest, zip_path = _make_fake_release(release_dir, '1.1.2')

    # API/network OK but _download returns WRONG sha
    def fake_fetch(url, token=None, timeout=30):
        if 'releases/latest' in (url or ''):
            return _fake_release_api('v1.1.2'), None
        else:
            return manifest, None

    def fake_download(url, dest, timeout=30):
        shutil.copy2(zip_path, dest)
        return 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', None

    monkeypatch.setattr(ug, '_fetch_json', fake_fetch)
    monkeypatch.setattr(ug, '_download', fake_download)
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'ERROR'
    assert 'Bütünlük' in result.get('error', '')
    assert (current / 'VERSION').read_text(encoding='utf-8').strip() == '1.1.1'  # untouched


def test_update_global_rate_limited_falls_back_local(tmp_path, monkeypatch, capsys):
    """403 + rate limit → RATE_LIMITED, exit 0."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'HTTP 403: Forbidden (rate limited)'))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'RATE_LIMITED'
    assert result['current_version'] == '1.1.1'


def test_update_global_no_remote_skips_network(tmp_path, monkeypatch, capsys):
    """--no-remote → LOCAL_ONLY, no network call."""
    ug, current = _ug_setup(monkeypatch, tmp_path, '1.1.1')

    network_called = []
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: network_called.append(1) or (None, None))
    monkeypatch.setattr(sys, 'argv', ['update_global.py', '--no-remote'])

    exit_code = ug.main()
    out, err = capsys.readouterr()

    assert exit_code == 0
    result = json.loads(out)
    assert result['status'] == 'LOCAL_ONLY'
    assert result['current_version'] == '1.1.1'
    assert len(network_called) == 0  # network never called


def test_normalize_version_handles_v_prefix_and_comparison():
    """Unit test for _normalize_version and _compare."""
    ug = _import_update_global()

    # _normalize_version
    assert ug._normalize_version('v1.1.1') == (1, 1, 1)
    assert ug._normalize_version('V1.1.1') == (1, 1, 1)
    assert ug._normalize_version('1.1.1') == (1, 1, 1)
    assert ug._normalize_version('1.2.0') == (1, 2, 0)
    assert ug._normalize_version('1.10.3') == (1, 10, 3)
    assert ug._normalize_version('2.0') == (2, 0)
    assert ug._normalize_version('') is None
    assert ug._normalize_version('abc') is None
    assert ug._normalize_version('v1.alpha') is None

    # _compare
    assert ug._compare((1, 2, 0), (1, 1, 9)) == '>'
    assert ug._compare((1, 1, 1), (1, 1, 1)) == '=='
    assert ug._compare((1, 0, 0), (2, 0, 0)) == '<'
    assert ug._compare((1, 10, 0), (1, 9, 9)) == '>'
    assert ug._compare((2,), (1, 9, 9)) == '>'
    # Shorter tuple equals prefix of longer in Python tuple ordering
    assert ug._compare((1,), (1, 0, 0)) == '<'


def _ug_setup_tracking(monkeypatch, tmp_path, version='1.1.1'):
    """Like _ug_setup but returns bootstrap_calls list for call tracking."""
    ug = _import_update_global()
    current = tmp_path / 'current'
    current.mkdir(parents=True, exist_ok=True)
    (current / 'VERSION').write_text(version, encoding='utf-8')
    monkeypatch.setattr(ug, 'runtime_root', lambda: current)
    bootstrap_calls = []
    monkeypatch.setattr(ug, 'install_bootstrap', lambda dst: bootstrap_calls.append(dst))
    return ug, current, bootstrap_calls


def test_update_global_always_calls_install_bootstrap_on_non_fatal(tmp_path, monkeypatch, capsys):
    """install_bootstrap called on UP_TO_DATE, OFFLINE, NO_RELEASES, RATE_LIMITED, LOCAL_ONLY."""
    ug, current, calls = _ug_setup_tracking(monkeypatch, tmp_path, '1.1.1')

    # UP_TO_DATE (==)
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (_fake_release_api('v1.1.1'), None))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])
    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'UP_TO_DATE'
    assert len(calls) == 1 and calls[0] == current, 'install_bootstrap not called on UP_TO_DATE'

    # OFFLINE
    calls.clear()
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'URLError: connection refused'))
    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'OFFLINE'
    assert len(calls) == 1, 'install_bootstrap not called on OFFLINE'

    # RATE_LIMITED
    calls.clear()
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'HTTP 403: Forbidden (rate limited)'))
    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'RATE_LIMITED'
    assert len(calls) == 1, 'install_bootstrap not called on RATE_LIMITED'

    # NO_RELEASES (404)
    calls.clear()
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (None, 'HTTP 404: Not Found'))
    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'NO_RELEASES'
    assert len(calls) == 1, 'install_bootstrap not called on NO_RELEASES'

    # LOCAL_ONLY (--no-remote)
    calls.clear()
    monkeypatch.setattr(sys, 'argv', ['update_global.py', '--no-remote'])
    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'LOCAL_ONLY'
    assert len(calls) == 1, 'install_bootstrap not called on LOCAL_ONLY'


def test_update_global_install_bootstrap_not_called_on_error(tmp_path, monkeypatch, capsys):
    """install_bootstrap NOT called on genuine ERROR (checksum mismatch)."""
    ug, current, calls = _ug_setup_tracking(monkeypatch, tmp_path, '1.1.1')

    release_dir = tmp_path / 'release'
    release_dir.mkdir()
    manifest, zip_path = _make_fake_release(release_dir, '1.1.2')

    def fake_fetch(url, token=None, timeout=30):
        if 'releases/latest' in (url or ''):
            return _fake_release_api('v1.1.2'), None
        else:
            return manifest, None

    def fake_download(url, dest, timeout=30):
        shutil.copy2(zip_path, dest)
        return 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', None

    monkeypatch.setattr(ug, '_fetch_json', fake_fetch)
    monkeypatch.setattr(ug, '_download', fake_download)
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'ERROR'
    assert len(calls) == 0, 'install_bootstrap should NOT be called on checksum ERROR'


def test_update_global_up_to_date_syncs_bootstrap_to_global_config(tmp_path, monkeypatch, capsys):
    """UP_TO_DATE → install_bootstrap actually writes bootstrap files to opencode_root."""
    ug = _import_update_global()
    current = tmp_path / 'current'
    current.mkdir(parents=True, exist_ok=True)
    (current / 'VERSION').write_text('1.1.1', encoding='utf-8')

    # Create bootstrap files under current (simulating install_global.py --install)
    bootstrap_commands = current / 'bootstrap' / 'commands'
    bootstrap_skill = current / 'bootstrap' / 'skills' / 'hhc-project-bootstrap'
    bootstrap_commands.mkdir(parents=True)
    bootstrap_skill.mkdir(parents=True)

    cmd_files = ['hhc-install.md', 'hhc-reconfigure.md', 'hhc-update.md', 'hhc-status.md']
    for cmd in cmd_files:
        (bootstrap_commands / cmd).write_text(
            f'# {cmd}\n\nTest content with {{{{KIT_ROOT}}}} and {{{{PYTHON}}}} placeholders.\n',
            encoding='utf-8')
    (bootstrap_skill / 'SKILL.md').write_text(
        '# HHC Project Bootstrap\n\nSkill test {{{{KIT_ROOT}}}}.\n',
        encoding='utf-8')

    # Setup: mock runtime_root and opencode_root
    monkeypatch.setattr(ug, 'runtime_root', lambda: current)

    # Mock opencode_root to a temp directory so real install_bootstrap writes there
    oc_root = tmp_path / 'opencode_config'
    import install_global as ig_mod
    monkeypatch.setattr(ig_mod, 'opencode_root', lambda: oc_root)

    # NOTE: install_bootstrap is NOT mocked here (unlike _ug_setup).
    # The real function will run and write bootstrap files to oc_root.

    # UP_TO_DATE simulation
    monkeypatch.setattr(ug, '_fetch_json',
                        lambda url, token=None, timeout=30: (_fake_release_api('v1.1.1'), None))
    monkeypatch.setattr(sys, 'argv', ['update_global.py'])

    exit_code = ug.main()
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(out)['status'] == 'UP_TO_DATE'

    # Verify bootstrap files were written to opencode_root with placeholders replaced
    for cmd in cmd_files:
        target = oc_root / 'commands' / cmd
        assert target.is_file(), f'{cmd} not found in opencode_root'
        content = target.read_text(encoding='utf-8')
        assert 'Test content with' in content
        assert '{{KIT_ROOT}}' not in content, f'Placeholder KIT_ROOT not replaced in {cmd}'
        assert '{{PYTHON}}' not in content, f'Placeholder PYTHON not replaced in {cmd}'
        assert str(current) in content, f'KIT_ROOT path not substituted in {cmd}'

    # Verify skill directory
    skill_target = oc_root / 'skills' / 'hhc-project-bootstrap' / 'SKILL.md'
    assert skill_target.is_file(), 'hhc-project-bootstrap SKILL.md not found'
    skill_content = skill_target.read_text(encoding='utf-8')
    assert 'Skill test' in skill_content
    assert '{{KIT_ROOT}}' not in skill_content, 'Placeholder not replaced in skill'


# 1.2.0 SMART profile-policy architecture

def _state(project: Path):
    return json.loads((project/'.opencode/hhc-team.json').read_text(encoding='utf-8'))


def test_profile_default_is_standard_and_normal_primary_is_working_manager(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p)
    assert r.returncode==0, r.stderr
    s=_state(p)
    assert s['profile']=='standard' and s['preset']=='standard'
    assert s['team_mode']=='multi' and s['manager_mode']=='hands_on'
    assert s['primary_agent']=='working-manager'


def test_basic_keeps_security_and_all_specialists_available(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','basic')
    assert r.returncode==0, r.stderr
    s=_state(p)
    expected={'architect','repository-explorer','coder','qa-reviewer','visual-qa','security-reviewer'}
    assert expected <= set(s['roles'])
    manager=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert 'security-reviewer: allow' in manager
    assert 'Çalışma Profili: Basic' in manager
    assert 'gerekli uzmanı sırf profil nedeniyle kapatma' in manager


def test_profile_policy_overlay_is_small_and_roster_stable(tmp_path):
    role_sets=[]; skill_sets=[]; sizes=[]
    for profile in ('basic','standard','powerful'):
        p=tmp_path/profile
        assert run(KIT/'scripts/install.py','--project-path',p,'--preset',profile).returncode==0
        s=_state(p); role_sets.append(s['roles']); skill_sets.append(s['skills'])
        text=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
        sizes.append(len(text.encode('utf-8')))
        assert f'Çalışma Profili: {profile.title()}' in text
    assert role_sets[0]==role_sets[1]==role_sets[2]
    assert skill_sets[0]==skill_sets[1]==skill_sets[2]
    assert max(sizes)-min(sizes) < 800
    assert not any((KIT/'roles').glob('manager-basic.md'))


def test_powerful_policy_has_controlled_parallelism_and_no_default_duplicate(tmp_path):
    p=tmp_path/'app'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','powerful').returncode==0
    text=(p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')
    assert 'Çalışma Profili: Powerful' in text
    assert 'Bağımsız ve yüksek değerli işleri daha istekli paralelleştir' in text
    assert 'Aynı rolü varsayılan olarak çoğaltma' in text
    assert 'gerekli kalite kapıları geçtiğinde dur' in text
    assert 'Bağımlı işler' in text and 'sıralı kalır' in text


def test_project_characteristics_multilabel_react_dotnet_docker(tmp_path):
    p=tmp_path/'app'; p.mkdir()
    (p/'package.json').write_text(json.dumps({'dependencies':{'react':'1','vite':'1'}}),encoding='utf-8')
    (p/'app.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk.Web"></Project>',encoding='utf-8')
    (p/'Dockerfile').write_text('FROM scratch',encoding='utf-8')
    r=run(KIT/'scripts/project_characteristics.py','--project-path',p)
    assert r.returncode==0, r.stderr
    d=json.loads(r.stdout)
    assert d['browser_ui']['detected'] is True
    assert d['backend']['detected'] is True
    assert d['containerized']['detected'] is True


def test_project_characteristics_weak_package_json_does_not_force_browser_ui(tmp_path):
    p=tmp_path/'app'; p.mkdir()
    (p/'package.json').write_text(json.dumps({'dependencies':{'lodash':'1'}}),encoding='utf-8')
    d=json.loads(run(KIT/'scripts/project_characteristics.py','--project-path',p).stdout)
    assert d['browser_ui']['detected'] is False


def test_project_characteristics_detects_wordpress_as_multilabel(tmp_path):
    p=tmp_path/'site'; (p/'wp-content').mkdir(parents=True)
    d=json.loads(run(KIT/'scripts/project_characteristics.py','--project-path',p).stdout)
    assert d['wordpress']['detected'] is True
    assert d['browser_ui']['detected'] is True


def test_project_characteristics_detects_wpf_desktop(tmp_path):
    p=tmp_path/'desktop'; p.mkdir()
    (p/'app.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><UseWPF>true</UseWPF></PropertyGroup></Project>',encoding='utf-8')
    d=json.loads(run(KIT/'scripts/project_characteristics.py','--project-path',p).stdout)
    assert d['desktop_ui']['detected'] is True
    assert d['browser_ui']['detected'] is False


def test_playwright_is_characteristic_gated_not_profile_gated(tmp_path):
    p=tmp_path/'web'; p.mkdir()
    (p/'package.json').write_text(json.dumps({'dependencies':{'react':'1'}}),encoding='utf-8')
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','basic','--playwright','enabled')
    assert r.returncode==0, r.stderr
    assert _state(p)['playwright_enabled'] is True
    p2=tmp_path/'plain'
    r=run(KIT/'scripts/install.py','--project-path',p2,'--preset','powerful','--playwright','enabled')
    assert r.returncode!=0
    assert 'browser_ui' in r.stderr


def test_scout_is_profile_independent(tmp_path):
    for profile in ('basic','powerful'):
        p=tmp_path/profile
        r=run(KIT/'scripts/install.py','--project-path',p,'--preset',profile,'--scout','enabled','--scout-model','provider/research')
        assert r.returncode==0, r.stderr
        s=_state(p)
        assert s['scout_enabled'] is True and s['scout_model']=='provider/research'
        assert 'scout: allow' in (p/'.opencode/agents/working-manager.md').read_text(encoding='utf-8')


def test_legacy_profile_mappings_and_characteristic_hints(tmp_path):
    cases=[('minimal','basic',None),('standard','standard',None),('high-assurance','powerful',None),('web-development','standard','browser_ui'),('desktop-development','standard','desktop_ui')]
    for old,new,char in cases:
        p=tmp_path/old
        r=run(KIT/'scripts/install.py','--project-path',p,'--preset',old)
        assert r.returncode==0, (old,r.stderr)
        s=_state(p)
        assert s['profile']==new
        if char: assert s['project_characteristics'][char]['detected'] is True


def test_profile_reconfigure_preserves_explicit_model_assignments_when_resupplied(tmp_path):
    p=tmp_path/'app'
    models=['working-manager=provider/mgr','architect=provider/a','repository-explorer=provider/r','coder=provider/c','qa-reviewer=provider/q','visual-qa=provider/v','security-reviewer=provider/s']
    cmd=[KIT/'scripts/install.py','--project-path',p,'--preset','standard']
    for m in models: cmd += ['--model',m]
    assert run(*cmd).returncode==0
    cmd=[KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','powerful']
    for m in models: cmd += ['--model',m]
    r=run(*cmd); assert r.returncode==0, r.stderr
    s=_state(p)
    assert s['profile']=='powerful'
    assert s['models']['working-manager']=='provider/mgr'
    assert s['models']['security-reviewer']=='provider/s'


def test_no_silent_premium_fallback_or_profile_model_override():
    install=(KIT/'scripts/install.py').read_text(encoding='utf-8').lower()
    readme=(KIT/'README.md').read_text(encoding='utf-8').lower()
    assert 'premium' not in install or 'fallback' not in install
    assert 'sessiz premium fallback' in readme or 'sessizce daha pahalı' in readme
    for name in ('basic','standard','powerful'):
        data=json.loads((KIT/f'presets/{name}.json').read_text(encoding='utf-8'))
        assert 'model' not in data and 'models' not in data


def test_profile_names_and_semantics_have_tr_en_documentation_parity():
    tr=(KIT/'README.md').read_text(encoding='utf-8')
    en=(KIT/'README.en.md').read_text(encoding='utf-8')
    for name in ('Basic','Standard','Powerful'):
        assert name in tr and name in en
    for technical in ('browser_ui','desktop_ui','security-reviewer','visual-qa'):
        assert technical in tr and technical in en
    assert 'varsayılan ve önerilen' in tr.lower()
    assert 'default and recommended' in en.lower()


def test_main_profile_surface_exposes_only_three_and_custom_is_advanced():
    wizard=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    preset_files={p.stem for p in (KIT/'presets').glob('*.json')}
    assert preset_files=={'basic','standard','powerful'}
    assert 'Yalnız üç seçenek sun' in wizard
    assert 'Eski `custom` profilin görevi artık buradadır.' in wizard
    profile_section=wizard.split('## 2.',1)[0]
    assert '- **Web Development**' not in profile_section and '- **Desktop Development**' not in profile_section and '- **High Assurance**' not in profile_section


def test_background_is_treated_as_stable_without_experimental_user_warning():
    manager=(KIT/'roles/manager.md').read_text(encoding='utf-8').lower()
    bootstrap=(KIT/'bootstrap/skills/hhc-project-bootstrap/SKILL.md').read_text(encoding='utf-8').lower()
    assert 'background' in manager and 'background' in bootstrap
    assert 'experimental' not in manager and 'deneysel' not in manager
    assert 'dependency-independent' in bootstrap


# ── 1.2.0 audit fixes regression tests ──

def test_update_legacy_solo_agent_state_normalizes_to_working_manager(tmp_path):
    """Issue #1: rc.16 solo-agent state ile --update crash yapmamalı; working-manager'a normalize edilmeli."""
    p=tmp_path/'app'
    state_path=p/'.opencode/hhc-team.json'; state_path.parent.mkdir(parents=True)
    state={'schema_version':1,'kit_version':'1.1.0-rc.16','team_mode':'single','preset':'minimal',
           'primary_agent':'solo-agent','roles':['solo-agent'],'skills':[],'commands':[],'model_policy':'shared',
           'shared_model':'provider/old','models':{'solo-agent':'provider/old'},
           'managed_files':['.opencode/agents/solo-agent.md'],
           'config_created_by_hhc':False,'config_sha256':None,'manager_mode':None}
    state_path.write_text(json.dumps(state))
    # Simulate previous install artifact
    solo=p/'.opencode/agents/solo-agent.md'; solo.parent.mkdir(parents=True)
    solo.write_text('legacy solo agent')
    # --update should NOT crash (HHC-INSTALL-001)
    r=run(KIT/'scripts/install.py','--project-path',p,'--update')
    assert r.returncode==0, f'unexpected crash; stderr={r.stderr}'
    new_state=json.loads(state_path.read_text(encoding='utf-8'))
    assert new_state['primary_agent']=='working-manager'
    assert new_state['manager_mode']=='hands_on'
    assert 'solo-agent' not in new_state['roles']
    assert 'working-manager' in new_state['roles']
    # solo-agent.md artık mevcut değil
    assert not solo.exists()
    # working-manager.md kurulmuş olmalı
    assert (p/'.opencode/agents/working-manager.md').is_file()


def test_project_characteristics_detects_ios_mobile(tmp_path):
    """Issue #3: .xcodeproj dizinleri artık mobile olarak işaretlenmeli."""
    p=tmp_path/'ios-app'; p.mkdir()
    # .xcodeproj bir dizindir; _walk_names artık dizin adlarını da toplar
    xcode=p/'MyApp.xcodeproj'; xcode.mkdir()
    (xcode/'project.pbxproj').write_text('// xcode')
    # Ek iOS dosya sinyalleri
    (p/'Info.plist').write_text('<?xml version="1.0">')
    (p/'AppDelegate.swift').write_text('import UIKit')
    r=run(KIT/'scripts/project_characteristics.py','--project-path',p)
    assert r.returncode==0, r.stderr
    d=json.loads(r.stdout)
    assert d['mobile']['detected'] is True, f'mobile not detected: {d["mobile"]}'
    assert d['mobile']['score'] >= 2


def test_reconfigure_legacy_custom_preserves_specialists(tmp_path):
    """Issue #4: legacy custom state ile --reconfigure uzman listesini korumalı."""
    p=tmp_path/'app'
    # İlk kurulum: custom + seçili uzmanlar
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','custom','--roles','coder,qa-reviewer')
    assert r.returncode==0, r.stderr
    state_path=p/'.opencode/hhc-team.json'
    state=json.loads(state_path.read_text(encoding='utf-8'))
    assert state['advanced_roles']==['coder','qa-reviewer']
    # Reconfigure ile profil değiştir
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','basic')
    assert r.returncode==0, r.stderr
    new_state=json.loads(state_path.read_text(encoding='utf-8'))
    # Uzmanlar korunmalı
    assert 'coder' in new_state['roles']
    assert 'qa-reviewer' in new_state['roles']
    assert new_state['advanced_roles']==['coder','qa-reviewer']
    # Profil değişmiş olmalı
    assert new_state['profile']=='basic'


def test_profile_policy_injected_once_and_only_to_managers(tmp_path):
    """Issue #4: profil policy yalnızca manager/working-manager rollerine ve birer kez enjekte edilmeli."""
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    agents_dir=p/'.opencode/agents'
    # working-manager policy overlay'e sahip olmalı (tek sefer)
    wm_text=(agents_dir/'working-manager.md').read_text(encoding='utf-8')
    assert 'Çalışma Profili: Standard' in wm_text
    assert wm_text.count('Çalışma Profili: Standard') == 1
    # Diğer rollerde policy OLMAMALI
    for agent in agents_dir.glob('*.md'):
        role=agent.stem
        if role in ('manager','working-manager'):
            continue
        text=agent.read_text(encoding='utf-8')
        assert 'Çalışma Profili:' not in text, f'{role} should not have policy overlay'


# ── /hhc-status tests ──

def test_status_reports_kit_version_and_roles_and_models(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard',
          '--model','working-manager=provider/mgr','--model','coder=provider/coder','--model','qa-reviewer=provider/qa')
    assert r.returncode==0, r.stderr
    r=run(KIT/'scripts/install.py','--project-path',p,'--status')
    assert r.returncode==0, r.stderr
    out=r.stdout
    kit_version=(KIT/'VERSION').read_text(encoding='utf-8').strip()
    assert kit_version in out
    assert 'Proje sürümü (state):' in out
    assert 'Global kit sürümü:' in out
    assert 'working-manager' in out and 'coder' in out and 'qa-reviewer' in out
    assert 'provider/mgr' in out and 'provider/coder' in out and 'provider/qa' in out
    assert 'Scout:' in out
    assert 'KAPALI' in out
    assert 'Profil:' in out and 'standard' in out

def test_status_requires_state(tmp_path):
    p=tmp_path/'app'; p.mkdir()
    r=run(KIT/'scripts/install.py','--project-path',p,'--status')
    assert r.returncode==0, r.stderr
    assert 'kurulu değil' in r.stdout or 'HHC kurulu değil' in r.stdout

def test_status_does_not_write_files(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    state_before=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    before_managed=set(state_before.get('managed_files',[]))
    r=run(KIT/'scripts/install.py','--project-path',p,'--status')
    assert r.returncode==0, r.stderr
    state_after=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    after_managed=set(state_after.get('managed_files',[]))
    assert before_managed==after_managed
    assert state_before['kit_version']==state_after['kit_version']
