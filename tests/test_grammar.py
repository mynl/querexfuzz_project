"""Comprehensive grammar coverage tests.

One test per grammar feature, exercising both parsing and execution end-to-end.
Uses the `gdf` fixture: 15-row employee DataFrame with .querex attached.

DataFrame quick-reference (hire_date days ago):
  Alice Anderson   Engineering  95000  7yr  2600d
  Bob Baker        Marketing    72000  3yr   800d
  Charlie Chen     Engineering  88000  5yr  1300d
  Diana Drake      Sales        65000  2yr   300d
  Eve Ellis        Engineering 102000 10yr  3700d
  Frank Foster     HR           58000  1yr    60d
  Grace Green      Marketing    69000  4yr  1000d
  Henry Hall       Finance      84000  6yr  2200d
  Iris Irving      Engineering  91000  8yr  3000d
  James Johnson    Sales        71000  3yr   420d
  Kate King        HR           55000  2yr   120d
  Leo Lopez        Finance      78000  5yr  1700d
  Mary Moore       Marketing    74000  4yr  1000d
  Ned Nash         Engineering  97000  9yr  3300d
  Olivia Owen      Sales        63000  1yr    25d

base_cols  = [name, department, salary, years, rating, hire_date]  (6 cols)
bang_field = notes    (not in base_cols)
fuzzy      = name, department, notes
"""
BASE_COLS = ['name', 'department', 'salary', 'years', 'rating', 'hire_date']
ALL_COLS = BASE_COLS + ['notes']


# ===========================================================================
# Empty query
# ===========================================================================

def test_empty_query(gdf):
    result = gdf.querex("")
    assert len(result) == 15
    assert list(result.columns) == BASE_COLS


# ===========================================================================
# Flags
# ===========================================================================

def test_verbose_flag(gdf):
    result = gdf.querex("verbose")
    assert len(result) == 15

def test_recent_sorts_descending(gdf):
    # most recent hire = Olivia Owen (25d ago)
    result = gdf.querex("recent")
    assert result.iloc[0]['name'] == 'Olivia Owen'

def test_recent_and_verbose(gdf):
    result = gdf.querex("verbose recent")
    assert result.iloc[0]['name'] == 'Olivia Owen'


# ===========================================================================
# Top / Bottom
# ===========================================================================

def test_top_n(gdf):
    assert len(gdf.querex("top 5")) == 5

def test_bottom_n(gdf, grammar_df):
    result = gdf.querex("bottom 3")
    assert len(result) == 3
    # tail(3) of original row order: Mary Moore, Ned Nash, Olivia Owen
    assert list(result['name']) == list(grammar_df.tail(3)['name'])

def test_recent_top(gdf):
    result = gdf.querex("recent top 3")
    assert len(result) == 3
    assert result.iloc[0]['name'] == 'Olivia Owen'


# ===========================================================================
# Select
# ===========================================================================

def test_select_star(gdf):
    result = gdf.querex("select *")
    assert list(result.columns) == BASE_COLS
    assert len(result) == 15

def test_select_double_star(gdf):
    result = gdf.querex("select **")
    assert list(result.columns) == ALL_COLS

def test_select_named(gdf):
    result = gdf.querex("select name, salary")
    assert list(result.columns) == ['name', 'salary']

def test_select_star_plus_col(gdf):
    result = gdf.querex("select *, notes")
    assert list(result.columns) == ALL_COLS

def test_select_star_minus_col_dash(gdf):
    result = gdf.querex("select *, -salary")
    assert 'salary' not in result.columns
    assert len(result.columns) == 5

def test_select_star_minus_col_bang(gdf):
    result = gdf.querex("select *, !salary")
    assert 'salary' not in result.columns
    assert len(result.columns) == 5

def test_select_double_star_minus_col(gdf):
    result = gdf.querex("select **, -notes")
    assert 'notes' not in result.columns
    assert list(result.columns) == BASE_COLS


# ===========================================================================
# Regex
# ===========================================================================

