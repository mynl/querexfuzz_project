# Plan 2.0.5: migrate querexfuzz to DOOB

Per-project record for the tree-level plan `V:\dev\dev\plan-doob-migration.md`, which holds the
goal, the 19-step checklist, and the decisions. This file records what was found and done here.

## Found (2026-08-31)

- Tree clean; local one commit ahead of `mynl/querexfuzz_project` (`master`), unpushed. Every
  file, including `.git/`, carried the Windows read-only attribute from the snapshot copy;
  cleared with `attrib -R /S /D`.
- `.gitignore` ignored `CLAUDE.md` and `.claude/`, so the existing `CLAUDE.md` was untracked —
  contrary to the tree-level survey. Meanwhile `.claude/settings.local.json`,
  `.ipynb_checkpoints/` and `.virtual_documents/` were tracked.
- No author, no license field, no `LICENSE` file. `test` extra held pytest. `uv.lock` was stale.
- No old-machine paths (the only hits were inside a tracked notebook checkpoint's traceback).
- README pointed at a wrong clone URL (`mynl/querexfuzz`) and a `pip install -e .[test]` flow.

## Done

- [git] `.ipynb_checkpoints/`, `.virtual_documents/`, `.claude/settings.local.json` untracked
  (left on disk, now ignored); `*.sublime-*` removed; `.gitignore` replaced with the house
  standard plus `docs/build/` (Sphinx output here) and `.claude/settings.local.json`.
- [paths] Nothing to fix.
- [pyproject] Author `Stephen J. Mildenhall <steve@mynl.com>`; `license = "MIT"` with a new
  `LICENSE` file (MIT, matching the sibling packages — confirm if another license was intended);
  version 2.0.5; pytest in `[dependency-groups] dev`; `docs` extra kept for Read the Docs;
  `[tool.pytest.ini_options] testpaths` added. Build backend stays setuptools.
- [env + build] `uv lock` refreshed, `uv sync`, `uv run pytest` green, `uv build` clean.
- [docs] `CLAUDE.md` rewritten in the house shape (architecture table and query-syntax notes
  carried over), `CHANGELOG.md`, this plan. README dev section corrected.
- [close] Bumped 2.0.4 → 2.0.5, one commit.

## Open

- Publishing 2.0.5 (step 19) is Steve's call; PyPI has 2.0.4.
- `config.yaml` and `logconfig.yaml` at the repo root are examples nobody reads; either move
  them under `docs/` or reference them from the README.
- The example notebooks exist only as JupyterLab virtual copies under `.virtual_documents/`
  (now ignored); if they are wanted, promote them to real files.
