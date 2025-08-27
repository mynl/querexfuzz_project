from pathlib import Path
from types import MethodType
from functools import partial
import pandas as pd
from .config import QuerexfuzzConfig
from .parser import parser
from .engine import execute_query

class Querexfuzz:
    """Manages configuration and attachment of the .querexfuzz method."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config = QuerexfuzzConfig.from_yaml(self.config_path)

    def _query_method(self, df: pd.DataFrame, expr: str) -> pd.DataFrame:
        """The method that will be attached to the DataFrame."""
        spec = parser(expr)
        return execute_query(df, spec, self.config)

    def attach_to(self, df: pd.DataFrame) -> pd.DataFrame:
        """Attaches the .querexfuzz method to a DataFrame instance."""
        df.querexfuzz = MethodType(self._query_method, df)
        return df
