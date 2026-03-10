# 影式 (Kage-Shiki)

**"Not yet divine. Not yet free."**

A Windows-resident text desktop mascot with a persistent personality and continuous memory across sessions.

Memory carries over between sessions, and the personality is frozen after initial generation. The relationship deepens through the accumulation of shared history (episodes). The mascot lives along window borders — its body — and reacts when you poke it.

## Key Features

- **Personality Generation System**: Three modes — AI-generated / User-described / Blank-slate nurturing. Personality is frozen after generation to ensure consistency
- **3-Layer Memory System**: Hot (personality core, injected every time) / Warm (recent summaries) / Cold (FTS5 search)
- **Persistent Memory**: Immediate write of conversation fragments to SQLite + FTS5, with daily summary distillation
- **Shutdown Resilience**: Two-layer defense via atexit / signal handler + startup recovery
- **Windows Resident**: System tray via pystray + borderless tkinter window

## Tech Stack

| Component | Selection |
|-----------|-----------|
| Language | Python 3.12+ |
| GUI | tkinter (standard library) |
| Tray Resident | pystray |
| LLM API | anthropic (official SDK) |
| DB | SQLite + FTS5 |
| Config | TOML (tomllib) |
| Testing | pytest |

## Phase Roadmap

| Phase | Contents | Status |
|-------|----------|--------|
| **Phase 1: Foundation (MVP)** | tkinter GUI + pystray tray, API connection, personality generation wizard, memory system, daily summaries | **Complete** |
| **Phase 2a: Foundation Enhancement** | LLMProtocol extraction, truncation, wizard GUI, integration test hardening | **Building** |
| **Phase 2: Autonomy** | Desire system, autonomous utterances, semantic search (sqlite-vec), forgetting curve | Not started |
| **Phase 3: Intelligence** | Curiosity system, Theory of Mind, approval-gated personality trend updates | Not started |
| **Phase 4: Maturity** | Consistency check improvements, monthly memory summarization | Not started |

### Phase 2a Progress

Tests: 722 passed / Coverage: 92%

Implemented modules:
- `main.py` — **Startup sequence integration** (13 steps + thread management + shutdown CB)
- `core/config.py` — TOML config parser + validation
- `core/env.py` — Environment variable management + API key verification
- `core/errors.py` — Error message definitions (EM-001 to EM-011)
- `core/logging_setup.py` — Log configuration (RotatingFileHandler)
- `core/shutdown_handler.py` — 2-layer shutdown defense (atexit + SetConsoleCtrlHandler)
- `agent/llm_client.py` — LLM client + LLMProtocol (purpose-based model slots)
- `agent/agent_core.py` — AgentCore ReAct loop + consistency check + click handling
- `agent/prompt_builder.py` — PromptBuilder (SystemPrompt + Messages + truncation)
- `agent/truncation.py` — Truncation algorithm constants + token estimation
- `agent/trends_proposal.py` — personality_trends approval flow (triggers + judgment)
- `agent/human_block_updater.py` — human_block self-editing (with guardrails)
- `memory/db.py` — SQLite + FTS5 CRUD + retry + Warm Memory loading
- `memory/memory_worker.py` — Daily summary generation + missing date backfill
- `persona/persona_system.py` — 3-stage persona loading + freeze control + freeze_and_save
- `persona/wizard.py` — Wizard mode A/B/C + preview + freeze + blank cultivation
- `gui/tkinter_view.py` — MascotView Protocol + borderless window
- `gui/wizard_gui.py` — Wizard GUI (tkinter dialog)
- `tray/system_tray.py` — pystray integration + menu + notifications

---

## Development Process (LAM Framework)

To quickly understand the LAM (Living Architect Model) concepts, see the Concept Overview Slides (`docs/slides/index.html`, planned for future creation).

### Phase Commands

| Command | Purpose | Prohibited |
|---------|---------|------------|
| `/planning` | Requirements, design, task decomposition | Code generation |
| `/building` | TDD implementation | Implementation without specs |
| `/auditing` | Review, audit, refactoring | PM-level fixes prohibited (PG/SE allowed) |
| `/project-status` | Display progress status | - |

### Approval Gates

```
requirements → [approval] → design → [approval] → tasks → [approval] → BUILDING → [approval] → AUDITING
```

User approval is required at the completion of each sub-phase. Proceeding without approval is prohibited.

### Subagents

| Agent | Purpose | Recommended Phase |
|-------|---------|-------------------|
| `requirement-analyst` | Requirements analysis, user stories | PLANNING |
| `design-architect` | API design, architecture | PLANNING |
| `task-decomposer` | Task breakdown, dependencies | PLANNING |
| `tdd-developer` | Red-Green-Refactor implementation | BUILDING |
| `quality-auditor` | Quality audit, security | AUDITING |
| `doc-writer` | Documentation creation, spec drafting, and updates | ALL |
| `test-runner` | Test execution and analysis | BUILDING |
| `code-reviewer` | Code review (LAM quality standards) | AUDITING |

### Session Management Commands

| Command | Purpose |
|---------|---------|
| `/quick-save` | Lightweight save (SESSION_STATE.md only) |
| `/quick-load` | Lightweight load (daily resume) |
| `/full-save` | Full save (commit + push + daily) |
| `/full-load` | Full load (resuming after days away) |

### Recommended Models

| Phase | Recommended Model |
|-------|-------------------|
| **PLANNING** | Claude Opus / Sonnet |
| **BUILDING** | Claude Sonnet (or Haiku for simple tasks) |
| **AUDITING** | Claude Opus (Long Context) |

---

## Requirements

| Requirement | Purpose | Required |
|-------------|---------|----------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | AI assistant runtime | Required |
| Python 3.12+ | Application runtime | Required |
| Git | Version control | Required |

## License

MIT License
