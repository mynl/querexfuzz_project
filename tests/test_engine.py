def test_where_clause(configured_df):
    """Tests a simple 'where' query."""
    result_df = configured_df.querex("where city == 'Berlin'")
    assert len(result_df) == 2
    assert all(result_df['city'] == 'Berlin')

def test_top_clause(configured_df):
    """Tests the 'top' clause."""
    result_df = configured_df.querex("top 3")
    assert len(result_df) == 3

def test_date_clause(configured_df):
    """Tests a date query. Fixture dates are relative to now so this stays valid."""
    # Alice(-10d), Bob(-60d), David(-5d), Eve(-30d) are within 3 months; Charlie(-500d) is not
    result_df = configured_df.querex("@m-3")
    assert len(result_df) == 4
    assert 'Charlie' not in result_df['name'].values

def test_fuzzy_clause(configured_df):
    """Tests a fuzzy search query."""
    result_df = configured_df.querex("# dam")  # should match Amsterdam
    assert len(result_df) == 2
    assert 'score' in result_df.columns
    assert all(result_df['city'] == 'Amsterdam')

def test_complex_query(configured_df):
    """Tests a query combining multiple clauses."""
    result_df = configured_df.querex("where age > 30 select name, city order by name")
    assert len(result_df) == 3  # Charlie(35), David(40), Eve(45)
    assert list(result_df.columns) == ['name', 'city']
    assert result_df.iloc[0]['name'] == 'Charlie'  # alphabetical sort
