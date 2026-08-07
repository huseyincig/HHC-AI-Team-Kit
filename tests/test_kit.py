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


def test_roles_only_allowed_for_custom_profile(tmp_path):
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard','--roles','coder,qa-reviewer')
    assert r.returncode!=0


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


def test_reconfigure_removes_old_hhc_roles_but_keeps_user_files(tmp_path):
    p=tmp_path/'app'
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0
    user=p/'.opencode/agents/my-private-agent.md'; user.write_text('kullanıcı dosyası',encoding='utf-8')
    assert (p/'.opencode/agents/architect.md').exists()
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--team-mode','multi','--preset','minimal','--manager-mode','orchestrator','--shared-model','provider/team')
    assert r.returncode==0, r.stderr
    assert not (p/'.opencode/agents/architect.md').exists()
    assert user.read_text(encoding='utf-8')=='kullanıcı dosyası'
    assert (p/'.opencode/agents/manager.md').exists()
    assert not (p/'.opencode/agents/working-manager.md').exists()
    state=json.loads((p/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['preset']=='minimal' and state['manager_mode']=='orchestrator'


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
    assert (root/'hhc-install-remote.md').is_file()
    assert (root/'hhc-reconfigure.md').is_file()
    text=(root/'hhc-install.md').read_text(encoding='utf-8')
    assert 'Profil — her zaman ilk soru' in text and 'Tek Ana Ajan' in text and 'Çoklu Ajan Ekibi' in text and 'model_discovery.py' in text
    assert 'kurulu **her rol için** bir `--model role=provider/model`' in text
    assert 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in text


def test_adopts_identical_pre_state_install_for_future_reconfigure(tmp_path):
    p=tmp_path/'app'
    # rc.12 benzeri: dosyalar var fakat hhc-team.json yok.
    assert run(KIT/'scripts/install.py','--project-path',p,'--preset','standard').returncode==0
    state=p/'.opencode/hhc-team.json'; state.unlink()
    # Aynı kurulum yeniden çalışınca mevcut birebir HHC dosyaları güvenle sahiplenilir.
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','standard')
    assert r.returncode==0, r.stderr
    data=json.loads(state.read_text(encoding='utf-8'))
    assert '.opencode/agents/architect.md' in data['managed_files']
    assert data['config_created_by_hhc'] is True
    # Artık profil değişikliği eski HHC rolünü temizleyebilir.
    r=run(KIT/'scripts/install.py','--project-path',p,'--reconfigure','--preset','minimal')
    assert r.returncode==0, r.stderr
    assert not (p/'.opencode/agents/architect.md').exists()


def test_custom_profile_multi_requires_specialists_but_single_may_be_manager_only(tmp_path):
    p=tmp_path/'multi'
    r=run(KIT/'scripts/install.py','--project-path',p,'--team-mode','multi','--preset','custom')
    assert r.returncode!=0
    p2=tmp_path/'single'
    r=run(KIT/'scripts/install.py','--project-path',p2,'--team-mode','single','--preset','custom','--shared-model','provider/shared')
    assert r.returncode==0, r.stderr
    state=json.loads((p2/'.opencode/hhc-team.json').read_text(encoding='utf-8'))
    assert state['roles']==['working-manager']


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
    assert 'Preset' in skill and 'sabit pipeline değildir' in skill
    assert 'Kararı değiştirmeyecek bilinmeyeni araştırma' in skill
    assert 'Context taşıma; referans taşı' in skill
    assert len(skill.encode('utf-8')) < 7000
    p=tmp_path/'app'
    r=run(KIT/'scripts/install.py','--project-path',p,'--preset','minimal')
    assert r.returncode==0, r.stderr
    assert (p/'.opencode/skills/task-classification/SKILL.md').is_file()


def test_manager_uses_minimum_team_not_fixed_pipeline():
    for name in ('manager','working-manager'):
        text=(KIT/f'roles/{name}.md').read_text(encoding='utf-8')
        assert 'minimum' in text.lower()
        assert 'ihtiyaç' in text.lower() and 'genişlet' in text.lower()
        assert 'task-classification' in text
        assert 'her rol' in text.lower() or 'sabit pipeline' in text.lower()


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


def test_presets_are_capability_pools_and_include_classification():
    for name in ('minimal','standard','custom'):
        data=json.loads((KIT/f'presets/{name}.json').read_text(encoding='utf-8'))
        assert 'task-classification' in data['skills']
    # Standard kadro korunur; optimizasyon kurulumda rol silerek yapılmaz.
    standard=json.loads((KIT/'presets/standard.json').read_text(encoding='utf-8'))
    assert {'manager','architect','repository-explorer','coder','qa-reviewer','visual-qa'} <= set(standard['roles'])


def test_legacy_solo_agent_is_not_shipped_and_wizard_does_not_offer_solo_mode():
    assert not (KIT/'roles/solo-agent.md').exists()
    wizard=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    assert 'Tam bağımsız tek ajan' in wizard  # yasaklanan seçenek olarak anılır
    assert 'Yalnız iki seçenek sun' in wizard
    assert 'Tek Ana Ajan' in wizard and 'Çoklu Ajan Ekibi' in wizard


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
        exe.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
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


def test_manager_only_delegates_to_available_agents():
    for name in ('manager','working-manager'):
        text=(KIT/f'roles/{name}.md').read_text(encoding='utf-8').lower()
        assert 'gerçekten mevcut' in text and 'çağrılabilir' in text


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


def test_rc18_wizard_profile_is_first_and_multi_model_flow_is_deterministic():
    text=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    assert text.index('## 1. Profil') < text.index('## 2. Çalışma biçimi')
    assert '### Çoklu Ajan Ekibi — zorunlu rol bazlı akış' in text
    assert 'her rol için ayrı model cevabı topla' in text
    assert 'Bir rol için verilen cevabı başka role otomatik kopyalama' in text
    assert 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in text
    assert 'kurulu **her rol için** bir `--model role=provider/model`' in text


def test_rc17_user_visible_role_labels_are_turkish():
    text=(KIT/'bootstrap/commands/hhc-install.md').read_text(encoding='utf-8')
    for label in ('Çalışan Yönetici','Orkestratör','Mimar','Depo Gezgini','Kodlayıcı','Kalite İnceleyici','Görsel QA','Güvenlik İnceleyici'):
        assert label in text
    assert "Teknik agent ID'lerini kullanıcıya gösterme" in text


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


def test_rc17_reconfigure_uses_same_new_decision_tree():
    text=(KIT/'bootstrap/commands/hhc-reconfigure.md').read_text(encoding='utf-8')
    assert 'aynı karar ağacını' in text
    assert 'Önce profil' in text
    assert 'Tek Ana Ajan' in text and 'Çoklu Ajan Ekibi' in text
    assert 'solo-agent' in text and 'Eski rc.16 state' in text


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


def test_rc18_reconfigure_multi_model_flow_is_role_complete():
    text=(KIT/'bootstrap/commands/hhc-reconfigure.md').read_text(encoding='utf-8')
    assert 'Kurulu ekipte N rol varsa N ayrı model kararı alınmalıdır.' in text
    assert 'Bir rolün cevabını başka role otomatik uygulama.' in text
    assert 'kurulu her rol için açık `--model role=provider/model`' in text


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
    assert 'her rol için ayrı model cevabı topla' in install
    assert 'Bütün rollerin modeli belirlenmeden model adımından çıkma' in install
