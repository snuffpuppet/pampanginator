# Ollama (Local LLM) Setup

Run Kapilator completely offline with no API costs.

## Installation (macOS)

```bash
# Install via Homebrew
brew install ollama

# Pull a model (choose one):
ollama pull llama3.2       # 2 GB  — fast, good for basic queries
ollama pull gemma2:9b      # 5 GB  — better multilingual, follows instructions well
ollama pull phi4           # 9 GB  — best instruction-following of the small models

# Start the server (it runs automatically after install, or start it manually):
ollama serve
```

The server listens on `http://localhost:11434` by default.

## Configure Kapilator

Copy `.env.example` to `.env` and set:

```env
BACKEND=ollama
OLLAMA_MODEL=llama3.2      # match the model you pulled above
OLLAMA_URL=http://localhost:11434
```

Restart `npm run dev` after editing `.env`.

## Use both backends

To use both Claude and Ollama (for the Compare page), set your default backend in `.env` and make sure Ollama is running. The Compare page always calls both `/api/chat/anthropic` and `/api/chat/ollama` simultaneously regardless of the `BACKEND` setting.

```env
BACKEND=anthropic          # default for the main chat / translate / grammar pages
ANTHROPIC_API_KEY=sk-...
OLLAMA_MODEL=llama3.2
```

## Choosing a model

| Model | Size | Best for |
|-------|------|----------|
| `llama3.2` | 2 GB | Fast replies, everyday phrases |
| `gemma2:9b` | 5 GB | Better at following complex prompts |
| `phi4` | 9 GB | Strongest instruction-following in this size class |
| `mistral` | 4 GB | Good general alternative |

## Quality expectations

Local models are weaker than Claude for Kapampangan specifically because:
- Kapampangan is a low-resource language — limited training data
- Smaller models follow complex system prompts (Ading's persona) less reliably
- Verb focus / aspect explanations benefit most from Claude's reasoning depth

**Practical recommendation:**
- Use Ollama for vocabulary lookups, greetings, simple phrases
- Use Claude (API or claude.ai project) for grammar questions and error correction
- Use the **Compare** page to see the difference yourself

## Verify Ollama is running

```bash
curl http://localhost:11434/v1/models
# Should return a JSON list of your downloaded models
```
