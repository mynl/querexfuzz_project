from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class FuzzyConfig(BaseModel):
    """Configuration for the fuzzy searcher."""
    fields: list[str] | Literal['all'] = ['all']
    limit: int = 100
    score_col_name: str = "score"
    highlight: bool = True    # whether to use Highlight mode or not


class QuerexfuzzConfig(BaseModel):
    """Main configuration for the Querexfuzz engine."""
    base_cols: list[str] = Field(default_factory=list)
    bang_field: str | None = None
    date_fields: list[str] = Field(default_factory=list)
    default_date_field: str | None = None
    recent_field: str | None = None
    fuzzy: FuzzyConfig = Field(default_factory=FuzzyConfig)

    @field_validator("default_date_field")
    def _validate_default_date(cls, v, info):
        if v and v not in info.data.get("date_fields", []):
            raise ValueError(f"default_date_field '{v}'"
                             " must be in date_fields.")
        return v

    @classmethod
    def from_yaml(cls, path: Path):
        """Loads configuration from a YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found at {path}")
        with path.open('r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

