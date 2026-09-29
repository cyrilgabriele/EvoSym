# Local FrameX CLI

The team runs `.fx` programs with the FrameX CLI installed on each member's machine. Version 0.4.3 is verified on the development machine. The CLI is an external executable, not a Python dependency; do not add the unrelated PyPI `framex` package.

From the project root:

```sh
command -v framex
framex --version
framex --help
framex check path/to/program.fx
framex run path/to/program.fx
framex test path/to/program.fx
```

Use the [official FrameX documentation](https://unisg-ics-dsnlp.github.io/FrameX-Doc/index.html) for language syntax and behavior. `framex --help` lists the commands supported by the installed version.

## Install or repair the CLI

Get the course-provided [FrameX CLI release](https://github.com/unisg-ics-dsnlp/FrameX-CLI/releases), extract it, and follow its `INSTALL.md` for your operating system. Select the binary for your CPU architecture and verify the release checksums with the included `SHA256SUMS`. On Apple Silicon, the 0.4.3 archive names the binary `framex-0.4.3-aarch64-apple-darwin`; its install instructions copy it to `/usr/local/bin/framex`.

If macOS says Apple cannot verify `framex`, check which copy your shell finds with `command -v framex`. A downloaded copy may still carry a quarantine attribute even when a separately installed copy works. Follow the release's `INSTALL.md` instructions for the installed binary, then open a new terminal and rerun `framex --version`. Avoid placing the extracted release folder ahead of the installed binary on `PATH`.

The CLI runs `.fx` files. Python code using the FrameX client needs a separate Python framework or the [hosted Workbench](FRAME_X_WORKBENCH.md); the local CLI alone does not make `import framex` available.
