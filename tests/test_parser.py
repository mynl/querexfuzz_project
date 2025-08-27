import pytest
from querexfuzz.parser import parser

# A list of test cases: (query_string, expected_top_value, expected_fuzzy_value)
parser_test_cases = [
    ("top 10 # fuzzy query", 10, "fuzzy query"),
    ("recent select name, age", -1, None),
    ("! /some_regex/", -1, None),
    ("# just a fuzzy search", -1, "just a fuzzy search"),
    ("", -1, None),
]

@pytest.mark.parametrize("query, expected_top, expected_fuzzy", parser_test_cases)
def test_parser_basic_structure(query, expected_top, expected_fuzzy):
    """Tests that the parser correctly splits fuzzy queries and parses clauses."""
    spec = parser(query)
    assert isinstance(spec, dict)
    assert spec['top'] == expected_top
    assert spec['fuzzy'] == expected_fuzzy

def test_parser_date_clause():
    """Tests a more specific aspect of the parser, like date handling."""
    query = "@d-7"
    spec = parser(query)
    expected_date_spec = {
        'field': None, 'unit': 'd', 'start': '7', 'end': '0'
    }
    assert spec['dates'][0] == expected_date_spec

def test_parser_invalid_query():
    """Tests that the parser raises an error for invalid syntax."""
    with pytest.raises(ValueError):
        parser("top select where") # Invalid grammar
