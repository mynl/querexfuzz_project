import pandas as pd
import pytest
from querexfuzz import Querexfuzz

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------
BASE_COLS = ['name', 'department', 'salary', 'years', 'rating', 'hire_date']


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


@pytest.fixture
def grammar_df():
    """15-row employee DataFrame for comprehensive grammar coverage tests.

    Dates are relative to now so date-range tests stay valid over time.
    `notes` is intentionally absent from base_cols so select * vs ** differ.
    """
    now = pd.Timestamp.now().floor('D')
    days = [2600, 800, 1300, 300, 3700, 60, 1000, 2200, 3000, 420, 120, 1700, 1000, 3300, 25]
    data = {
        'name': [
            'Alice Anderson', 'Bob Baker', 'Charlie Chen', 'Diana Drake',
            'Eve Ellis', 'Frank Foster', 'Grace Green', 'Henry Hall',
            'Iris Irving', 'James Johnson', 'Kate King', 'Leo Lopez',
            'Mary Moore', 'Ned Nash', 'Olivia Owen',
        ],
        'department': [
            'Engineering', 'Marketing', 'Engineering', 'Sales',
            'Engineering', 'HR', 'Marketing', 'Finance',
            'Engineering', 'Sales', 'HR', 'Finance',
            'Marketing', 'Engineering', 'Sales',
        ],
        'salary': [
            95000, 72000, 88000, 65000, 102000, 58000, 69000, 84000,
            91000, 71000, 55000, 78000, 74000, 97000, 63000,
        ],
        'years': [7, 3, 5, 2, 10, 1, 4, 6, 8, 3, 2, 5, 4, 9, 1],
        'rating': [4.5, 3.8, 4.2, 3.5, 4.9, 3.2, 4.0, 4.3, 4.7, 3.6, 3.1, 4.1, 3.9, 4.8, 3.4],
        'hire_date': [now - pd.Timedelta(days=d) for d in days],
        'notes': [
            'senior python developer backend systems',
            'social media marketing campaigns digital',
            'python java full stack developer',
            'enterprise software sales consultant',
            'lead architect cloud infrastructure python',
            'recruitment onboarding talent acquisition',
            'brand strategy content marketing analytics',
            'financial reporting tax compliance audit',
            'machine learning python data science',
            'regional sales manager enterprise accounts',
            'employee relations benefits administration',
            'budget forecasting financial analysis',
            'email campaigns social marketing analytics',
            'senior python developer distributed systems',
            'new business development sales pipeline',
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def gdf(grammar_df):
    """grammar_df with .querex / .q attached via a fully configured engine."""
    engine = Querexfuzz(
        base_cols=BASE_COLS,
        date_fields=['hire_date'],
        default_date_field='hire_date',
        bang_field='notes',
        recent_field='hire_date',
        fuzzy=dict(fields=['name', 'department', 'notes'], limit=15, score_col_name='score'),
    )
    engine.attach_to(grammar_df)
    return grammar_df
