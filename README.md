AI Assistant
====

This project implements various agents to make code improvements.

Name: 

### Timeline

Start Date: Feb 18

Finish Date: 

Hours Spent:

Phase 1 Deadline: Feb 21
Phase 2 Deadline: Feb 28
Phase 3 Deadline: Mar 6

### Tutorial, LLMs, and other Code used
- GPT-5.3 Codex - suggestions about how to use Ruff


### Resource Attributions


### Running the Program

Main class: `main.py`

Data files needed: any file you wish to inspect using our AI agents

Inputs: file path to reference the file, choice of agent (optional)

Known Bugs:

### Instructions
Create and activate virtual environment as below:
```
python3 -m venv <venv-name-here>
source <venv-name-here>/bin/activate # macOS/Linux
pip install -r requirements.txt
```

To run our application, you may choose between 4 agents: `CODE_STYLE`, `IDIOMS`, `TESTS`, `DESIGN`.

```
python -m src.main <path_to_your_file> --agent <agent_chosen> <include or exclude --apply flag>
python -m src.main data/sample_bad_code_style.py --agent CODE_STYLE --apply
```

### Notes/Assumptions
- To test the program, run
```python
python -m pytest -q
```

### Impressions

