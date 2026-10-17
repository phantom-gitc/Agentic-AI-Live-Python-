import os
import sys

# Ensure UTF-8 output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import TypedDict
from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, START, END

# 1. Setup Gemini Client from .env
load_dotenv()
api_key = os.getenv("GEMINI_API") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def ask_gemini(prompt: str) -> str:
    """Simple helper to call Gemini"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={"automatic_function_calling": {"disable": True}}
    )
    return response.text.strip()


# 2. Define the State (The shared dictionary that moves through each step)
class IdeaState(TypedDict):
    topic: str
    invention: str
    sales_pitch: str
    warning_label: str


# 3. Define the 3 Crazy Nodes
def mad_scientist_node(state: IdeaState) -> dict:
    """Step 1: Turn any ordinary topic into a crazy sci-fi invention"""
    prompt = f"Invent a crazy, absurd, sci-fi invention based on: '{state['topic']}'. Keep it to 2 short sentences."
    result = ask_gemini(prompt)
    print("\n[Node 1: Mad Scientist] Invented:")
    print(f" -> {result}")
    return {"invention": result}


def salesman_node(state: IdeaState) -> dict:
    """Step 2: A greedy TV salesman creates an infomercial pitch for it"""
    prompt = f"Write a funny, loud 2-sentence TV infomercial pitch selling this invention: '{state['invention']}'."
    result = ask_gemini(prompt)
    print("\n[Node 2: TV Salesman] Pitch:")
    print(f" -> {result}")
    return {"sales_pitch": result}


def warning_node(state: IdeaState) -> dict:
    """Step 3: Add a hilarious ridiculous safety warning label"""
    prompt = f"Write a funny 1-sentence legal/safety warning label for: '{state['invention']}'."
    result = ask_gemini(prompt)
    print("\n[Node 3: Safety Inspector] Warning Label:")
    print(f" -> {result}")
    return {"warning_label": result}


# 4. Build the LangGraph
# Flow: START -> scientist -> salesman -> warning -> END
builder = StateGraph(IdeaState)

# Add nodes
builder.add_node("scientist", mad_scientist_node)
builder.add_node("salesman", salesman_node)
builder.add_node("warning", warning_node)

# Connect nodes with edges
builder.add_edge(START, "scientist")
builder.add_edge("scientist", "salesman")
builder.add_edge("salesman", "warning")
builder.add_edge("warning", END)

# Compile into a runnable LangGraph application
app = builder.compile()


# 5. Run it!
if __name__ == "__main__":
    print("=" * 60)
    print("       THE CRAZY INVENTION FACTORY (LangGraph)")
    print("=" * 60)
    
    # Enter any normal thing: pizza, shoes, coffee, cat...
    topic = input("\nEnter any simple word (e.g. Coffee, Shoes, Pizza): ").strip()
    if not topic:
        topic = "Socks"

    print(f"\n[+] Running LangGraph for: '{topic}' ...")
    
    # app.invoke passes the input through the graph
    final_output = app.invoke({"topic": topic})

    print("\n" + "=" * 60)
    print("  ALL DONE! Final State stored in LangGraph:")
    print("=" * 60)
    print(f"Topic:     {final_output['topic']}")
    print(f"Invention: {final_output['invention']}")
    print(f"Pitch:     {final_output['sales_pitch']}")
    print(f"Warning:   {final_output['warning_label']}")
    print("=" * 60)
