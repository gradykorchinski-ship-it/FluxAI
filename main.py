import os
import sys
import copy
import re
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = (
    "You are an AI assistant embedded in a custom CLI application. "
    "Do not invent commands. "
    "Respond only to the user's message."
)

USE_COLORS = True
MODEL = "llama-3.1-8b-instant"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[36m"
BRIGHT_CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
GRAY = "\033[90m"

messages = []
checkpoints = []
AGENT_MODE = False

VALID_COMMANDS = {
    "/exit",
    "/clear",
    "/cls",
    "/help",
    "/config",
    "/agent",
}


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def render_markdown(text: str) -> str:
    if not USE_COLORS:
        text = re.sub(r"^### (.*)$", r"\1", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)", r"\1", text)
        text = re.sub(r"^\s*[-*] (.*)$", r"• \1", text, flags=re.MULTILINE)
        return text

    text = re.sub(r"^### (.*)$", lambda m: f"{YELLOW}{BOLD}{m.group(1)}{RESET}", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", lambda m: f"{BRIGHT_CYAN}{BOLD}{m.group(1)}{RESET}", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)", lambda m: f"{CYAN}{DIM}{m.group(1)}{RESET}", text)
    text = re.sub(r"^\s*[-*] (.*)$", lambda m: f"{GREEN}• {m.group(1)}{RESET}", text, flags=re.MULTILINE)
    return text


def print_banner():
    print(f"{BLUE}────────────────────────────────────────{RESET}")
    print(f"{BOLD} Flux AI CLI{RESET}")
    print(f" Model: {MODEL}")
    print(" Commands:")
    print("   /exit   Exit")
    print("   /clear  Clear conversation")
    print("   /cls    Clear console")
    print("   /help   Show help")
    print("   /config Edit config")
    print("   /agent  Toggle agent mode")
    print("   <<#     Rewind to checkpoint")
    print(f"{BLUE}────────────────────────────────────────{RESET}")


def print_ai_reply(text):
    print(f"\n{BOLD}{BLUE}AI:{RESET}")
    print(f"{BLUE}{'─' * 40}{RESET}")
    print(render_markdown(text.strip()))
    print(f"{BLUE}{'─' * 40}{RESET}")


def print_checkpoint(n):
    print(f"{GRAY}[checkpoint #{n}]{RESET}\n")


def print_rewind(n):
    print(f"\n{YELLOW}Rewound to checkpoint #{n}{RESET}\n")


def reset_conversation():
    global messages, checkpoints
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    checkpoints = [copy.deepcopy(messages)]


def allowed_action(action, arg=None):
    if action == "pwd":
        return os.getcwd()
    if action == "list_dir":
        return "\n".join(os.listdir("."))
    if action == "read_file":
        if not arg or not os.path.isfile(arg):
            return "Invalid file"
        if os.path.getsize(arg) > 10_000:
            return "File too large"
        with open(arg, "r", errors="ignore") as f:
            return f.read()
    return "Action not allowed"


def agent_execute(plan):
    for step in plan:
        if not isinstance(step, dict) or "action" not in step:
            print("Invalid agent step.")
            continue
        action = step["action"]
        arg = step.get("arg")
        print(f"\nProposed action: {action} {arg or ''}")
        if input("Execute? y/n: ").strip().lower() != "y":
            print("Skipped.")
            continue
        print(f"\nResult:\n{allowed_action(action, arg)}")


def main():
    global AGENT_MODE

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    clear_console()
    reset_conversation()
    print_banner()

    while True:
        user_input = input("> ").strip()

        if not user_input:
            continue

        if user_input.startswith("/") and user_input not in VALID_COMMANDS:
            print("Unknown command. Type /help for available commands.\n")
            continue

        if user_input == "/exit":
            if input("Exit? y/n: ").lower() == "y":
                print("Goodbye.")
                break
            continue

        if user_input == "/cls":
            clear_console()
            print_banner()
            continue

        if user_input == "/help":
            print(f"\n{GREEN}Model: {MODEL}{RESET}")
            print("Available commands:")
            print("  /exit    Exit the CLI")
            print("  /clear   Clear conversation")
            print("  /cls     Clear console")
            print("  /config  Edit configuration")
            print("  /agent   Toggle agent mode")
            print("  pwd | list_dir | read_file <path>  (agent mode)")
            print("  <<#      Rewind to checkpoint #\n")
            continue

        if user_input == "/config":
            print("Config menu not modified here.")
            continue

        if user_input == "/agent":
            AGENT_MODE = not AGENT_MODE
            print(f"\nAgent mode {'enabled' if AGENT_MODE else 'disabled'}.\n")
            continue

        if user_input == "/clear":
            reset_conversation()
            print("\nContext cleared.\n")
            continue

        if user_input.startswith("<<"):
            try:
                idx = int(user_input[2:])
                messages[:] = copy.deepcopy(checkpoints[idx])
                checkpoints[:] = checkpoints[: idx + 1]
                print_rewind(idx)
            except Exception:
                print("Invalid checkpoint number.\n")
            continue

        if AGENT_MODE:
            if user_input in ("pwd", "list_dir"):
                agent_execute([{"action": user_input}])
                continue

            if user_input.startswith("read_file "):
                agent_execute([{"action": "read_file", "arg": user_input.split(" ", 1)[1]}])
                continue

            agent_prompt = (
                "Respond ONLY with valid JSON array. "
                "Allowed actions: pwd, list_dir, read_file."
            )

            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": agent_prompt},
                    {"role": "user", "content": user_input},
                ],
            )

            try:
                plan = json.loads(r.choices[0].message.content)
            except Exception:
                print("Agent returned invalid plan.\n")
                continue

            agent_execute(plan)
            continue

        messages.append({"role": "user", "content": user_input})
        r = client.chat.completions.create(model=MODEL, messages=messages)
        reply = r.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        checkpoints.append(copy.deepcopy(messages))
        print_ai_reply(reply)
        print_checkpoint(len(checkpoints) - 1)


if __name__ == "__main__":
    main()
