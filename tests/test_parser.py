import pytest
from querexfuzz.parser import parser

# (query_string, expected_top_value, expected_fuzzy_value)
# top defaults to 0 (no limit) when no top clause is present
parser_test_cases = [
    ("top 10 # fuzzy query", 10, "fuzzy query"),
    ("recent select name, age", 0, None),
    ("! /some_regex/", 0, None),
    ("# just a fuzzy search", 0, "just a fuzzy search"),
    ("", 0, None),
]

@pytest.mark.parametrize("query, expected_top, expected_fuzzy", parser_test_cases)
def test_parser_basic_structure(query, expected_top, expected_fuzzy):
    """Tests that the parser correctly splits fuzzy queries and parses clauses."""
    spec = parser(query)
    assert isinstance(spec, dict)
    assert spec['top'] == expected_top
    assert spec['fuzzy'] == expected_fuzzy

def test_parser_date_clause():
    """Tests date spec parsing. start and end are always ints."""
    spec = parser("@d-7")
    expected = {'field': None, 'unit': 'd', 'start': 7, 'end': 0}
    assert spec['dates'][0] == expected

def test_parser_invalid_query():
    """Tests that the parser raises an error for invalid syntax."""
    with pytest.raises(ValueError):
        parser("top select where")
