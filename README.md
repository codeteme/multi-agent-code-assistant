# AI-Powered Code Quality Assistant

> An agentic system that automatically scans, fixes, and validates Python code quality using specialized LLM-powered agents.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/linter-ruff-orange.svg)](https://docs.astral.sh/ruff/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

This is a multi-agent AI system that takes a Python file and runs it through a pipeline of four specialized agents. Each agent finds a specific category of issue, suggests targeted fixes, applies them, and verifies the result, retrying automatically if the fix didn't converge.

Unlike a simple linter, the tool understands why code is problematic, not just that it is. It can spot missing tests, un-Pythonic patterns, and structural design issues that static analysis tools miss entirely.

---

## Demo

```bash
$ python -m src.main data/sample.py --apply

[CodeStyle] Found 5 issue(s).
[CodeStyle] Validated on attempt 1.

[Idiom] Found 1 issue(s).
[Idiom] Validated on attempt 1.

[Clean Code] Found 2 issue(s).
[Clean Code] Validated on attempt 1.

[Testing] Found 2 issue(s).
[Testing] pytest returncode=0
[Testing] Validated on attempt 1.
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

The tool uses an evaluator-optimizer loop for each agent, which the same pattern used in production AI systems. After applying a fix, the agent re-scans the file and checks its own work. If issues remain, it regenerates suggestions with the new context and tries again (up to 3 times).

```
Input file
    │
    ▼
┌─────────────────────────────────────────────┐
│  Phase 1 (sequential)                       │
│  Style Agent → Idioms Agent → Clean Code    │
│  Each: scan → suggest → apply → validate    │
│         └─────── retry if needed ───────┘   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Phase 2                                    │
│  Testing Agent                              │
│  Reads final file, generates pytest tests,  │
│  validates by actually running pytest       │
└─────────────────────────────────────────────┘
    │
    ▼
Fixed file + generated test file
```

The testing agent always runs last — after the file has settled, so it generates tests against the final class and method names, not intermediate versions.

---

## Agents

| Agent | Tool | What it fixes |
|-------|------|---------------|
| **Style** | Ruff | Imports, spacing, formatting, naming conventions |
| **Idioms** | LLM | Un-Pythonic patterns (`range(len(x))`, bare `except`, `== None`, etc.) |
| **Clean Code** | LLM | Magic strings/numbers, functions doing too much, deep nesting, dead code |
| **Testing** | LLM + pytest | Missing tests, untested edge cases, weak assertions |

The Style agent uses Ruff directly (no LLM) making it fast, deterministic, and free. The other agents use an LLM for judgment, but apply fixes using **exact string replacement** rather than letting the LLM rewrite the entire file. This prevents hallucination and keeps changes surgical.

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
│   └── testing_agent.py
├── util/
│   ├── controller.py           # Orchestrates agent execution and retry loop
│   ├── planner.py              # Determines which agents run and in what order
│   ├── llm_scanner.py          # Sends scan prompts to the LLM
│   ├── llm_generator.py        # Sends suggestion prompts to the LLM
│   ├── text_applier.py         # Applies fixes via exact string replacement
│   ├── testing_applier.py      # Writes generated tests to test files
│   ├── code_style_scanner.py   # Wraps Ruff
│   ├── code_style_applier.py   # Wraps ruff --fix and ruff format
│   └── validator.py            # Shared validation logic
├── api.py                      # REST API
└── main.py                     # CLI entry point
prompts/
├── cleancode/                  # scan.txt, generate_suggestions.txt, apply.txt
├── idioms/                     # scan.txt, generate_suggestions.txt, apply.txt
└── testing/                    # scan.txt, generate_suggestions.txt
```

Prompts live in plain text files (not hardcoded strings) so they can be versioned, diffed, and iterated on independently of the code.

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

---

## Usage

### CLI

```bash
# Scan only — no changes made
python -m src.main path/to/file.py

# Run a specific agent
python -m src.main path/to/file.py --agent CODE_STYLE
python -m src.main path/to/file.py --agent IDIOMS
python -m src.main path/to/file.py --agent CLEAN_CODE
python -m src.main path/to/file.py --agent TESTS

# Run all agents and apply fixes
python -m src.main path/to/file.py --apply
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

Tests mock the LLM client, so no API calls are made during CI. Each agent and utility has its own test file mirroring the `src/` structure.

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

**Why sequential agents instead of parallel?**
All agents write to the same file. Running them in parallel caused race conditions where one agent's fix would be overwritten by another. Sequential execution with a defined order (style then idioms then clean code then testing) ensures each agent builds on a stable foundation.

**Why string replacement instead of LLM rewriting?**
Early versions used the LLM to rewrite the entire file when applying fixes. The LLM would invent domain-specific variable names (`customer_id`, `max_retries`) for ambiguous single-letter variables, add methods that weren't requested, and generally hallucinate. String replacement applies only the exact `original_code` - `fixed_code` pairs from the suggestions and nothing else changes.

**Why does the testing agent run last?**
The other agents may rename classes or methods. If the testing agent generated tests against `myClass` and then the clean code agent renamed it to `MyClass`, the tests would fail with `NameError`. Running last ensures the testing agent sees the final, stable version of the file.

---

## Known limitations

- The Clean Code and Idioms agents use LLM-based scanning, so results vary between runs. The retry loop mitigates this but convergence is not guaranteed on highly subjective issues.
- The Testing Agent generates tests for whatever class names exist in the file at run time. Stale test files from previous runs are overwritten on each attempt.
- Ruff is required to be installed in the environment — it is not bundled in the Docker image by default.

---

## License

MIT