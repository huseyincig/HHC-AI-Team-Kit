# HHC AI Team Kit

[Türkçe](README.md) | [English](README.en.md)

**Version: 1.2.3**

HHC AI Team Kit installs a small, SMART, model- and provider-independent AI software team into OpenCode projects. It uses OpenCode's native primary/subagent, Task, skill, command, and permission mechanisms instead of building a second orchestration framework.

## Quick Install

### Recommended: install from GitHub

**Windows**

```powershell
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
HHC-KUR.cmd
```

**macOS / Linux**

```bash
git clone https://github.com/huseyincig/HHC-AI-Team-Kit.git
cd HHC-AI-Team-Kit
./HHC-KUR.sh
```

Then open the target project in OpenCode and run:

```text
/hhc-install
```

The setup assistant asks for the work profile, Scout/Playwright opt-ins, and role-based model assignments. Project characteristics such as Web/Desktop are inferred from the repository whenever possible.

> Requirements: Git and Python 3.9+.

### Install from ZIP

1. Download the current ZIP from GitHub Releases.
2. Extract it.
3. Run `HHC-KUR.cmd` on Windows or `./HHC-KUR.sh` on macOS/Linux.
4. Run `/hhc-install` inside the target project.

Details: [INSTALLATION.md](INSTALLATION.md)

## Highlights

- **SMART routing:** selects the smallest useful team instead of running a fixed agent chain.
- **Three simple work profiles:** Basic, Standard, and Powerful change work policy, not specialist availability.
- **Automatic project characteristics:** multi-label detection for browser UI, desktop UI, backend, CLI, library, database, WordPress, containers, and mobile signals.
- **Low agent/context overhead:** specialists are invoked only when they add real quality, independence, or context-isolation value.
- **Role-based model selection:** capability, context limits, and cost are used when verifiable.
- **Local vs external research:** `repository-explorer` handles local code; OpenCode Scout handles external/current sources.
- **On-demand skills:** detailed skill bodies load only when needed.
- **Deterministic evidence first:** tests/build/lint/diff are preferred over redundant LLM review.
- **Controlled parallelism:** independent work may run in the background; dependent or conflicting work stays sequential.
- **Opt-in Playwright:** offered only when `browser_ui` is detected and scoped to `visual-qa`.
- **MCP default-off:** reliable CLI tools stay CLI tools.
- **Depth guard:** `subagent_depth: 1` is preserved.

## SMART Workflow

```text
User
  ↓
Working Manager short pre-flight
  ↓
Work-profile policy + project characteristics
  ↓
Smallest useful specialist set
  ↓
Role-assigned model
  ↓
Scout / QA / Security / Visual QA when justified
  ↓
Deterministic + specialist evidence
  ↓
Enough evidence → STOP
```

**SMART does not mean more agents.** It means better intent interpretation, narrower delegation, less unnecessary context/LLM work, and stopping when enough evidence exists.

## Work Profiles

Profiles are no longer agent rosters. Core specialists remain available in all three profiles; the profile changes invocation, parallelism, and verification intensity.

| Profile | Best for | Behavior |
|---|---|---|
| **Basic** | Cost/context efficiency | Higher specialist threshold, conservative parallelism, second opinions only for critical risk. Required specialists remain available. |
| **Standard** | Most projects | **Default and recommended.** Minimum useful team, risk-based QA/Security/Visual QA, controlled parallelism for independent work. |
| **Powerful** | Quality/assurance priority | Lower specialist/review threshold and more proactive parallelism for independent high-value work. It does not run every agent or duplicate roles by default. |

`web-development`, `desktop-development`, `high-assurance`, `minimal`, and `custom` are no longer new-install choices; they are recognized only for safe legacy migration.

## Project Characteristics

HHC can infer multiple characteristics at once instead of forcing a single project-type enum:

`browser_ui`, `desktop_ui`, `backend`, `cli`, `library`, `database`, `wordpress`, `containerized`, `mobile`.

