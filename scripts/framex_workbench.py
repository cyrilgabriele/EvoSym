"""Run FrameX programs in the course Workbench without local FrameX packages."""

from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://framex.nlp-lab.ai"


def read_credentials(path: Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return (
        values["FRAME_X_WORKBENCH_USERNAME"],
        values["FRAME_X_WORKBENCH_PASSWORD"],
    )


class Workbench:
    def __init__(self) -> None:
        self.csrf = ""
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(self, path: str, method: str = "GET", payload: dict | None = None) -> dict:
        headers = {
            "Accept": "application/json",
            "Origin": BASE_URL,
            "Referer": BASE_URL + "/",
            "User-Agent": "Mozilla/5.0",
        }
        body = None
        if method != "GET":
            headers["Content-Type"] = "application/json"
            headers["X-Studio-CSRF"] = self.csrf
            body = json.dumps(payload or {}).encode()
        request = urllib.request.Request(
            BASE_URL + path, data=body, headers=headers, method=method
        )
        with self.opener.open(request, timeout=30) as response:
            return json.load(response)

    def login(self, env_file: Path) -> None:
        username, password = read_credentials(env_file)
        result = self.request(
            "/api/login", "POST", {"username": username, "password": password}
        )
        self.csrf = result["csrf"]

    def run(self, remote_path: str) -> int:
        suffix = Path(remote_path).suffix
        if suffix not in {".fx", ".py"}:
            raise ValueError("Only .fx and .py files can be run")
        action = "run" if suffix == ".fx" else "python"
        run_id = self.request(
            "/api/runs", "POST", {"action": action, "files": [remote_path]}
        )["id"]
        for _ in range(60):
            run = self.request("/api/runs/" + run_id)
            if run.get("status") != "running":
                result = run.get("result") or {}
                print(f"Run: {run.get('status')} (exit {result.get('exit_code')})")
                if result.get("stdout"):
                    print(result["stdout"], end="" if result["stdout"].endswith("\n") else "\n")
                if result.get("stderr"):
                    print(result["stderr"], file=sys.stderr)
                return 0 if run.get("status") == "completed" and result.get("exit_code") == 0 else 1
            time.sleep(1)
        print(f"Run still active after 60 seconds: {run_id}", file=sys.stderr)
        return 1


def upload(workbench: Workbench, local_path: Path) -> str:
    if local_path.suffix not in {".fx", ".py"}:
        raise ValueError("Local program must have a .fx or .py extension")
    content = local_path.read_text()
    stem = re.sub(r"[^A-Za-z0-9_-]", "-", local_path.stem)[:48]
    digest = hashlib.sha256(content.encode()).hexdigest()[:12]
    remote_path = f"codex-{stem}-{digest}{local_path.suffix}"
    files = workbench.request("/api/files")["files"]
    if any(item["path"] == remote_path for item in files):
        saved = workbench.request("/api/file?path=" + urllib.parse.quote(remote_path))
        if saved["content"] != content:
            raise ValueError(f"Remote file differs: {remote_path}")
    else:
        workbench.request(
            "/api/files/manage",
            "POST",
            {
                "operation": "create",
                "kind": "file",
                "path": remote_path,
                "destination": remote_path,
                "content": content,
            },
        )
    return remote_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show workspace state")
    commands.add_parser("files", help="List Workbench files")
    run_command = commands.add_parser("run", help="Run an existing Workbench file")
    run_command.add_argument("remote_path")
    upload_command = commands.add_parser(
        "upload-run", help="Upload a local file under a content-based name and run it"
    )
    upload_command.add_argument("local_path", type=Path)
    args = parser.parse_args()

    try:
        workbench = Workbench()
        workbench.login(args.env_file)
        if args.command == "status":
            print(workbench.request("/api/workspace")["state"])
            return 0
        if args.command == "files":
            for entry in workbench.request("/api/files")["files"]:
                print(entry["path"])
            return 0
        if args.command == "upload-run":
            args.remote_path = upload(workbench, args.local_path)
            print(f"Workbench file: {args.remote_path}")
        return workbench.run(args.remote_path)
    except (OSError, KeyError, ValueError, urllib.error.URLError) as error:
        print(f"FrameX Workbench error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
