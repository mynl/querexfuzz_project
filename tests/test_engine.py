# in tests/test_engine.py

def test_where_clause(configured_df):
    """Tests a simple 'where' query."""
    result_df = configured_df.querexfuzz("where city == 'Berlin'")
    assert len(result_df) == 2
    assert all(result_df['city'] == 'Berlin')

def test_top_clause(configured_df):
    """Tests the 'top' clause."""
    result_df = configured_df.querexfuzz("top 3")
    assert len(result_df) == 3

def test_date_clause(configured_df):
    """
    Tests a date query. NOTE: This is sensitive to the current date.
    The current date is 2025-08-27.
    """
    # People registered in the last 3 months (since 2025-05-27)
    result_df = configured_df.querexfuzz("@m-3")
    assert len(result_df) == 4
    assert 'Charlie' not in result_df['name'].values

def test_fuzzy_clause(configured_df):
    """Tests a fuzzy search query."""
    result_df = configured_df.querexfuzz("# dam") # Should match Amsterdam
    assert len(result_df) == 2
    assert 'score' in result_df.columns
    assert all(result_df['city'] == 'Amsterdam')

def test_complex_query(configured_df):
    """Tests a query combining multiple clauses."""
    query = "where age > 30 select name, city order by name"
    result_df = configured_df.querexfuzz(query)

    assert len(result_df) == 2
    assert list(result_df.columns) == ['name', 'city']
    assert result_df.iloc[0]['name'] == 'Charlie' # After sorting
