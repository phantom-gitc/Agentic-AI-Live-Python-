# Claude Code Agent

A terminal coding agent that uses an AI model plus guarded local tools to inspect, edit, and run a project from natural-language tasks.

## Setup

```bash
cd claude_code
copy .env.example .env
```

Add your API keys to `.env`.

If you are using the repository virtual environment on Windows:

```bash
..\venv\Scripts\python.exe main.py --help
```

Or install the app dependencies into your active Python:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py "Analyze this project"
python main.py "Create a FastAPI hello-world app"
python main.py --verbose "Run the tests and fix failures"
```

Interactive mode:

```bash
python main.py
```

The default provider is `hybrid`. In hybrid mode, the app uses OpenAI as the main model and Gemini as the reviewer. If `OPENAI_API_KEY` is blank but `GROQ_API_KEY` exists, it uses Groq as the main model and Gemini as the reviewer.

Use OpenAI + Gemini together:

```bash
AI_PROVIDER=hybrid
AI_MODEL=
FALLBACK_MODEL=openai/gpt-oss-20b
GEMINI_MODEL=
MAX_OUTPUT_TOKENS=3000
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
```

Use Groq + Gemini together:

```bash
AI_PROVIDER=hybrid
AI_MODEL=
FALLBACK_MODEL=openai/gpt-oss-20b
GEMINI_MODEL=
MAX_OUTPUT_TOKENS=3000
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```

Use Groq:

```bash
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_key
```

Use Gemini:

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
```

Use OpenAI:

```bash
AI_PROVIDER=openai
AI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=your_openai_key
```

## Folder Structure

```text
claude_code/
|-- CLAUDE.md
|-- README.md
|-- main.py
|-- requirements.txt
|-- claude_code_agent/
|   |-- agent.py
|   |-- cli.py
|   |-- config.py
|   |-- ai/
|   |-- prompts/
|   `-- tools/
```

Prompting examples live in `claude_code_agent/prompts/examples.md`.
