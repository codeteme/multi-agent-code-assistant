# AI-Powered Code Quality Assistant

> An agentic system that automatically scans, fixes, and validates Python code quality using specialized LLM-powered agents — with optional agentic mode where the LLM drives the entire loop.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/linter-ruff-orange.svg)](https://docs.astral.sh/ruff/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

This is a multi-agent AI system that takes a Python file and runs it through a pipeline of four specialized agents. Each agent finds a specific category of issue, suggests targeted fixes, applies them, and verifies the result.

The system supports two execution modes:

- **Rigid pipeline** — a deterministic Python loop drives `scan → suggest → apply → validate`, retrying up to 3 times per agent.
- **Agentic mode** — the LLM receives the same tools as callable functions and decides autonomously what to call, in what order, and when to stop.

The Testing agent adds a **RAG layer**: it queries a ChromaDB vector store of existing test files and injects the most similar examples into its prompts so generated tests match the project's conventions.

---

## Demo

```bash
# Rigid pipeline — deterministic, fast
python -m src.main data/sample.py --apply

# Agentic mode — LLM drives the loop
python -m src.main data/sample.py --agent CLEAN_CODE --apply --agentic

# Testing agent with RAG (seed the store first)
python -c "from src.util.test_store import seed; seed()"
python -m src.main data/sample.py --agent TESTS --apply
```

**Input:**
```python
import os,sys
x=10
class   myClass:
    def __init__(self,name):
        self.name=name
    def getName( self ):
        if self.name=="":
            return "no name"
        else:
            return self.name
```

**Output:**
```python
import sys

x = 10


class MyClass:
    NO_NAME_PLACEHOLDER = "no name"

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name if self.name else self.NO_NAME_PLACEHOLDER
```

---

## How it works

### Rigid pipeline

Each agent runs through an evaluator-optimizer loop. After applying a fix, the agent re-scans the file and checks its own work. If issues remain, it regenerates suggestions with the new context and tries again (up to 3 times).

```
Input file
    │
    ▼
┌─────────────────────────────────────────────┐
│  Planner                                    │
│  Heuristics + run memory → agent list       │
│  (skips agents that passed last run)        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Phase 1 (sequential)                       │
│  Style → Idioms → Clean Code                │
│  Each: scan → suggest → apply → validate    │
│         └─────── retry if needed ───────┘   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Phase 2                                    │
│  Testing Agent  (RAG-enhanced)              │
│  Retrieves similar test files from ChromaDB │
│  Generates pytest tests, validates with     │
│  pytest                                     │
└─────────────────────────────────────────────┘
    │
    ▼
Fixed file + generated test file
```

### Agentic mode

Instead of a scripted loop, the LLM is given four tools (`scan`, `get_suggestions`, `apply`, `validate`) and a system prompt instructing it to iterate autonomously. The controller executes whatever tools the LLM requests and feeds results back into the conversation. A hard cap of 3 validate calls prevents infinite loops.

```
Input file + agent name
    │
    ▼
AgenticController
    │
    ├── messages = [system_prompt, user_request]
    │
    └── while LLM calls tools:
          LLM → tool_call (scan / get_suggestions / apply / validate)
          execute_tool() → result
          append result to messages
          LLM sees result → decides next tool
          stop when LLM is satisfied or validate_count == 3
```

### RAG layer (Testing agent)

```
seed() — run once:
  all tests/**/*.py → embed → ChromaDB (.chromadb/)

At scan/suggest time:
  source code → query ChromaDB → top-2 similar test files
  injected as {{ retrieved_examples }} in prompts
  LLM generates tests that match project conventions
```

---

## Agents

| Agent | Tool | What it fixes |
|-------|------|---------------|
| **Style** | Ruff | Imports, spacing, formatting, naming conventions |
| **Idioms** | LLM | Un-Pythonic patterns (`range(len(x))`, bare `except`, `== None`, etc.) |
| **Clean Code** | LLM | Magic strings/numbers, functions doing too much, deep nesting, dead code |
| **Testing** | LLM + RAG + pytest | Missing tests, untested edge cases, weak assertions |

The Style agent uses Ruff directly (no LLM) — fast, deterministic, and free. The other agents use an LLM for judgment but apply fixes using **exact string replacement** rather than letting the LLM rewrite the entire file, preventing hallucination.

---

## Architecture

```
src/
├── agents/
│   ├── abstract_agent.py       # Base class: scan, get_suggestions, apply, validate
│   ├── registry.py             # Maps agent names to classes
│   ├── code_style_agent.py
│   ├── idioms_agent.py
│   ├── clean_code_agent.py
│   └── testing_agent.py        # RAG-enhanced: calls retrieve() before scan/suggest
├── util/
│   ├── controller.py           # Rigid pipeline: scripted scan→suggest→apply→validate loop
│   ├── agentic_controller.py   # Agentic mode: LLM decides which tools to call
│   ├── planner.py              # Heuristic agent selection + run memory
│   ├── llm_scanner.py          # Sends scan prompts to the LLM
│   ├── llm_generator.py        # Sends suggestion prompts to the LLM
│   ├── text_applier.py         # Applies fixes via exact string replacement
│   ├── testing_applier.py      # Writes generated tests to test files
│   ├── test_store.py           # RAG: seed() and retrieve() via ChromaDB
│   ├── code_style_scanner.py   # Wraps Ruff
│   ├── code_style_applier.py   # Wraps ruff --fix and ruff format
│   ├── run_memory.py           # Persists per-file agent results across runs
│   └── validator.py            # Shared validation logic
├── api.py                      # REST API
└── main.py                     # CLI entry point — routes to controller or agentic_controller
prompts/
├── cleancode/                  # scan.txt, generate_suggestions.txt, apply.txt
├── idioms/                     # scan.txt, generate_suggestions.txt, apply.txt
└── testing/                    # scan.txt, generate_suggestions.txt
                                # both include {{ retrieved_examples }} for RAG injection
.chromadb/                      # ChromaDB vector store (created by seed())
```

---

## Getting started

### Prerequisites

- Python 3.11+
- [Ruff](https://docs.astral.sh/ruff/)
- An LLM API key (OpenAI-compatible endpoint)

### Install

```bash
git clone https://github.com/yourname/multi-agent-code-assistant.git
cd multi-agent-code-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
LITELLM_TOKEN=your_api_key_here
LLM_API_URL=https://your-llm-endpoint/v1
MODEL_ID=gpt-4
```

### Seed the RAG store (one-time)

```bash
python -c "from src.util.test_store import seed; seed()"
```

Re-run this whenever you add or change test files.

---

## Usage

### CLI

```bash
# Scan only — no changes made
python -m src.main path/to/file.py

# Run a specific agent (rigid pipeline)
python -m src.main path/to/file.py --agent CODE_STYLE
python -m src.main path/to/file.py --agent IDIOMS
python -m src.main path/to/file.py --agent CLEAN_CODE
python -m src.main path/to/file.py --agent TESTS

# Run all agents and apply fixes
python -m src.main path/to/file.py --apply

# Agentic mode — LLM drives the scan→fix→validate loop
python -m src.main path/to/file.py --agent CLEAN_CODE --apply --agentic
```

Try it on the included samples:
```bash
python -m src.main data/sample_bad_code_style.py --apply
python -m src.main data/sample_bad_idioms.py --apply
python -m src.main data/sample_all_issues.py --apply

# Reset samples between runs
git checkout data/sample_*.py
```

### REST API

```bash
# Start locally
docker-compose up --build

# Check health
curl http://localhost:8000/health

# Analyze a file
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample_bad_code_style.py", "apply": true}'

# Run a specific agent only
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample_bad_code_style.py", "agent": "IDIOMS", "apply": true}'
```

### VS Code Extension

Install and usage instructions are in [`agent-extension/README.md`](agent-extension/README.md).

---

## Running tests

```bash
# Run all tests
python -m pytest -q

# With coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

Tests mock the LLM client, so no API calls are made during CI.

---

## Deployment

The app ships as a single Docker container with a REST API.

```bash
docker build -t refactor .
docker run -p 8000:8000 --env-file .env refactor
```

Live deployment:
- **Production:** http://vcm-52418.vm.duke.edu/
- **Staging:** http://vcm-52527.vm.duke.edu:4003/

---

## Design decisions

**Why two execution modes (rigid vs agentic)?**
The rigid pipeline is fast, deterministic, and easy to debug — ideal for CI. Agentic mode lets the LLM adapt its strategy based on what it finds, which handles unusual code patterns better but adds latency and non-determinism. Both share the same four agents.

**Why sequential agents instead of parallel?**
All agents write to the same file. Running them in parallel caused race conditions. Sequential execution with a defined order (style → idioms → clean code → testing) ensures each agent builds on a stable foundation.

**Why string replacement instead of LLM rewriting?**
Early versions used the LLM to rewrite the entire file when applying fixes. The LLM would hallucinate domain-specific variable names and add methods that weren't requested. String replacement applies only the exact `original_code` → `fixed_code` pairs from the suggestions.

**Why does the testing agent run last?**
The other agents may rename classes or methods. Running last ensures the testing agent sees the final, stable version of the file and generates tests against the correct names.

**Why RAG only for the Testing agent?**
The Style, Idioms, and Clean Code agents rely on rules already in GPT-4.1's training data. The Testing agent benefits from seeing how *this specific codebase* writes tests — conventions, fixture patterns, naming styles — which RAG provides by retrieving the most similar existing test files.

**Why ChromaDB for RAG?**
It runs locally with no external service dependency, stores embeddings on disk, and supports semantic similarity queries out of the box.

---

## Known limitations

- The Clean Code and Idioms agents use LLM-based scanning, so results vary between runs. The retry loop mitigates this but convergence is not guaranteed on highly subjective issues.
- The Testing agent generates tests for whatever class names exist in the file at run time. Stale test files from previous runs are overwritten on each attempt.
- Ruff must be installed in the environment.
- The RAG store must be seeded before the Testing agent can use retrieval. If the store is empty, the agent falls back to prompt-only generation.

---

## License

MIT
