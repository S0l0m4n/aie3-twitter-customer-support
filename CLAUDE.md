# CLAUDE.md

### Introduction
You are a coding agent that will write code as I direct you to. There is a spec file that sets the scene, generated from a previous chat that I had with Claude. Read that first before continuing.

All code you suggest will be made in this Git repo. Wait for me to commit changes or to tell you to commit before proceeding onto the next task, unless we're iterating on the current code.

Follow all best practices in software development for project folder structure, preserving secrets, but don't overdo it. I need to understand all code that is written, so prefer simplicity over brevity or elegance.

Do not spawn unnecessary files. You can generate extra documentation files if you need to – I might not track these.

When I ask you a question in VS Code, I want you to directly answer it, not just suggest a code edit.

Try to keep Git diffs minimal between commits. Only change something that is working when you need to change it to support the new feature, or if the current way of doing it is dragging us down or a much better solution is available.

Never end a code file, e.g. `*.py`, with an empty line.

Do not run any script without expicit permission first. In particular, do not run any script that you just coded; let me review it first outside of our chat.

### Project-Specific Rules

**Architecture spec is the source of truth.** The ARCHITECTURE_SPEC.md file contains the full architecture spec. If something is defined there — API response shape, feature list, prompt wording, logging format — follow it exactly. Don't improvise alternatives unless I ask you to. You'll find the spec and other documents under the top-level `data` directory.

**Shared code: `features.py`.** The feature extraction function must be identical between the notebook and `backend/services/features.py`. If you change one, change the other. Never let them drift.

**Latency measurement.** Wrap every service call with `time.time()` before and after. Report in milliseconds. No libraries needed.

**Error handling.** All-or-nothing on `/query` — if any service fails, the whole request returns an error. No partial responses. Retry Groq calls once with a 2-second delay. Don't retry local services (ChromaDB, ML model).

**ChromaDB.** In-process only. Never set up a client-server connection. Use `chromadb.PersistentClient(path=...)` pointed at the data directory.

**Frontend.** Single-page React app. One `fetch` call to `POST /query`. No routing library, no state management library. Just `useState`. Functional, not pretty.

**Docker.** Two services only: `backend` and `frontend`. No third container for ChromaDB. Named volumes for `chroma_data` and `logs`.

**No overengineering.** No abstract base classes, no factory patterns, no dependency injection. Flat imports, simple functions, obvious code. I will be asked to explain every line in review.

### Code Style
- Python: type hints on function signatures, but don't overdo it on local variables.
- Use `async` for FastAPI route handlers. Services that call the LLM should be async. ML model and ChromaDB calls can be sync.
- Frontend: functional components only, no class components.
- Comments only where the *why* isn't obvious. Don't comment what the code does.
