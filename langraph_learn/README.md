# 🧪 The Crazy Invention Factory (Simple LangGraph Demo)

A super simple, crazy 3-step LangGraph pipeline.

You enter any normal everyday object (e.g. *Coffee*, *Socks*, *Pizza*):
1. **Node 1: Mad Scientist** turns it into an absurd sci-fi invention.
2. **Node 2: TV Salesman** writes a high-energy TV infomercial pitch.
3. **Node 3: Safety Inspector** adds a ridiculous legal warning label.

---

## 🚀 How to Run

In PowerShell:

```powershell
cd "d:\Agentic - AI\langraph_learn"
python main.py
```

Then type any word (or press Enter for default `Socks`)!

---

## 🧠 LangGraph in 4 Simple Steps (Under 90 Lines of Code!)

1. **State**: Define a dictionary of fields that pass through the pipeline:
   ```python
   class IdeaState(TypedDict):
       topic: str
       invention: str
       sales_pitch: str
       warning_label: str
   ```

2. **Nodes**: Functions that receive the state and return updates:
   ```python
   def mad_scientist_node(state): ...
   def salesman_node(state): ...
   def warning_node(state): ...
   ```

3. **Graph Builder**: Connect nodes with edges:
   ```python
   builder = StateGraph(IdeaState)
   builder.add_node("scientist", mad_scientist_node)
   builder.add_node("salesman", salesman_node)
   builder.add_node("warning", warning_node)

   builder.add_edge(START, "scientist")
   builder.add_edge("scientist", "salesman")
   builder.add_edge("salesman", "warning")
   builder.add_edge("warning", END)
   ```

4. **Run**:
   ```python
   app = builder.compile()
   output = app.invoke({"topic": "Pizza"})
   ```
