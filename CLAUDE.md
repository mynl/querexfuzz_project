# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode with test dependencies
pip install -e .[test]

# Run all tests
pytest

# Run a single test file
pytest tests/test_parser.py
pytest tests/test_engine.py

# Run a single test by name
pytest tests/test_engine.py::test_function_name -v

# Run the example script
python example.py
```

No linter or formatter is configured.

## Architecture

**Querexfuzz** is a pandas DataFrame query engine that unifies SQL-like filters, regular expressions, date ranges, fuzzy matching, and sorting into a single query string syntax (e.g., `"top 10 where city == 'Berlin' @m-3 select name, age #berlin"`).

### Module roles

| Module | Role |
|---|---|
| `core.py` | `Querexfuzz` class — holds config, attaches `.querexfuzz()` to `pd.DataFrame` |
| `config.py` | Pydantic models: `QuerexfuzzConfig`, `FuzzyConfig` — validated at init time |
| `parser.py` | Lark-based transformer — converts query string → structured spec dict |
| `grammar.lark` | Lark grammar defining query syntax |
| `engine.py` | Executes spec dicts against a DataFrame: WHERE → regex → date → fuzzy → sort → top/select |
| `dates.py` | Resolves relative date syntax (`@m-3`, `@y-5:2`, etc.) to concrete date ranges |
| `logging_filters.py` | Custom logging filters |

### Data flow

```
query string
     │
     ▼
parser.py (Lark grammar → QueryTransformer)
     │  produces spec dict
     ▼
engine.py (applies clauses in order)
  1. WHERE   — pandas df.query() for SQL-like conditions
  2. REGEX   — column ~ pattern or ! pattern (bang_field default)
  3. DATE    — date range via dates.py
  4. FUZZY   — skimmatch scoring, filtered by limit threshold
  5. SORT    — order by columns (- prefix = descending)
  6. TOP/BOTTOM — head/tail N rows
  7. SELECT  — column projection (*, **, *, -col exclusions)
     │
     ▼
filtered/sorted DataFrame
```

### Configuration

Configured via YAML file or kwargs — both feed into `QuerexfuzzConfig`:

```python
qx = Querexfuzz("config.yml")           # from file
qx = Querexfuzz(base_cols=[...], ...)   # from kwargs
qx = querexfuzz_from_df(df)             # auto-detect from DataFrame
```

Key config fields: `base_cols`, `date_fields`, `default_date_field`, `bang_field` (default regex target), `recent_field`, `fuzzy` (dict → `FuzzyConfig`).

### Query syntax (clause order matters)

```
[recent] [verbose] [top N | bottom N] [select cols] [field ~ regex | ! term]
[where expr] [order by cols] [@ date_spec] [# fuzzy_term]
```

Fuzzy (`#`) must be last. Date spec format: `@[field] unit[-offset][:range]` where unit is `d/w/m/q/y`.

### Testing notes

Tests in `tests/conftest.py` build a shared fixture DataFrame and a configured `Querexfuzz` instance. Date-range tests are sensitive to the reference date embedded in the fixture — if date filter tests fail unexpectedly, check `conftest.py` for the anchor date.
