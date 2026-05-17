# Querexfuzz

A flexible query engine for pandas DataFrames. `querexfuzz` lets you filter and search your data using a unified syntax that combines SQL-like `where` clauses, regular expressions, natural date ranges, and fuzzy matching — all in a single query string.

---

## Core Features

- **Unified query language**: combine `where`, regex (`~` / `!`), date filters (`@`), and fuzzy matching (`#`) in one string.
- **DataFrame native**: attaches a `.querex()` method (and `.q()` alias) directly to DataFrame instances.
- **Auto-configuration**: `querexfuzz_from_df` inspects column types and sets sensible defaults automatically.
- **Fast fuzzy search**: powered by [skimmatch](https://github.com/mynl/skimmatch); matcher built once per DataFrame and cached for the lifetime of the engine.
- **Configurable**: via YAML file, keyword arguments, or both.

---

## Installation

```bash
pip install querexfuzz
```

For development:

```bash
git clone https://github.com/mynl/querexfuzz.git
cd querexfuzz
pip install -e .[test]
```

---

## Quickstart

### Auto-configure from a DataFrame

The simplest path — `querexfuzz_from_df` inspects column types and wires everything up:

```python
import pandas as pd
from querexfuzz import querexfuzz_from_df

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 40, 45],
    'city': ['Amsterdam', 'Berlin', 'Copenhagen', 'Berlin', 'Amsterdam'],
    'registered_date': pd.to_datetime([
        '2025-08-10', '2025-06-15', '2024-01-20', '2025-08-25', '2025-07-30'
    ])
})

querexfuzz_from_df(df)        # attaches .querex() and .q() to df in-place

result = df.querex("where city == 'Berlin'")
result = df.q("top 5 # ams")  # short alias
```

### Explicit configuration

```python
from querexfuzz import Querexfuzz

engine = Querexfuzz(
    base_cols=['name', 'city', 'registered_date', 'age'],
    date_fields=['registered_date'],
    default_date_field='registered_date',
    bang_field='name',
    recent_field='registered_date',
    fuzzy=dict(fields=['name', 'city'], limit=50, score_col_name='score'),
)
engine.attach_to(df)

result = df.querex("recent top 10 where age > 30 # berlin")
```

### From a YAML config file

```python
engine = Querexfuzz(config_path='config.yml')
engine = Querexfuzz(config_path='config.yml', fuzzy={'limit': 200})  # with overrides
```

---

## Query Syntax

Clauses are **order-sensitive** and must appear in this sequence (all optional):

```
[verbose] [recent] [top N | bottom N] [select cols]
[field ~ regex | ! term] [where expr] [order by cols] [@ date_spec] [# fuzzy_term]
```

An empty query returns all base columns for all rows.

### `where` — SQL-like filter

```python
df.querex("where city == 'Amsterdam' and age > 30")
```

### `!` / `~` — Regex

```python
df.querex("! ^[AB]")            # regex on bang_field (default regex target)
df.querex("name ~ ^[AB]")       # regex on named column
```

### `@` — Date range

Units: `c` calendar year, `y` year, `q` quarter, `m` month, `w` week, `d` day, `h` hour.

```python
df.querex("@m-3")                        # last 3 months (default date field)
df.querex("@registered_date m-28:6")     # 28 to 6 months ago on named field
df.querex("@y-1")                        # last year
```

### `#` — Fuzzy matching

Must be the **last** clause. Results are sorted by score descending.

```python
df.querex("# berlin")
df.querex("where age > 30 # ams")        # filter first, then fuzzy over full data
```

### `select` — Column projection

| Syntax | Meaning |
|---|---|
| *(default)* | base columns |
| `select *` | base columns |
| `select **` | all columns |
| `select a, b` | named columns |
| `select *, a` | base columns plus `a` |
| `select *, -a` | base columns minus `a` (`-` or `!` prefix) |
| `select **, -a` | all columns minus `a` |

### `top` / `bottom` / `recent` / `order by`

```python
df.querex("top 10")
df.querex("bottom 5")
df.querex("recent")                       # sort by recent_field descending
df.querex("order by age")
df.querex("order by -age, name")          # - prefix = descending
```

### Combining clauses

```python
df.querex("top 5 recent where city == 'Berlin' @m-3 select name, age # bob")
```

---

## Fuzzy matching and caching

The fuzzy matcher (skimmatch) is built **once** per attached DataFrame and cached on the engine. Repeat fuzzy queries against the same DataFrame pay only the cost of `matcher.query()`.

When `where`, regex, or date pre-filters are present, the matcher still runs over the full DataFrame and results are intersected with the pre-filtered rows (5× over-fetch to compensate for the narrower valid set).

If the DataFrame's contents change between queries, re-attach with `mutable=True`:

```python
engine.attach_to(df, mutable=True)   # rebuilds matcher on every fuzzy call
```

---

## Versions

### 2.0.3 (current)
Fuzzy caching refactor. Matcher built once per attached DataFrame and cached by `id(df)` on the engine — repeat queries skip all data preparation. Multiple DataFrames per engine each get an independent cache entry. `attach_to(mutable=True)` opt-in for DataFrames whose contents change.

### 2.0.2
Performance pass on `execute_query`: lazy DataFrame copy (copy only when date-column type coercion is needed, after prior filters have already reduced the frame); initial fuzzy matcher caching.

### 2.0.1
Code review fixes: method renamed `.querex()` / `.q()`; `importlib.metadata` version; Pydantic config corrections; parser and test suite overhaul; `tzlocal` dependency added.

### 2.0.0
Major rewrite. Lark-based grammar parser, Pydantic configuration, `skimmatch` fuzzy backend (replacing `rustfuzz`), `src/` layout.

### 0.1.0
Initial release.
