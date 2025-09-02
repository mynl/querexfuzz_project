import logging
from pathlib import Path
from types import MethodType
import yaml

import pandas as pd

from .parser import parser
from .engine import execute_query
from .config import QuerexfuzzConfig, FuzzyConfig


logger = logging.getLogger(__name__)

# Define the method name as a class attribute for consistency
_METHOD_NAME = "querexfuzz"


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
        # logger.debug(
        #     "Final configuration:\n%s",
        #     self.config.model_dump_json(indent=4)
        # )

    @staticmethod
    def parse(expr):
        """Convenience method for testing parser."""
        # note, you can also import parser directly!
        return parser(expr)

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
            _METHOD_NAME, id(df)
        )
        setattr(df, _METHOD_NAME, MethodType(self._query_method, df))

        if alias:
            logger.debug(
                "Adding alias '.%s' for the query method.", alias
            )
            setattr(df, alias, MethodType(self._query_method, df))

        return df


# helper factory method
def querexfuzz_from_df(df, *, base_cols=None, bang_field=None,
                       default_date_field=None, recent_field=None,
                       fuzzy_fields=None, score_col_name='score', attach=True):
    """
    Create a Querexfuzz by inspecting df.

    By default, all columns not starting _ are selected to base_cols.
    All date fields to date_fields. If only one, it becomes the
    default_date_field (default for @ clauses) and the recent_field
    (field for sorting for recent).

    If there is only one object field, it becomes the bang field (default
    for regex).
    If fuzzy_fields is None then all object fields are selected. If there
    is only one, it becomes bang_field if that is omitted.

    Highlight mode is true if len(fuzzy_fields)==1.

    Parameters
    ----------

    bang_field, default_date_field, recent_field ->
    score_col_name: name for the score column in fuzzy matches
    attach: attach querexfuzz method to df (default True)

    """
    base_cols = base_cols or [i for i in df.columns if i[0] != '_']
    date_fields = [i for i in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns if i[0] != '_']
    if default_date_field is None and len(date_fields) == 1:
        default_date_field = date_fields[0]
    if recent_field is None and len(date_fields) == 1:
        recent_field = date_fields[0]
    elif recent_field is None and default_date_field is not None:
        recent_field = default_date_field
    elif recent_field is not None and default_date_field is None:
        default_date_field = recent_field

    # ensure_list:
    fuzzy_fields = [fuzzy_fields] if isinstance(fuzzy_fields, str) else fuzzy_fields
    fuzzy_fields = fuzzy_fields or [i for i in df.select_dtypes(include="object").columns
                                    if i[0] != '_']
    if bang_field is None and len(fuzzy_fields) == 1:
        bang_field = fuzzy_fields[0]

    highlight = len(fuzzy_fields) == 1

    qfz = Querexfuzz(
        base_cols=base_cols,
        date_fields=date_fields,
        default_date_field=default_date_field,
        bang_field=bang_field,
        recent_field=recent_field,
        fuzzy=FuzzyConfig(fields=fuzzy_fields,
                          limit=50,
                          score_col_name=score_col_name,
                          highlight=highlight)
    )
    if attach:
        # this acts in-place
        qfz.attach_to(df)
    return qfz
