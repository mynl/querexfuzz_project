from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta


def resolve_date_range(spec: dict) -> tuple[datetime, datetime]:
    """Converts a date spec from the parser into a (start, end) datetime tuple."""
    now = pd.Timestamp.now()
    unit = spec['unit']
    unit_map = {
        'y': 'years', 'q': 'months', 'm': 'months',
        'w': 'weeks', 'd': 'days', 'h': 'hours'
    }

    # Handle special case for "this year"
    if spec['end'] is None:
        start_date = pd.Timestamp(f"{now.year}-01-01")
        end_date = pd.Timestamp(f"{now.year}-12-31T23:59:59")
        return start_date, end_date

    multiplier = 3 if unit == 'q' else 1
    start_val = int(spec['start']) * multiplier
    end_val = int(spec['end']) * multiplier

    start_offset = relativedelta(**{unit_map[unit]: start_val})
    end_offset = relativedelta(**{unit_map[unit]: end_val})

    start_date = now - start_offset
    end_date = now - end_offset

    return (start_date, end_date) if start_date <= end_date else (end_date, start_date)
