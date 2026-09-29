# Project guidance

- Consult `docs/adrs/` before changing design decisions.
- Keep changes focused, writing concise, and research claims sourced.
- Use Python 3.11+ and `uv` for Python work.
- Keep the structure of `tests/` aligned with the project structure, mirroring the source paths for corresponding tests.
- If a new package is needed, pause work before changing dependencies or installing it. Tell the developer the exact `uv add <package>` command, listing only direct packages the task actually needs, not their transitive dependencies. The developer must run it manually in the terminal; resume only after the developer confirms the package was added and explicitly gives the go-ahead.
- For FrameX execution, read `docs/FRAME_X_WORKBENCH.md` first. Use `uv run python scripts/framex_workbench.py` to run `.fx` or `.py` code in the hosted Workbench with credentials from `.env`. Do not install PyPI `framex`; it is an unrelated package. Never output Workbench credentials.