def test_regex_bang_plain(gdf):
    # bang_field=notes; 'python' appears in Alice, Charlie, Eve, Iris, Ned
    result = gdf.querex("! python")
    assert len(result) == 5

def test_regex_bang_slash(gdf):
    result = gdf.querex("! /python/")
    assert len(result) == 5

def test_regex_ident(gdf):
    result = gdf.querex("department ~ ^E")
    assert len(result) == 5
    assert all(result['department'] == 'Engineering')

def test_regex_ident_slash(gdf):
    result = gdf.querex("department ~ /^Engineering$/")
    assert len(result) == 5

def test_regex_case_insensitive(gdf):
    result = gdf.querex("! PYTHON")
    assert len(result) == 5

def test_regex_multiple_and(gdf):
    # notes ~ 'marketing' AND department ~ 'Marketing' → Bob, Grace, Mary
    result = gdf.querex("! marketing and department ~ Marketing")
    assert len(result) == 3
    assert set(result['department']) == {'Marketing'}


# ===========================================================================
# Where
# ===========================================================================

def test_where_eq(gdf):
    result = gdf.querex("where department == 'Engineering'")
    assert len(result) == 5

def test_where_ne(gdf):
    result = gdf.querex("where department != 'Engineering'")
    assert len(result) == 10

def test_where_gt(gdf):
    result = gdf.querex("where salary > 90000")
    assert len(result) == 4

def test_where_gte(gdf):
    result = gdf.querex("where salary >= 95000")
    assert len(result) == 3

def test_where_lt(gdf):
    result = gdf.querex("where salary < 60000")
    assert len(result) == 2

def test_where_lte(gdf):
    result = gdf.querex("where salary <= 58000")
    assert len(result) == 2

def test_where_and(gdf):
    result = gdf.querex("where department == 'Engineering' and salary > 90000")
    assert len(result) == 4
    assert all(result['department'] == 'Engineering')

def test_where_or(gdf):
    result = gdf.querex("where department == 'Engineering' or department == 'Finance'")
    assert len(result) == 7

def test_where_parenthesized(gdf):
    q = "where (department == 'Engineering' or department == 'Finance') and salary > 85000"
    result = gdf.querex(q)
    assert len(result) == 5  # Eng: Alice,Charlie,Eve,Iris,Ned; Finance: none (Henry=84k)
    assert all(result['salary'] > 85000)


# ===========================================================================
# Order By
# ===========================================================================

def test_order_by_asc(gdf):
    result = gdf.querex("order by salary")
    assert result.iloc[0]['salary'] == 55000  # Kate King

def test_order_by_desc(gdf):
    result = gdf.querex("order by -salary")
    assert result.iloc[0]['salary'] == 102000  # Eve Ellis

def test_sort_by_alias(gdf):
    result = gdf.querex("sort by salary")
    assert result.iloc[0]['salary'] == 55000

def test_order_by_multiple(gdf):
    # dept asc, then name asc → first is Alice Anderson (Engineering, A)
    result = gdf.querex("order by department, name")
    assert result.iloc[0]['name'] == 'Alice Anderson'

def test_order_by_mixed(gdf):
    # dept asc, salary desc → Engineering first; Eve has highest Engineering salary
    result = gdf.querex("order by department, -salary")
    assert result.iloc[0]['name'] == 'Eve Ellis'
    assert result.iloc[0]['department'] == 'Engineering'


# ===========================================================================
# Date
# ===========================================================================

def test_date_d_unit(gdf):
    # @d-30: last 30 days; only Olivia (25d) qualifies
    result = gdf.querex("@d-30")
    assert len(result) == 1
    assert result.iloc[0]['name'] == 'Olivia Owen'

def test_date_m_unit(gdf):
    # @m-3: last 3 calendar months (~91d); Olivia(25d) + Frank(60d); Kate(120d) excluded
    result = gdf.querex("@m-3")
    assert len(result) == 2
    assert set(result['name']) == {'Olivia Owen', 'Frank Foster'}

def test_date_y_one_year(gdf):
    # @y-1: last year; Olivia(25d), Frank(60d), Kate(120d), Diana(300d) = 4
    result = gdf.querex("@y-1")
    assert len(result) == 4