A React + .NET + Docker project can therefore be browser-facing, backend, and containerized at the same time. Detection uses multiple repository signals; a weak single clue is not treated as certainty.

## Roles

| Display name | Technical ID | Responsibility |
|---|---|---|
| **Working Manager** | `working-manager` | Handles small/medium work directly and delegates only when useful. Normal primary agent. |
| **Orchestrator** | `manager` | Read-only orchestration/quality-gate primary for Advanced Configuration. |
| **Architect** | `architect` | Handles real architecture, contracts, data-model, and boundary changes. |
| **Repository Explorer** | `repository-explorer` | Finds relevant files/symbols/dependencies/tests with narrow context. |
| **Coder** | `coder` | Implements changes and runs relevant deterministic checks. |
| **QA Reviewer** | `qa-reviewer` | Reviews diff, tests, acceptance criteria, and regression risk. |
| **Security Reviewer** | `security-reviewer` | Handles auth, permission, mutation, network, dependency, and other security boundaries. |
| **Visual QA** | `visual-qa` | Validates UI/layout/responsive/interaction changes with visual/browser evidence. |

Normal users do not need to choose a role roster. The old Custom profile is now an Advanced Configuration specialist override.

## Skill System

HHC ships 13 on-demand skills:

`task-classification`, `repository-analysis`, `implementation-planning`, `safe-refactoring`, `code-review`, `test-strategy`, `regression-review`, `visual-qa`, `accessibility-review`, `browser-testing`, `security-review`, `release-guardrails`, `changelog-and-documentation`.

## Model Selection

Normal setup asks the user to assign models to installed roles. Profiles never silently promote roles to more expensive models: **ROLE → ASSIGNED MODEL** remains the rule.

`model_advisor.py` can classify verifiable capability metadata as RECOMMENDED / COMPATIBLE / WARNING / INCOMPATIBLE. Unknown capability/cost data is not invented, and there is no runtime model router or silent premium fallback.

A shared model remains available as an Advanced Configuration option and does not change the work profile.

## OpenCode Scout

Scout is profile-independent, opt-in, and disabled by default. It is for external documentation, dependencies, upstream source, and current information. Local repository discovery stays with `repository-explorer`.

## Playwright

Playwright is no longer coupled to a `web-development` profile. It is offered only when `browser_ui` is detected and remains opt-in/default-off. Its tools are denied globally and allowed only for `visual-qa`.

## Parallelism and Powerful Safety Valves

Background subagents are treated as usable by HHC, but only for work that is dependency-independent, does not require the parent to wait, and cannot cause file/state conflicts.

Architecture → implementation → tests and conflicting file edits remain sequential. Powerful does not duplicate the same role by default; a second review is justified only when it can produce genuinely independent evidence for important/critical work. Stop after deterministic evidence and required quality gates pass.

## Reconfigure and Update

`/hhc-reconfigure` changes the profile, model assignments, Scout/Playwright choices, and Advanced Configuration overrides while safely migrating legacy profiles.

`/hhc-update` synchronizes to a newer kit version while preserving state.

`/hhc-status` reports the current HHC configuration status read-only (version, profile, roles, models, Scout, Playwright, MCP).

## Technical Notes

The project state now records `profile`, a small `profile_policy`, and multi-label `project_characteristics`. `subagent_depth: 1` remains unchanged. Existing user `opencode.jsonc` is never silently overwritten.

### Legacy migration

- `minimal` → `basic`
- `standard` → `standard`
- `high-assurance` → `powerful`
- `web-development` → `standard` + `browser_ui`
- `desktop-development` → `standard` + `desktop_ui`
- `custom` → `standard` + preserved specialist list as Advanced Configuration

## Test and Validation

```bash
python scripts/validate.py
python -m pytest -q
python scripts/release-build.py
```

## Contributing, Security, and License

- [INSTALLATION.md](INSTALLATION.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [LICENSE](LICENSE)
