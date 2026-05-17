"""Querexfuzz: A flexible query engine for pandas DataFrames."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("querexfuzz")
except PackageNotFoundError:
    __version__ = "unknown"

from .core import Querexfuzz, querexfuzz_from_df, querexfuzz_help

__all__ = ["Querexfuzz", "querexfuzz_from_df", "querexfuzz_help"]
