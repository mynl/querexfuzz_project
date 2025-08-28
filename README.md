# Querexfuzz

[](https://www.google.com/search?q=https://github.com/mynl/querexfuzz/actions)

A flexible and powerful query engine for pandas DataFrames. `querexfuzz` lets you filter and search your data using a clean, combined syntax that supports SQL-like queries, regular expressions, natural date ranges, and fuzzy matching.

----

NOTES: move later

* considered lazy setup: makes first call slow; Gemini thinks initial call will be quick. this approach gives consistent parse speed.

-----

## Core Features

  * **Unified Query Language**: Combine `where` clauses, `regex` searches (`~`), date filters (`@`), and fuzzy matching (`#`) in a single string.
  * **DataFrame Native**: Attaches a `.querexfuzz()` method directly to your DataFrame instances for a seamless `pandas` workflow.
  * **Highly Configurable**: Use a simple `config.yml` file to define default columns, search fields, and other behaviors for different datasets.
  * **Developer Friendly**: Built with a modern `src/` layout, Pydantic for configuration, and a `pytest` suite for robust testing.

-----

## Installation

To install the package for use in your projects:

```bash
pip install querexfuzz
```

For development, clone the repository and install it in editable mode with the testing dependencies:

```bash
git clone https://github.com/mynl/querexfuzz.git
cd querexfuzz
pip install -e .[test]
```

-----

## Quickstart

1.  **Create a `config.yml` file** in your project's root directory to configure the engine:

    ```yaml
    # config.yml
    base_cols:
      - name
      - city
      - registered_date
      - age

    date_fields:
      - registered_date

    default_date_field: registered_date
    bang_field: name
    recent_field: registered_date

    fuzzy:
      fields:
        - name
        - city
      limit: 50
      score_col_name: score
    ```

2.  **Use `querexfuzz` in your Python code**:

    ```python
    import pandas as pd
    from querexfuzz import Querexfuzz

    # Create a sample DataFrame
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'city': ['Amsterdam', 'Berlin', 'Copenhagen', 'Berlin', 'Amsterdam'],
        'registered_date': pd.to_datetime([
            '2025-08-10', '2025-06-15', '2024-01-20', '2025-08-25', '2025-07-30'
        ])
    }
    df = pd.DataFrame(data)

    # Initialize Querexfuzz with your config
    qflex = Querexfuzz(config_path='config.yml')

    # Attach the .querexfuzz() method to your DataFrame
    df = qflex.attach_to(df)

    # Run your first query!
    result = df.querexfuzz("where city == 'Berlin' and age > 35")
    print(result)
    ```

-----

## Query Syntax Examples

The `querexfuzz` language is designed to be intuitive. Clauses can be combined in almost any order.

### `where` Clause

Uses standard `pandas.DataFrame.query()` syntax for SQL-like filtering.

```python
# Find people in Amsterdam older than 30
df.querexfuzz("where city == 'Amsterdam' and age > 30")
```

### `regex` Search

Use `~` for column-specific regex and `!` for a default "bang" field (configured in `config.yml`).

```python
# Find names starting with A or B
df.querexfuzz("name ~ ^[A-B]")

# Use the default bang_field (e.g., name)
df.querexfuzz("! ice") # Matches Alice
```

### `@date` Filter

Query date ranges using natural language specifiers.

```python
# People registered in the last 3 months
# Assuming today is 2025-08-27
df.querexfuzz("@m-3")

# People registered between 6 and 28 months ago on the 'registered_date' field
df.querexfuzz("@registered_date m-28:6")

# People registered this year
df.querexfuzz("@y")
```

### `#fuzzy` Matching

Fuzzy search across one or more columns (configured in `fuzzy.fields`). This clause should always be the last part of the query.

```python
# Fuzzy find matches for "berlin"
# Results will be sorted by a 'score' column by default
df.querexfuzz("# berlin")
```

### Combining Clauses

Combine clauses to create powerful and specific queries.

```python
# Get the top 2 people registered in the last 3 months from Berlin,
# selecting only their name and age.
query = "top 2 recent where city == 'Berlin' @m-3 select name, age"
df.querexfuzz(query)
```

-----

## Development

  * **Structure**: This project uses a `src/` layout.
  * **Installation**: Run `pip install -e .[test]` to install in editable mode with test dependencies.
  * **Testing**: Run `pytest` from the project root to execute the test suite.
