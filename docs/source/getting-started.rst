Getting Started
===============

Installation
------------

Install from PyPI::

   pip install querexfuzz

Or with `uv <https://docs.astral.sh/uv/>`_ (recommended)::

   uv add querexfuzz

Querexfuzz requires Python 3.13 or later and pandas 2.0 or later.

----

Quickstart
----------

The fastest way to get started is :func:`querexfuzz_from_df`, which inspects your
DataFrame's column types and configures everything automatically.

.. code-block:: python

   import pandas as pd
   from querexfuzz import querexfuzz_from_df

   df = pd.DataFrame({
       'name':    ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
       'dept':    ['Engineering', 'Marketing', 'Engineering', 'Sales', 'Engineering'],
       'salary':  [95000, 72000, 88000, 65000, 102000],
       'joined':  pd.to_datetime(['2020-03-01', '2022-06-15', '2021-09-01',
                                  '2023-01-10', '2019-07-20']),
   })

   querexfuzz_from_df(df)   # attaches .querex() and .q() to df in-place

Now query with ``.querex()`` or the short alias ``.q()``:

.. code-block:: python

   # All engineers
   df.querex("where dept == 'Engineering'")

   # Top 3 most recently joined, showing name and salary only
   df.querex("recent top 3 select name, salary")

   # Hired in the last 5 years, salary above 80k
   df.querex("where salary > 80000 @y-5")

   # Fuzzy search — must be last
   df.q("# alc")

----

Explicit configuration
----------------------

For full control, create a :class:`Querexfuzz` instance with keyword arguments and attach
it to one or more DataFrames:

.. code-block:: python

   from querexfuzz import Querexfuzz

   engine = Querexfuzz(
       base_cols=['name', 'dept', 'salary', 'joined'],
       date_fields=['joined'],
       default_date_field='joined',
       bang_field='name',          # default column for ! regex
       recent_field='joined',      # column used by 'recent' sort
       fuzzy=dict(
           fields=['name', 'dept'],
           limit=50,
           score_col_name='score',
       ),
   )

   engine.attach_to(df)
   df.querex("recent top 5 where salary > 80000")

----

From a YAML file
----------------

Configuration can also be loaded from a YAML file, with optional keyword overrides:

.. code-block:: python

   engine = Querexfuzz(config_path='config.yml')
   engine = Querexfuzz(config_path='config.yml', fuzzy={'limit': 200})

Example ``config.yml``:

.. code-block:: yaml

   base_cols: [name, dept, salary, joined]
   date_fields: [joined]
   default_date_field: joined
   bang_field: name
   recent_field: joined
   fuzzy:
     fields: [name, dept]
     limit: 50
     score_col_name: score

----

Multiple DataFrames
-------------------

A single engine can be attached to multiple DataFrames. Each gets its own independent
fuzzy-matcher cache:

.. code-block:: python

   engine.attach_to(df_employees)
   engine.attach_to(df_contractors)

   df_employees.querex("# python")
   df_contractors.querex("# python")   # uses a separate cached matcher

If a DataFrame's contents change between queries, re-attach with ``mutable=True`` to
rebuild the fuzzy matcher on every call:

.. code-block:: python

   engine.attach_to(df, mutable=True)

----

Next steps
----------

- :doc:`query-syntax` — full reference for every clause
- :doc:`api` — complete API documentation
