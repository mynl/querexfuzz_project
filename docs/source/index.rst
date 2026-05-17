.. querexfuzz documentation master file

Querexfuzz
==========

**Querexfuzz** is a flexible query engine for `pandas <https://pandas.pydata.org>`_
DataFrames. It lets you filter, sort, and search your data using a single unified query
string that combines SQL-like ``where`` clauses, regular expressions, relative date ranges,
and fuzzy matching — without leaving Python.

.. code-block:: python

   from querexfuzz import querexfuzz_from_df

   querexfuzz_from_df(df)   # attaches .querex() to df

   df.querex("top 10 where department == 'Engineering' @y-1 # python")

Key features:

- **Unified syntax** — combine ``where``, regex, date, fuzzy, sort, and select in one string
- **DataFrame native** — attaches ``.querex()`` and ``.q()`` directly to your DataFrame instance
- **Auto-configuration** — ``querexfuzz_from_df`` inspects column types and wires up defaults
- **Fast fuzzy search** — powered by `skimmatch <https://github.com/mynl/skimmatch>`_; matcher built once and cached
- **Configurable** — via keyword arguments, YAML file, or both

----

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting-started
   query-syntax
   api
