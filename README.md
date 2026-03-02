AI Assistant
====

This project implements various agents to make code improvements.

Name: 

### Timeline

Start Date: Feb 18

Finish Date: 

Hours Spent:

Phase 1 Deadline: Feb 21

Phase 2 Deadline: Mar 1

Phase 3 Deadline: Mar 6

### Tutorial, LLMs, and other Code used
- GPT-5.3 Codex - suggestions about how to use Ruff
- Claude Code (Sonnet 4.6) - help understand minimal Extension API and its capabilities

### Resource Attributions


### Running the Program

Main class: `main.py`

Data files needed: any file you wish to inspect using our AI agents

Inputs: file path to reference the file, choice of agent (optional)

Known Bugs:

### VCM IDs of servers

- Main: http://vcm-52418.vm.duke.edu/
- Dev: http://vcm-52527.vm.duke.edu:4003/

### Instructions

#### CLI non-docker interface
Create and activate virtual environment as below:
```
python3 -m venv <venv-name-here>
source <venv-name-here>/bin/activate # macOS/Linux
pip install -r requirements.txt
```

To run our application, you may choose between 4 agents: `CODE_STYLE`, `IDIOMS`, `TESTS`, `DESIGN`.
If you run the application without specifying an agent, the system will run all four agents.

```
python -m src.main <path_to_your_file> --agent <agent_chosen> <include or exclude --apply flag>
python -m src.main data/sample_bad_code_style.py --agent CODE_STYLE --apply
```

#### Extension API
To try the extension, open `agent-extension/src/extension.ts` and press `F5`. This will open a new VSCode window. Open a new project/file that has python code (e.g. `data/sample_bad_*.py`) and type `AI Code Analysis: Analyze Current File` in the command palette(`Cmd + Shift + P`). Then click on the agent you wish to execute.

#### Server-deployed REST API
- To verify that the program is up and running on the server you can go to the dev server at http://vcm-52527.vm.duke.edu:4003/health
- To check that the http://vcm-52527.vm.duke.edu:4003/scan endpoint works you can run api_caller.py through ```python -m src.api_caller```

### Notes/Assumptions
- To test the program, run
```python
python -m pytest -q
```
- To check if program meets the project's style and quality standards before pushing run the local pipeline:
```bash
# Requires Docker to be running
gitlab-ci-local

### Impressions

