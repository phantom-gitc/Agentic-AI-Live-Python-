"""
🧪 THE CRAZY INVENTION FACTORY (LangGraph Edition)
Short, hilarious, and beautiful CLI.
"""

import os
import sys
import textwrap

# Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import TypedDict
from dotenv import load_dotenv
from colorama import Fore, Style, init

from google import genai
from langgraph.graph import StateGraph, START, END

init(autoreset=True)

# ---------------------------------------------------------
# 1. Gemini Client Setup
# ---------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


def ask_gemini(prompt: str) -> str:
    """Helper to query Gemini with tight, short responses."""
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={"automatic_function_calling": {"disable": True}}
        )
        return response.text.strip().replace("\n", " ")
    except Exception as e:
        return f"[Glitch: {e}]"


# ---------------------------------------------------------
# 2. State Definition (Simple TypedDict)
# ---------------------------------------------------------
class InventionState(TypedDict):
    topic: str
    invention: str
    pitch: str
    warning: str


# ---------------------------------------------------------
# 3. Graph Nodes (SHORT, PUNCHY & HILARIOUS)
# ---------------------------------------------------------
def scientist_node(state: InventionState) -> dict:
    prompt = (
        f"Invent an absurd, funny sci-fi gadget based on '{state['topic']}'. "
        "Limit your answer to strictly ONE short sentence (under 20 words). Be hilarious!"
    )
    res = ask_gemini(prompt)
    print(f"\n {Fore.CYAN}🧪 [1/3] SCIENTIST:{Style.RESET_ALL} {res}")
    return {"invention": res}


def salesman_node(state: InventionState) -> dict:
    prompt = (
        f"You are a hyper TV infomercial host pitching: '{state['invention']}'. "
        "Give a loud, funny sales pitch in strictly ONE short sentence (under 25 words)."
    )
    res = ask_gemini(prompt)
    print(f"\n {Fore.YELLOW}📢 [2/3] INFOMERCIAL:{Style.RESET_ALL} {res}")
    return {"pitch": res}


def warning_node(state: InventionState) -> dict:
    prompt = (
        f"Write a funny legal/medical warning label for: '{state['invention']}'. "
        "Strictly ONE short sentence (under 20 words)."
    )
    res = ask_gemini(prompt)
    print(f"\n {Fore.RED}⚠️  [3/3] WARNING:{Style.RESET_ALL} {res}")
    return {"warning": res}


# ---------------------------------------------------------
# 4. Build LangGraph
# ---------------------------------------------------------
builder = StateGraph(InventionState)

builder.add_node("scientist", scientist_node)
builder.add_node("salesman", salesman_node)
builder.add_node("warning", warning_node)

builder.add_edge(START, "scientist")
builder.add_edge("scientist", "salesman")
builder.add_edge("salesman", "warning")
builder.add_edge("warning", END)

app = builder.compile()


# ---------------------------------------------------------
# 5. Beautiful CLI
# ---------------------------------------------------------
def print_banner():
    print(Fore.MAGENTA + Style.BRIGHT + "\n╔" + "═" * 62 + "╗")
    print(Fore.MAGENTA + Style.BRIGHT + "║" + Fore.CYAN + Style.BRIGHT + "        ⚡ THE CRAZY INVENTION FACTORY (LangGraph) ⚡         " + Fore.MAGENTA + Style.BRIGHT + "║")
    print(Fore.MAGENTA + Style.BRIGHT + "║" + Fore.LIGHTWHITE_EX + "    Turn any boring word into an absurd sci-fi product!       " + Fore.MAGENTA + Style.BRIGHT + "║")
    print(Fore.MAGENTA + Style.BRIGHT + "╚" + "═" * 62 + "╝")


def wrap_text(label: str, text: str, color: str, width: int = 60) -> None:
    indent = "    "
    wrapped = textwrap.fill(text, width=width, initial_indent=f" {color}{label}: {Style.RESET_ALL}", subsequent_indent=indent)
    print(wrapped)


def run_pipeline(word: str):
    print(Fore.LIGHTBLACK_EX + "\n" + "─" * 64)
    print(Fore.WHITE + f" 🚀 Input Word: {Fore.GREEN + Style.BRIGHT}{word.upper()}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Running LangGraph 3-node pipeline...)")
    print(Fore.LIGHTBLACK_EX + "─" * 64)

    result = app.invoke({"topic": word})

    print(Fore.LIGHTBLACK_EX + "─" * 64)
    print(Fore.GREEN + Style.BRIGHT + " ✨ FINAL PRODUCT CARD:")
    wrap_text("💡 Concept", result['topic'].capitalize(), Fore.CYAN)
    wrap_text("🔬 Tech   ", result['invention'], Fore.YELLOW)
    wrap_text("📣 Pitch  ", f"\"{result['pitch']}\"", Fore.MAGENTA)
    wrap_text("⚠️  Alert  ", result['warning'], Fore.RED)
    print(Fore.LIGHTBLACK_EX + "─" * 64)


def main():
    print_banner()
    while True:
        try:
            user_input = input(Fore.YELLOW + Style.BRIGHT + "\n👉 Enter any word (e.g. Socks, Pizza, Homework) or 'q' to quit: " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_input or user_input.lower() in ["q", "quit", "exit"]:
            print(Fore.CYAN + "\n👋 Thanks for inventing! Goodbye.\n")
            break

        run_pipeline(user_input)


if __name__ == "__main__":
    main()
