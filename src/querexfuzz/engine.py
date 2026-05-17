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
    """Warning raised when Querexfzz configuration is unusual or suboptimal."""
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
def execute_query(df: pd.DataFrame, spec: dict, config: QuerexfuzzConfig) -> pd.DataFrame:
    """Apply the parsed query specification to a DataFrame."""
    df = df.copy()

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
                logger.warning(f"Warning: Regex error with pattern '{pattern}'. "
                               "Ignoring and continuing.")
        else:
            raise ValueError(f"Invalid column for regex search: '{col}'")

    # 3. Filter: Date clauses
    for date_filter in spec['dates']:
        col = date_filter['field'] or config.default_date_field
        if not col or col not in df.columns:
            warnings.warn('No valid field for date spec - ignoring.',
                         QuerexfuzzConfigurationWarning
                         )
        else:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            start_date, end_date = resolve_date_range(date_filter)
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
                         QuerexfuzzConfigurationWarning
                         )
        else:
            if len(search_cols) == 1:
                search_list = df[search_cols[0]].astype(str).to_list()
            else:
                search_list = df[search_cols].apply(
                    lambda row: ' '.join(row.astype(str)), axis=1).to_list()

            limit = spec['top'] if spec['top'] > 0 else fuzzy_conf.limit

            if fuzzy_conf.highlight:
                logger.info('creating highlighting matcher...')
                matcher = FuzzyMatcherMultiHi(search_list)
                logger.info('creating matcher...done')
                indices, scores, highlights = matcher.query(spec['fuzzy'], limit)
                logger.info('rust matching complete')
                # decorate only makes sense with one column
                if len(search_cols) == 1:
                    df = decorate(df, indices, scores, highlights,
                        search_cols[0], fuzzy_conf.score_col_name)
                else:
                    # manual
                    df = df.iloc[indices].copy()
                    df[fuzzy_conf.score_col_name] = scores
            else:
                logger.info('creating fuzzy matcher...')
                matcher = FuzzyMatcherMulti(search_list)
                logger.info('created fuzzy matcher')
                indices, scores = matcher.query(spec['fuzzy'], limit)
                df = df.iloc[indices].copy()
                df[fuzzy_conf.score_col_name] = scores
            logger.info('created fuzzy search output')
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
                         QuerexfuzzConfigurationWarning
                         )
    # 6. Limit (Top N)
    if spec['top'] > 0:
        df = df.head(spec['top'])
    elif spec['top'] < 0:
        df = df.tail(-spec['top'])

    # 7. Select Columns
    # per README
    # `select *` means select the base columns (and is the default behavior with no select clause)
    # `select **` actually selects all the columns
    # `select a, b, c` selects `a`, `b` and `c`
    # `select *, a, b` selects the base columns plus `a` and `b`
    # `select *, ~a, !b` selects the base columns minus `a` and `b`; either `-` or `!` can be used
    # `select **, -a` selects all columns except `a`
    sel = spec['select']
    if sel['include'] or sel['exclude']:
        if '__all__' in sel['include']:
            fields = list(df.columns)
        elif '__base__' in sel['include'] or not sel['include']:
            # just in case and to get the right order
            # or empty include => base cols by default
            fields = [i for i in config.base_cols if i in df.columns]
        else:
            fields = []
        # de-duplicate (note i in seen is O(1) because of hashing)
        seen = set()
        fields = [i for i in fields if not (i in seen or seen.add(i))]
        # do in two steps to avoid duplicating fields
        fields = fields + [
            i for i in sel['include'] if i in df.columns and not (i in seen or seen. add(i))]
        final_fields = [
            f for f in fields if f not in sel['exclude']]
    elif config.base_cols:
        # if there is no select clause
        final_fields = [f for f in config.base_cols if f in df.columns]
    else:
        # no select and no base_cols ==> all cols
        final_fields = list(df.columns)
    if has_fuzzy_results and fuzzy_conf.score_col_name not in final_fields:
        final_fields.append(fuzzy_conf.score_col_name)

    df = df[final_fields]

    return df
