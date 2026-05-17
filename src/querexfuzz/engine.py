import logging
import re
from typing import List, Tuple, Set
import warnings

import pandas as pd

from skimmatch import FuzzyMatcherMulti, FuzzyMatcherMultiHi

from .config import QuerexfuzzConfig
from .dates import resolve_date_range


logger = logging.getLogger(__name__)
logger.info('engine setup')


class QuerexfuzzConfigurationWarning(UserWarning):
    """Warning raised when Querexfuzz configuration is unusual or suboptimal."""
    pass


# helpers
def highlight(txt: str, indices: List[int]) -> str:
    """Highlight txt at specified indices with HTML <mark> tags."""
    if not indices:
        return txt

    highlight_set: Set[int] = set(indices)

    raw_html = "".join(
        f"<mark>{char}</mark>" if i in highlight_set else char
        for i, char in enumerate(txt)
    )

    return raw_html.replace('</mark><mark>', '')


def decorate(
    df: pd.DataFrame,
    idx: List[int],
    scores: List[int],
    highlights: List[List[int]],
    col: str,
    score_col: str
) -> pd.DataFrame:
    """
    Filters a DataFrame based on search results and adds score and highlight columns.

    Args:
        df: The original DataFrame.
        idx: A list of integer indices for the matched rows.
        scores: A list of scores for each match.
        highlights: A list of lists, containing character indices to highlight.
        col: The name of the column in the DataFrame to apply highlighting to.

    Returns:
        A new DataFrame containing only the matched rows, with a 'score' column
        and an updated column with HTML highlights.
    """
    decorated_df = df.iloc[idx].copy()
    decorated_df[score_col] = scores

    highlighted_col = [
        highlight(text, hl_indices)
        for text, hl_indices in zip(decorated_df[col], highlights)
    ]
    decorated_df[col] = highlighted_col

    return decorated_df


