# Project guidance

- Consult `docs/adrs/` before changing design decisions.
- Keep changes focused, writing concise, and research claims sourced.
- Use Python 3.11+ and `uv` for Python work.
- Keep the structure of `tests/` aligned with the project structure, mirroring the source paths for corresponding tests.
- If a new package is needed, pause work before changing dependencies or installing it. Tell the developer the exact `uv add <package>` command, listing only direct packages the task actually needs, not their transitive dependencies. The developer must run it manually in the terminal; resume only after the developer confirms the package was added and explicitly gives the go-ahead.
- Use the [official FrameX documentation](https://unisg-ics-dsnlp.github.io/FrameX-Doc/index.html) as the source of truth for FrameX syntax, APIs, and behavior. For `.fx` files, use the team-installed `framex` CLI (verified with version 0.4.3); see `docs/FRAME_X_LOCAL.md` for commands and setup. For Python client code that needs the hosted Workbench, read `docs/FRAME_X_WORKBENCH.md` and use `uv run python scripts/framex_workbench.py` with credentials from `.env`. Do not install PyPI `framex`; it is an unrelated package. Never output Workbench credentials.
