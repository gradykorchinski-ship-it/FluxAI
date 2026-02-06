# FluxAI

FluxAI is a terminal-based AI chat application powered by Groq models.  
It provides a clean CLI interface with conversation memory, checkpoints, configuration options, and a strictly sandboxed agent mode.

The project is designed to be safe, predictable, and extensible, with all control logic handled by the CLI rather than the model.

---

## Features

- Interactive chat with persistent conversation context
- Conversation checkpoints with rewind support
- Configurable system prompt and model selection
- ANSI-colored output with optional toggle
- Safe, opt-in agent mode with strict action limits
- Human-in-the-loop execution for all agent actions
- No arbitrary command execution
- No background processes or hidden behavior

---

## Agent Mode (Safe by Design)

Agent mode allows the AI to *propose* and *execute* a very limited set of actions, only after user confirmation.

### Allowed actions:
- `pwd` – show current working directory
- `list_dir` – list files in the current directory
- `read_file <path>` – read a small text file

All actions are:
- Explicitly allow-listed
- Confirmed by the user before execution
- Executed locally by the CLI, not by the model

The model cannot run shell commands or modify files.

---

## Commands

### CLI Commands
- `/help` – show available commands
- `/exit` – exit the application
- `/clear` – clear conversation memory
- `/cls` – clear the console
- `/config` – edit configuration
- `/agent` – toggle agent mode on or off
- `<<N` – rewind to checkpoint N

### Agent Commands (agent mode only)
- `pwd`
- `list_dir`
- `read_file <path>`

---

## Installation

### Requirements
- Python 3.10 or newer
- A Groq API key

### Setup

```bash
git clone https://github.com/gradykorchinski-ship-it/FluxAI.git
cd FluxAI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
