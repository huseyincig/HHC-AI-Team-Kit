# Installation

[README](README.en.md) | [Türkçe kurulum](KURULUM.md)

## 1. Recommended: machine install from GitHub

### Windows

```powershell
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
HHC-KUR.cmd
```

### macOS / Linux

```bash
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
./HHC-KUR.sh
```

Requirements: Git and Python 3.9+.

## 2. Alternative: ZIP install

1. Download the current Release ZIP.
2. Extract it.
3. Run `HHC-KUR.cmd` on Windows or `./HHC-KUR.sh` on macOS/Linux.

Global OpenCode commands:

- `/hhc-install`
- `/hhc-install-remote`
- `/hhc-reconfigure`
- `/hhc-update`

## 3. Install into a target project

Open the project in OpenCode and run:

```text
/hhc-install
```

### Step 1 — Work profile

Only three profiles are offered:

- **Basic:** cost/context priority; higher specialist and parallelism threshold.
- **Standard:** **default/recommended** balanced SMART behavior.
- **Powerful:** quality/assurance priority; more proactive parallelism and verification for independent high-value work.

Profiles are not agent rosters. Core specialists remain available in all three.

### Step 2 — Project characteristics are inferred

HHC does not ask the user to choose Web/Desktop. It infers multi-label repository characteristics:

`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

A project may have multiple characteristics at once.

### Step 3 — Scout

OpenCode Scout is opt-in and defaults to **No**. It is profile-independent and used for external/current documentation, dependency, and upstream research. Local repository discovery stays with `repository-explorer`.

### Step 4 — Playwright

Playwright is offered only when `browser_ui` is verified. It remains opt-in/default-off and its tools are exposed only to `visual-qa`.

### Step 5 — Models

Model discovery and `model_advisor.py` are used for role assignments. Normal setup collects role-specific model choices and never silently upgrades models because Powerful was selected.

Scout receives a separate model when enabled.

### Normal primary/team behavior

The new normal UX no longer asks a top-level **Single Primary / Multi-Agent** question. Defaults are:

- primary: **Working Manager (`working-manager`)**
- backend: `multi + hands_on`
- all core specialists available
- SMART chooses which specialist to invoke per task

Legacy `single|multi`, shared-model, and orchestrator-primary paths remain available for migration/Advanced Configuration.

## 4. Advanced Configuration

The old Custom profile is no longer a main profile. Advanced users may explicitly restrict specialists with `--roles`, choose orchestrator primary, use one shared model, or force a project characteristic.

## 5. Parallelism and background

Background subagents are treated as usable by HHC only for independent work that does not require the parent to wait and cannot create file/state conflicts.

Dependent phases and overlapping edits remain sequential. Powerful does not run every role or duplicate the same role by default.

## 6. Legacy profile migration

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + preserved specialist list as Advanced Configuration

Existing role/model/Scout/Playwright choices are preserved where applicable.

## 7. Reconfigure

```text
/hhc-reconfigure
```

Changes profile, models, Scout/Playwright, and Advanced Configuration safely.

## 8. Update

```text
/hhc-update
```

Synchronizes to the new kit version while preserving state.

## 9. Existing `opencode.jsonc`

Existing user config is never silently overwritten. `subagent_depth: 1` remains preserved.

## 10. Remote target repository

```text
/hhc-install-remote <git-url>
```

Clones the target repo and applies the same Basic/Standard/Powerful SMART setup flow.
