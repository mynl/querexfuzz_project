# Changelog

Notable changes to querexfuzz. Keep a Changelog form; versions follow `project.version` in
`pyproject.toml`. History before 2.0.5 is not reconstructed.

## [2.0.5] - 2026-08-31

### Changed

- Migrated to DOOB: test tooling moved from the `test` extra to `[dependency-groups] dev`
  (`uv sync` installs it); the `docs` extra stays for Read the Docs.
- Author and license metadata added (`LICENSE` file, PEP 639 fields); `uv.lock` refreshed.
- Notebook checkpoints, JupyterLab virtual documents, and the local Claude settings file
  untracked; `.gitignore` brought to the house standard and no longer ignores `CLAUDE.md`.
- README development instructions corrected (repository name, `uv` workflow).

### Added

- `CLAUDE.md` (rewritten in the house shape), `CHANGELOG.md`, and
  `dev/plan-2.0.5-doob-migration.md`.
