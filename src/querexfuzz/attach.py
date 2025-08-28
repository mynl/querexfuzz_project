import logging
from pathlib import Path
from types import MethodType
import yaml

import pandas as pd

from .parser import parser
from .engine import execute_query
from .config import QuerexfuzzConfig  # Assuming your Pydantic model is here


logger = logging.getLogger(__name__)

# Define the method name as a class attribute for consistency
_METHOD_NAME = "querefuzz"

class Querexfuzz:
    """Manages configuration and attachment of the .querefuzz method."""

    def __init__(self, *, config_path: str | Path | None = None, **kwargs):
        """
        Initializes the Querefuzz engine with a flexible configuration.

        The configuration can be loaded from a YAML file, provided directly as
        keyword arguments, or both (with keyword arguments overriding the file's
        settings).

        Args:
            config_path (str | Path | None, optional): The path to a YAML
                configuration file. Defaults to None.
            **kwargs: Keyword arguments that correspond to the fields in the
                QuerefuzzConfig model. These will override any values loaded
                from the config_path.

        Examples:
            >>> # 1. From a file only
            >>> qf = Querefuzz(config_path='config.yml')

            >>> # 2. From keyword arguments only
            >>> qf = Querefuzz(base_cols=['name', 'age'], recent_field='mod')

            >>> # 3. From a file with specific overrides
            >>> qf = Querefuzz(config_path='config.yml', fuzzy={'limit': 200})
        """
        config_data = {}
        if config_path:
            self.config_path = Path(config_path)
            with self.config_path.open('r') as f:
                config_data = yaml.safe_load(f)

        # Keyword arguments override the data loaded from the file
        # inplace update, same as config_data.update(kwargs)
        config_data |= kwargs

        # Validate and create the final config object using Pydantic
        self.config = QuerexfuzzConfig(**config_data)

        logger.info("Querexfuzz engine initialized successfully.")
        logger.debug(
            "Final configuration:\n%s",
            self.config.model_dump_json(indent=4)
        )

    def _query_method(self, df: pd.DataFrame, expr: str) -> pd.DataFrame:
        """The method that is attached to the DataFrame."""
        spec = parser(expr)
        logger.debug("Parsed query spec: %s", spec)
        return execute_query(df, spec, self.config)

    def attach_to(self, df: pd.DataFrame, alias: str | None = 'q') -> pd.DataFrame:
        """
        Attaches the query method to a DataFrame instance.

        Args:
            df (pd.DataFrame): The DataFrame to modify.
            alias (str | None, optional): A short alias for the query method.
                Set to 'q' by default. If None or '', no alias is created.
                Defaults to 'q'.

        Returns:
            pd.DataFrame: The same DataFrame, now with the query method attached.
        """
        logger.debug(
            "Attaching .%s method to DataFrame with id: %d",
            self._METHOD_NAME, id(df)
        )
        setattr(df, self._METHOD_NAME, MethodType(self._query_method, df))

        if alias:
            logger.debug(
                "Adding alias '.%s' for the query method.", alias
            )
            setattr(df, alias, MethodType(self._query_method, df))

        return df
