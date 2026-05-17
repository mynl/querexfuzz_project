import pandas as pd
import pytest
from querexfuzz import Querexfuzz


@pytest.fixture
def test_df():
    """Standard DataFrame for testing. Dates are relative to now so date tests stay valid."""
    now = pd.Timestamp.now().floor('D')
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'city': ['Amsterdam', 'Berlin', 'Copenhagen', 'Berlin', 'Amsterdam'],
        'registered_date': [
            now - pd.Timedelta(days=10),   # very recent
            now - pd.Timedelta(days=60),   # ~2 months ago — within 3 months
            now - pd.Timedelta(days=500),  # >1 year ago — outside 3 months
            now - pd.Timedelta(days=5),    # very recent
            now - pd.Timedelta(days=30),   # ~1 month ago — within 3 months
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def configured_df(test_df):
    """DataFrame with .querex method attached, configured to match the test data."""
    engine = Querexfuzz(
        base_cols=['name', 'city', 'registered_date', 'age'],
        date_fields=['registered_date'],
        default_date_field='registered_date',
        bang_field='name',
        recent_field='registered_date',
        fuzzy=dict(fields=['name', 'city'], limit=50, score_col_name='score'),
    )
    return engine.attach_to(test_df.copy())
