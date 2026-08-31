# querexfuzz

Adds to `V:\dev\CLAUDE.md` (house rules). Project detail only — see **Deltas** at the foot.

A query engine for pandas DataFrames that unifies SQL-like `where` clauses, regular expressions,
relative date ranges, fuzzy matching, sorting, and projection into one query string, e.g.
`"top 10 where city == 'Berlin' @m-3 select name, age #berlin"`. It attaches `.querex()` (alias
`.q()`) to DataFrames. Fuzzy matching is delegated to `skimmatch`. Published to PyPI as
`querexfuzz`; documented on Read the Docs (`querexfuzz-project`); consumed by archivum via PyPI.

## Commands

```
uv sync                       # venv + lock (dev group: pytest)
uv run pytest                 # all tests; tests/test_grammar.py is the big one (~54 tests)
uv run pytest tests/test_engine.py::test_name -v
uv build                      # wheel + sdist into dist/
uv sync --extra docs && uv run sphinx-build -b html docs/source docs/build/html
```

No linter or formatter is configured.

## Publishing

Steve publishes; Claude prepares. Once per machine, create a PyPI API token and store it as
`UV_PUBLISH_TOKEN` in the user environment (never in the repo). Per release: bump `version` in
`pyproject.toml`, add the CHANGELOG entry, commit, then `uv build` and `uv publish`. Read the
Docs rebuilds from GitHub on push; it installs `.[docs]` per `.readthedocs.yaml`.

## Architecture

| Module | Role |
|---|---|
| `core.py` | `Querexfuzz` — holds config, attaches `.querex()` / `.q()` to `pd.DataFrame`; `querexfuzz_from_df` auto-configures from column types |
| `config.py` | Pydantic models `QuerexfuzzConfig`, `FuzzyConfig`, validated at init |
| `parser.py` + `grammar.lark` | Lark grammar and transformer: query string → spec dict |
| `engine.py` | Applies the spec in fixed order: WHERE → regex → date → fuzzy → sort → top/bottom → select |
| `dates.py` | Relative date syntax (`@m-3`, `@y-5:2`) → concrete ranges |
| `logging_filters.py` | Filters that isolate or exclude parser debug output |

Query clause order matters and fuzzy (`#`) must be last:

```
[recent] [verbose] [top N | bottom N] [select cols] [field ~ regex | ! term]
[where expr] [order by cols] [@ date_spec] [# fuzzy_term]
```

Date spec: `@[field] unit[-offset][:range]`, unit in `d/w/m/q/y`. Configuration comes from a
YAML file or kwargs, both feeding `QuerexfuzzConfig`; key fields are `base_cols`, `date_fields`,
`default_date_field`, `bang_field`, `recent_field`, `fuzzy`. `config.yaml` and `logconfig.yaml`
at the repo root are examples, not read by the package.

Tests share fixtures from `tests/conftest.py`; fixture dates are relative to `pd.Timestamp.now()`
so date tests stay valid over time.

## Deltas from house rules

- **Build backend is setuptools**, not hatchling: the package is published and builds today;
  switching is churn with no visible gain (decided 2026-08-31).
- **A `docs` extra is kept** alongside the `dev` dependency group because Read the Docs installs
  extras, not groups.
- Version lives in `pyproject.toml` only; `__version__` reads it via `importlib.metadata`.
