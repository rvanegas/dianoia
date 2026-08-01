# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Dianoia** is the server for an AI-powered argumentation platform. Users build structured logical arguments (thesis + assumptions → conclusion) and receive AI-generated evaluations and improvement recommendations via background agents. The companion UI is **Noesis** (`~/src/noesis`).

## Commands

### Backend

```bash
# Dev server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# or:
./bin/backend-dev

# Tests
pytest                        # all tests
pytest tests/test_file.py::TestClass::test_method -v  # single test
pytest -k "test_improvement"  # by keyword

# Type checking / linting / formatting
mypy .
pylint backend/
black --check .
```

### Full stack (with Docker)

```bash
./bin/dev-docker     # Docker Compose (backend + PostgreSQL)
docker-compose up --build
```

## Architecture

### Request Flow

```
Client (Noesis or other) → FastAPI routes (api/) → Service layer (services/) → Anthropic Claude
                                                         ↓
                                               Agent Coordinator (background threads)
                                                         ↓
                                               AgentResultManager (in-memory, TTL 3 days)
                                                         ↑
Client polls GET /api/agents/results ────────────────────────────────────────
```

### Backend Structure

- `api/argument.py` — Routes: `argue`, `assume`, `remove`, `replace`, `user-justify`, `explain`, `reject-formalization`, `endorse-formalization`, `upload`, `gen-name`
- `api/agents.py` — Routes: `GET /api/agents/results` (grouped by type, filtered by snapshot), `GET /api/agents/active`
- `services/agents.py` — Agent implementations: `ContentEvaluationAgent`, `FormalEvaluatorAgent`, `FormalizationAgent`, `ImprovementAgent`, `NameGenerationAgent`
- `services/agent_coordinator.py` — Thread-based task queue; `AgentResultManager` stores results keyed by `(conversation_id, snapshot_id)`; handles TTL cleanup and cooldown periods
- `services/agent_prompts.py` — All LLM prompt templates
- `services/argument_service.py` — Core argument manipulation (`next_symbol()`, `new_step()`, `clean_citations()`)
- `services/conversation.py` — `Gpt` wrapper class for name generation and explanations; uses `client.messages.create()` with `output_config` for structured JSON
- `services/openaiclient.py` — Anthropic client instance (named for historical reasons)
- `core/logic.py` — Modal first-order logic with predicate variables: `Variable`, `Constant`, `PredicateVariable`; `Formula` subclasses `Predicate`, `Identity`, `Connective`, `Quantifier`, `Modal`; each with `to_dict()` / `to_ascii()` / `from_json()`. See `LOGIC-ASCII.md` and `LOGIC-JSON.md` for the notation.
- `services/formalization_normalizer.py` — Replaces semantic names from the LLM (`is_mortal`, `socrates`) with canonical symbols before storage: predicates → `P Q R …` (first-appearance order across all steps), constants → `a b c …`, bound individual variables → `x y z …` (DFS order, per formula), bound predicate variables → `X Y Z …` (DFS order, per formula). The `ascii` field is always regenerated from the normalized JSON tree, never taken from model output.
- `schemas/` — Pydantic request/response schemas
- `startup_init.py` — Background thread that pre-warms GPT instances at server startup to avoid first-request delays

### Agent System

Agents run in background threads after each user action. The **ImprovementAgent** is the primary user-facing agent; it triggers after content/formal evaluation results are available and generates cohesive recommendation sets to strengthen the concluding proposition. Results are filtered by `snapshot_id` so stale results from earlier conversation states are not shown.

**Design decision — evaluators diagnose, the improver prescribes.** Evaluation agents (`truth_evaluator`, `content_validity_evaluator`, `form_evaluator`) emit only scores and diagnostic `logical_issues`; they carry no free-text `recommendations` field. The **improver is the sole producer of recommendations**, and every recommendation it emits is *applyable* — a structured `new`/`rewrite` proposition change (see the `ImprovementRecommendation` schema in `schemas/agent_results.py`), synthesized across all evaluators' diagnoses. This avoids the prior redundancy where each evaluator independently emitted unstructured, unapplyable prose suggestions. (The `phrasing_evaluator`'s per-symbol `recommendation` is a separate parseability concern and is unaffected.) The improver already fires automatically once per snapshot via the evaluate cascade, so no separate on-demand trigger is needed.

**Agent filtering:** `FilteredAgentInput` (in `schemas/agent_input.py`) strips irrelevant data before passing to each agent — the `ContentEvaluationAgent` never sees formalization data, the `FormalEvaluatorAgent` never sees natural-language proposition text. Use the class methods `for_content_evaluation()`, `for_formal_evaluation()`, `for_formalization()` when constructing agent inputs.

**Conversation ID format:** Composite key `"session_id:conversation_id"` — enables multi-conversation sessions from a single client session.

Agent trigger logic and cooldown periods live in `agent_coordinator.py`.

### Key Concepts

- **Snapshot**: Immutable capture of argument state at a point in time. Agent results are bound to a snapshot so recommendations remain coherent.
- **Formalization**: Each proposition can be given a formal logical representation (`core/logic.py`) that a user can endorse. The `FormalizationAgent` produces semantic-name JSON; `formalization_normalizer` canonicalizes it. Once all propositions are endorsed, the `FormalEvaluatorAgent` runs.
- **Improvement recommendations**: Sets of suggested proposition additions/rewrites produced by the `ImprovementAgent`, each with expected score improvements and reasoning.

### Test Patterns

Tests use FastAPI `TestClient`, mock `coordinator.queue_task()`, and patch LLM calls. Key test files: `test_api_argument.py` (route integration), `test_improvement_agent*.py` (trigger logic), `test_api_agents_stale_results.py` (snapshot filtering), `test_result_manager.py` (TTL/cleanup), `test_dual_evaluators.py` (content + formal interaction).

## Configuration

Config is read from `~/.config/dianoia/config.toml` with environment variable fallbacks:

```toml
anthropic_api_key = "..."
model = "claude-sonnet-4-6"
```

Or via environment variables: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`.