def test_date_y_two_years(gdf):
    # @y-2: last 2 years; adds James(420d) = 5
    result = gdf.querex("@y-2")
    assert len(result) == 5

def test_date_range_form(gdf):
    # @y-5:1: window from 5y ago to 1y ago (365d–1825d)
    # James(420), Bob(800), Grace(1000), Mary(1000), Charlie(1300), Leo(1700) = 6
    result = gdf.querex("@y-5:1")
    assert len(result) == 6

def test_date_unit_only(gdf):
    # @y with no offset → start defaults to 1, end=0 → same as @y-1
    result = gdf.querex("@y")
    assert len(result) == 4

def test_date_named_field(gdf):
    # explicit field name; same result as @y-2
    result = gdf.querex("@hire_date y-2")
    assert len(result) == 5

def test_date_excludes_old(gdf):
    result = gdf.querex("@y-1")
    names = set(result['name'])
    assert 'Ned Nash' not in names    # 3300d ago
    assert 'Eve Ellis' not in names   # 3700d ago


# ===========================================================================
# Fuzzy
# ===========================================================================

def test_fuzzy_score_col_present(gdf):
    result = gdf.querex("# alice")
    assert 'score' in result.columns

def test_fuzzy_top_result(gdf):
    result = gdf.querex("# alice")
    assert result.iloc[0]['name'] == 'Alice Anderson'

def test_fuzzy_top_limits_rows(gdf):
    result = gdf.querex("top 2 # python")
    assert len(result) == 2

def test_fuzzy_prefilter_and_fuzzy(gdf):
    # pre-filter to Engineering, then fuzzy over full df, intersect back
    result = gdf.querex("where department == 'Engineering' # python")
    assert 'score' in result.columns
    assert all(result['department'] == 'Engineering')


# ===========================================================================
# Combinations
# ===========================================================================

def test_top_and_where(gdf):
    result = gdf.querex("top 3 where department == 'Engineering'")
    assert len(result) == 3
    assert all(result['department'] == 'Engineering')

def test_where_and_select(gdf):
    result = gdf.querex("where salary > 90000 select name, salary")
    assert len(result) == 4
    assert list(result.columns) == ['name', 'salary']

def test_where_and_sort(gdf):
    result = gdf.querex("where department == 'Engineering' order by -salary")
    assert len(result) == 5
    assert result.iloc[0]['name'] == 'Eve Ellis'

def test_regex_and_where(gdf):
    # regex on notes (bang_field), then where on salary
    # all 4 high-earners (Alice, Eve, Iris, Ned) also have 'python' in notes
    result = gdf.querex("! python where salary > 90000")
    assert len(result) == 4
    assert all(result['salary'] > 90000)

def test_date_and_select(gdf):
    result = gdf.querex("@y-1 select name, hire_date")
    assert len(result) == 4
    assert list(result.columns) == ['name', 'hire_date']

def test_recent_top_where(gdf):
    # Engineers sorted most-recent-first: Charlie(1300d), Alice(2600d), Iris(3000d), Ned(3300d), Eve(3700d)
    result = gdf.querex("recent top 3 where department == 'Engineering'")
    assert len(result) == 3
    assert result.iloc[0]['name'] == 'Charlie Chen'

def test_bottom_and_sort(gdf):
    # sort by salary asc, then bottom 5 = last 5 = five highest salaries (≥88000)
    result = gdf.querex("order by salary bottom 5")
    assert len(result) == 5
    assert all(result['salary'] >= 88000)

def test_where_sort_select(gdf):
    # years > 5: Alice(7), Eve(10), Henry(6), Iris(8), Ned(9) = 5 rows
    # order by -salary: Eve(102k), Ned(97k), Alice(95k), Iris(91k), Henry(84k)
    result = gdf.querex("where years > 5 order by -salary select name, department, salary")
    assert len(result) == 5
    assert list(result.columns) == ['name', 'department', 'salary']
    assert result.iloc[0]['name'] == 'Eve Ellis'