# main class
def execute_query(
    df: pd.DataFrame,
    spec: dict,
    config: QuerexfuzzConfig,
    matcher_cache: dict | None = None,
) -> pd.DataFrame:
    """Apply the parsed query specification to a DataFrame.

    Filter operations (WHERE, regex, date range, sort, head/tail, column select)
    all return new DataFrames, so no upfront copy is needed.  The only in-place
    write is date-column type coercion; a copy is made there, after prior filters
    have already reduced the DataFrame.
    """
    # 1. Filter: WHERE clause (SQL-like)
    if spec['where']:
        df = df.query(spec['where'])

    # 2. Filter: Regex clauses
    for field, pattern in spec['regex']:
        col = config.bang_field if field == 'BANG' else field
        if col and col in df.columns:
            try:
                df = df.loc[df[col].astype(str).str.contains(
                    pattern, regex=True, case=False, na=False)]
            except re.error:
                logger.warning("Regex error with pattern '%s' — ignoring.", pattern)
        else:
            raise ValueError(f"Invalid column for regex search: '{col}'")

    # 3. Filter: Date clauses
    for date_filter in spec['dates']:
        col = date_filter['field'] or config.default_date_field
        if not col or col not in df.columns:
            warnings.warn('No valid field for date spec - ignoring.',
                         QuerexfuzzConfigurationWarning)
        else:
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                df = df.copy()  # copy only when in-place type coercion is needed
                df[col] = pd.to_datetime(df[col], errors='coerce')
            start_date, end_date = resolve_date_range(date_filter)
            if df[col].dt.tz is None:
                start_date = start_date.replace(tzinfo=None)
                end_date = end_date.replace(tzinfo=None)
            df = df.loc[df[col].between(start_date, end_date)]

    # 4. Fuzzy Search
    has_fuzzy_results = False
    if spec['fuzzy']:
        fuzzy_conf = config.fuzzy
        if fuzzy_conf.fields == 'all':
            search_cols = df.select_dtypes(include='object').columns.tolist()
        elif fuzzy_conf.fields:
            search_cols = [c for c in fuzzy_conf.fields if c in df.columns]
        else:
            search_cols = []
        if not search_cols:
            warnings.warn('No valid field for fuzzy search - ignoring pattern.',
                         QuerexfuzzConfigurationWarning)
        else:
            if len(search_cols) == 1:
                search_list = df[search_cols[0]].astype(str).to_list()
            else:
                search_list = df[search_cols].apply(
                    lambda row: ' '.join(row.astype(str)), axis=1).to_list()

            limit = spec['top'] if spec['top'] > 0 else fuzzy_conf.limit

            # Cache matcher by (highlight_mode, data_hash). Evict oldest when > 8 entries.
            cache_key = (fuzzy_conf.highlight, hash(tuple(search_list)))
            if matcher_cache is not None and cache_key in matcher_cache:
                matcher = matcher_cache[cache_key]
                logger.debug('reusing cached fuzzy matcher')
            else:
                logger.info('building fuzzy matcher...')
                matcher = (FuzzyMatcherMultiHi if fuzzy_conf.highlight
                           else FuzzyMatcherMulti)(search_list)
                if matcher_cache is not None:
                    if len(matcher_cache) >= 8:
                        del matcher_cache[next(iter(matcher_cache))]
                    matcher_cache[cache_key] = matcher

            if fuzzy_conf.highlight:
                indices, scores, highlights = matcher.query(spec['fuzzy'], limit)
                if len(search_cols) == 1:
                    df = decorate(df, indices, scores, highlights,
                                  search_cols[0], fuzzy_conf.score_col_name)
                else:
                    df = df.iloc[indices].copy()
                    df[fuzzy_conf.score_col_name] = scores
            else:
                indices, scores = matcher.query(spec['fuzzy'], limit)
                df = df.iloc[indices].copy()
                df[fuzzy_conf.score_col_name] = scores

            logger.info('fuzzy search complete')
            has_fuzzy_results = True
        logger.debug('Applied fuzzy matching')

    # 5. Sort
    sort_cols = [col for col, asc in spec['sort']]
    sort_order = [asc for col, asc in spec['sort']]

    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=sort_order)
    elif has_fuzzy_results:
        df = df.sort_values(by=config.fuzzy.score_col_name, ascending=False)
    elif 'recent' in spec['flags']:
        if config.recent_field:
            df = df.sort_values(by=config.recent_field, ascending=False)
        else:
            warnings.warn('No valid recent field - recent sort ignored.',
                         QuerexfuzzConfigurationWarning)

    # 6. Limit (Top N)
    if spec['top'] > 0:
        df = df.head(spec['top'])
    elif spec['top'] < 0:
        df = df.tail(-spec['top'])

    # 7. Select Columns
    # `select *`    → base columns (default when no select clause)
    # `select **`   → all columns
    # `select a, b` → named columns
    # `select *, a` → base columns plus a
    # `select *, -a`→ base columns minus a  (- or ! prefix)
    # `select **,-a`→ all columns minus a
    sel = spec['select']
    if sel['include'] or sel['exclude']:
        if '__all__' in sel['include']:
            fields = list(df.columns)
        elif '__base__' in sel['include'] or not sel['include']:
            fields = [i for i in config.base_cols if i in df.columns]
        else:
            fields = []
        # de-duplicate while preserving order (i in seen is O(1))
        seen: Set[str] = set()
        fields = [i for i in fields if not (i in seen or seen.add(i))]
        fields = fields + [
            i for i in sel['include'] if i in df.columns and not (i in seen or seen.add(i))]
        final_fields = [f for f in fields if f not in sel['exclude']]
    elif config.base_cols:
        final_fields = [f for f in config.base_cols if f in df.columns]
    else:
        final_fields = list(df.columns)
    if has_fuzzy_results and fuzzy_conf.score_col_name not in final_fields:
        final_fields.append(fuzzy_conf.score_col_name)

    return df[final_fields]
