# in tests/conftest.py
import pandas as pd
import pytest
from querexfuzz import Querexfuzz

@pytest.fixture(scope="module")
def test_df():
    """Provides a standard DataFrame for testing."""
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'city': ['Amsterdam', 'Berlin', 'Copenhagen', 'Berlin', 'Amsterdam'],
        'registered_date': pd.to_datetime([
            '2025-08-10', '2025-06-15', '2024-01-20', '2025-08-25', '2025-07-30'
        ])
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="module")
def configured_df(test_df):
    """Provides a DataFrame with the .querexfuzz method already attached."""
    # This assumes a valid config.yml exists at the project root
    qflex_engine = Querexfuzz(config_path='config.yml')
    return qflex_engine.attach_to(test_df.copy())
