import logging
import re
import pandas as pd
from .config import QuerexfuzzConfig
from .dates import resolve_date_range


logger = logging.getLogger(__name__)
logger.info('engine setup')


def _mock_fuzzy_search(series: pd.Series, query: str, limit: int) -> tuple[pd.Index, list[float]]:
    """A placeholder for your Rust-based fuzzy matcher."""
    # This mock finds case-insensitive substrings and scores by length.
    if query is None or not query.strip():
        return series.index, [1.0] * len(series)

    matches = series.astype(str).str.contains(query, case=False, na=False)
    matched_series = series[matches].head(limit)

    # Simple score: ratio of query length to target length
    scores = [len(query) / len(s) if s else 0 for s in matched_series]

    return matched_series.index, scores


def execute_query(df: pd.DataFrame, spec: dict, config: QuerexfuzzConfig) -> pd.DataFrame:
    """Applies the parsed query specification to a DataFrame."""
    df = df.copy()

    # 1. Filter: WHERE clause (SQL-like)
    if spec['where']:
        df = df.query(spec['where'])

    # 2. Filter: Regex clauses
    for field, pattern in spec['regex']:
        col = config.bang_field if field == 'BANG' else field
        if col and col in df.columns:
            try:
                df = df.loc[df[col].astype(str).str.contains(pattern, regex=True, case=False, na=False)]
            except re.error:
                print(f"Warning: Regex error with pattern '{pattern}'. Ignoring.")
        else:
            raise ValueError(f"Invalid column for regex search: '{col}'")

    # 3. Filter: Date clauses
    for date_filter in spec['dates']:
        col = date_filter['field'] or config.default_date_field
        if not col or col not in df.columns:
            raise ValueError(f"Invalid column for date search: '{col}'")
        df[col] = pd.to_datetime(df[col], errors='coerce')
        start_date, end_date = resolve_date_range(date_filter)
        df = df.loc[df[col].between(start_date, end_date)]

    # 4. Fuzzy Search
    has_fuzzy_results = False
    if spec['fuzzy']:
        fuzzy_conf = config.fuzzy
        if fuzzy_conf.fields == 'all':
            search_cols = df.select_dtypes(include='object').columns.tolist()
        else:
            search_cols = [c for c in fuzzy_conf.fields if c in df.columns]

        if not search_cols:
            raise ValueError("No valid columns found for fuzzy search.")

        search_series = df[search_cols].apply(lambda row: ' '.join(row.astype(str)), axis=1)

        limit = spec['top'] if spec['top'] > 0 else fuzzy_conf.limit
        indices, scores = _mock_fuzzy_search(search_series, spec['fuzzy'], limit)

        df = df.loc[indices].copy()
        df[fuzzy_conf.score_col_name] = scores
        has_fuzzy_results = True

    # 5. Sort
    sort_cols = [col for col, asc in spec['sort']]
    sort_order = [asc for col, asc in spec['sort']]

    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=sort_order)
    elif has_fuzzy_results:
        df = df.sort_values(by=config.fuzzy.score_col_name, ascending=False)
    elif 'recent' in spec['flags'] and config.recent_field:
        df = df.sort_values(by=config.recent_field, ascending=False)

    # 6. Limit (Top N)
    if spec['top'] > 0:
        df = df.head(spec['top'])

    # 7. Select Columns
    sel = spec['select']
    if sel['include'] or sel['exclude']:
        if sel['include'] == ['*']:
            fields = list(df.columns)
        else:
            fields = config.base_cols + [c for c in sel['include'] if c not in config.base_cols]

        final_fields = [f for f in fields if f not in sel['exclude'] and f in df.columns]
        df = df[final_fields]
    elif config.base_cols:
        final_fields = [f for f in config.base_cols if f in df.columns]
        df = df[final_fields]

    return df
