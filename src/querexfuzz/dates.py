"""
Convert date spec from parser into (start, end) datetime tuple.

Testers::

    s = Querexfuzz.parse('@ c @ m @ d @ y @mod m-3:2 @create y-10:9 @ d-91:30 ')
    for s in s['dates']:
        print(s)
        print(qfd.resolve_date_range(s))

"""

from datetime import datetime
from logging import getLogger

from dateutil.relativedelta import relativedelta
import tzlocal
import pandas as pd


TIMEZONE = tzlocal.get_localzone()

logger = getLogger(__name__)


def resolve_date_range(spec: dict) -> tuple[datetime, datetime]:
    """Converts a date spec from the parser into a (start, end) datetime tuple."""
    now = pd.Timestamp.now(tz=TIMEZONE)
    unit = spec['unit']

    # --- New section for 'c' (calendar year) unit ---
    if unit == 'c':
        current_year = now.year
        # the current partial year counts as 1
        # and the full year is added below
        # ergo subtract one
        start_offset = int(spec['start']) - 1
        end_offset = int(spec['end'])
        start_year = current_year - start_offset
        end_year = current_year - end_offset

        # Ensure start year is before end year
        if start_year > end_year:
            start_year, end_year = end_year, start_year

        start_date = pd.Timestamp(f"{start_year}-01-01", tz=TIMEZONE)
        # Go to the very end of the last day of the end year
        end_date = pd.Timestamp(f"{end_year}-12-31T23:59:59.999999", tz=TIMEZONE)

        # logger.debug("Resolved calendar year range: %s to %s", start_date, end_date)
        return start_date, end_date

    # --- Existing logic for relative units (y, m, d, etc.) ---
    unit_map = {
        'y': 'years', 'q': 'months', 'm': 'months',
        'w': 'weeks', 'd': 'days', 'h': 'hours'
    }
    multiplier = 3 if unit == 'q' else 1
    start_val = float(spec['start']) * multiplier
    end_val = float(spec['end']) * multiplier

    start_offset = relativedelta(**{unit_map[unit]: start_val})
    end_offset = relativedelta(**{unit_map[unit]: end_val})

    start_date = now - start_offset
    end_date = now - end_offset

    # Ensure the date range is in the correct order
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # logger.debug("Resolved relative date range: %s to %s", start_date, end_date)
    return start_date, end_date
