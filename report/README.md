# Reports

- `hackathon01/`: completed Hackathon 1 report, including its source files and bibliography.
- `hackathon02/`: empty original TMLR template for Hackathon 2, with the same authors and style files.

Build either report from the repository root:

```sh
latexmk -cd -pdf report/hackathon01/main.tex
latexmk -cd -pdf report/hackathon02/main.tex
```

Each command writes `main.pdf` into the corresponding report directory. LaTeX build output is ignored by Git.
