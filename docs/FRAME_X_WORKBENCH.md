# FrameX Workbench from this repo

The team uses the [local FrameX CLI](FRAME_X_LOCAL.md) for `.fx` files. Use this hosted Workbench workflow for Python code that needs the [FrameX Python client](https://unisg-ics-dsnlp.github.io/FrameX-Doc/python/client.html), or when a program specifically needs the course Workbench. Do not install the unrelated PyPI `framex` dataset package for this project.

`scripts/framex_workbench.py` uses only Python's standard library to authenticate to the course Workbench and run `.fx` or `.py` files there. It reads `FRAME_X_WORKBENCH_USERNAME` and `FRAME_X_WORKBENCH_PASSWORD` from the root `.env`. Never commit `.env` or print its values. The script uses the Workbench web app's API, which is not a documented public API and may change.

Set the course credentials in the root `.env`:

```dotenv
FRAME_X_WORKBENCH_USERNAME=your_username
FRAME_X_WORKBENCH_PASSWORD=your_password
```

```sh
uv run python scripts/framex_workbench.py status
uv run python scripts/framex_workbench.py files
uv run python scripts/framex_workbench.py run codex-smoke-test.fx
uv run python scripts/framex_workbench.py run codex-python-smoke-test.py
uv run python scripts/framex_workbench.py upload-run path/to/program.fx
uv run python scripts/framex_workbench.py upload-run path/to/program.py
```

`upload-run` saves a local program in the Workbench as `codex-<name>-<content-hash>.<ext>`, then runs it. Identical content reuses the same remote file; changed content gets a new file. It does not overwrite existing Workbench files. The Workbench workspace must be running before `run` or `upload-run`; start it in the web UI if `status` says otherwise.

Verified on 2026-09-29: `codex-smoke-test.fx` returned `true` with one passed expectation, and `codex-python-smoke-test.py` printed `{'status': 'true'}`. Both files are in the Workbench account, separate from this repo.
