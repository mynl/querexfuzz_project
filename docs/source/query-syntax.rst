Query Syntax
============

A querexfuzz query is a single string made up of optional clauses. **Clauses are
order-sensitive** and must appear in the sequence shown below. All clauses are optional;
an empty string returns all base columns for all rows.

.. code-block:: text

   [verbose] [recent] [top N | bottom N] [select ...]
   [field ~ regex | ! regex] [where expr] [order by cols]
   [@[field] date_spec] [# fuzzy_term]

The fuzzy clause (``#``) must always be **last**.

----

.. contents:: Clauses
   :local:
   :depth: 1

----

Flags: ``verbose`` and ``recent``
----------------------------------

``verbose``
   Prints query details to the logger. No effect on the returned DataFrame.

``recent``
   Sorts results by the configured ``recent_field`` (most recent first) after all
   filters are applied. Equivalent to ``order by -<recent_field>`` but uses the
   engine's configured default rather than naming a column explicitly.

.. code-block:: python

   df.querex("verbose recent top 5")

----

``top N`` / ``bottom N``
------------------------

Limits the result to the first or last *N* rows **after** sorting and filtering.

.. code-block:: python

   df.querex("top 10")
   df.querex("bottom 5")
   df.querex("recent top 3")      # 3 most recent
   df.querex("top 2 # python")    # 2 best fuzzy matches

----

``select``
----------

Controls which columns are returned. When no ``select`` clause is given, the engine
returns the configured ``base_cols``.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Syntax
     - Meaning
   * - *(omitted)*
     - ``base_cols`` (the configured default set)
   * - ``select *``
     - ``base_cols``
   * - ``select **``
     - All columns in the DataFrame
   * - ``select a, b, c``
     - Named columns only
   * - ``select *, a``
     - ``base_cols`` plus column ``a``
   * - ``select *, -a``
     - ``base_cols`` minus column ``a``
   * - ``select *, !a``
     - Same as ``select *, -a`` (``-`` and ``!`` are equivalent for exclusion)
   * - ``select **, -a``
     - All columns minus ``a``

.. code-block:: python

   df.querex("select name, salary")
   df.querex("select *, -salary")
   df.querex("where age > 30 select name, dept, salary")

----

Regex: ``!`` and ``~``
-----------------------

Filters rows using a regular expression. Matching is **case-insensitive**.

``! pattern``
   Applies the regex to the configured ``bang_field`` (the default regex target column).

``field ~ pattern``
   Applies the regex to the named column.

Patterns can be plain text or enclosed in slashes (``/pattern/``); both forms are
equivalent.

Multiple regex clauses can be chained with ``and``:

.. code-block:: python

   df.querex("! python")                   # bang_field contains 'python'
   df.querex("! /^Alice/")                 # bang_field starts with 'Alice'
   df.querex("dept ~ ^Eng")                # dept starts with 'Eng'
   df.querex("! python and dept ~ Eng")    # both conditions

----

``where``
---------

SQL-style row filter, passed directly to :meth:`pandas.DataFrame.query`. Supports all
operators that ``df.query()`` accepts.

Supported comparison operators: ``==``, ``!=``, ``>``, ``>=``, ``<``, ``<=``

Logical operators: ``and``, ``or``

Parentheses for grouping are supported:

.. code-block:: python

   df.querex("where salary > 90000")
   df.querex("where dept == 'Engineering' and salary >= 95000")
   df.querex("where dept == 'Engineering' or dept == 'Finance'")
   df.querex("where (dept == 'Engineering' or dept == 'Finance') and salary > 85000")

String values must be quoted (single or double quotes).

----

``order by`` / ``sort by``
--------------------------

Sorts the result by one or more columns. ``sort by`` is an alias for ``order by``.

Prefix a column name with ``-`` for descending order:

.. code-block:: python

   df.querex("order by salary")            # ascending
   df.querex("order by -salary")           # descending
   df.querex("sort by dept, -salary")      # dept asc, then salary desc
   df.querex("order by dept, name")        # multiple columns

When a fuzzy ``#`` clause is present and no explicit ``order by`` is given, results are
automatically sorted by fuzzy score descending.

----

``@`` Date range
----------------

Filters rows whose date column falls within a relative date window. Uses the configured
``default_date_field`` unless a field name is specified.

**Syntax:** ``@[field] unit[-start[:end]]``

**Date units:**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Unit
     - Meaning
   * - ``d``
     - Days
   * - ``w``
     - Weeks
   * - ``m``
     - Months (calendar months via ``dateutil.relativedelta``)
   * - ``q``
     - Quarters (3-month blocks)
   * - ``y``
     - Years
   * - ``h``
     - Hours
   * - ``c``
     - Calendar years (Jan 1 – Dec 31 boundaries)

**Forms:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Form
     - Meaning
   * - ``@m``
     - Last 1 month (unit only → start defaults to 1, end = now)
   * - ``@m-3``
     - Last 3 months
   * - ``@y-2``
     - Last 2 years
   * - ``@y-5:1``
     - Between 5 years ago and 1 year ago
   * - ``@joined y-2``
     - Last 2 years on column ``joined`` (explicit field)

.. code-block:: python

   df.querex("@d-30")                 # last 30 days
   df.querex("@m-3")                  # last 3 calendar months
   df.querex("@y-1")                  # last year
   df.querex("@y-5:1")                # 5 years ago to 1 year ago
   df.querex("@joined y-2")           # named field
   df.querex("@c-1")                  # last calendar year (Jan 1 to Dec 31)

Multiple date clauses can be chained (one per field):

.. code-block:: python

   df.querex("@created y-1 @modified m-3")

----

``#`` Fuzzy search
------------------

Performs a fuzzy search across the configured ``fuzzy.fields`` using
`skimmatch <https://github.com/mynl/skimmatch>`_. **Must be the last clause.**

Results include a score column (default name ``score``) and are sorted by score
descending unless an explicit ``order by`` overrides this.

The fuzzy matcher is built once on the first call per DataFrame and cached for the
lifetime of the engine — subsequent calls reuse it at near-zero cost.

When combined with pre-filter clauses (``where``, regex, date), the matcher still runs
over the full DataFrame and the results are intersected with the filtered rows using
5× over-fetch:

.. code-block:: python

   df.querex("# python")                        # fuzzy over all rows
   df.querex("top 5 # engineering")             # top 5 matches
   df.querex("where dept == 'Engineering' # python")  # filter then fuzzy

----

Combining clauses
-----------------

All clauses can be combined freely, subject to the ordering constraint:

.. code-block:: python

   # Most recently hired Engineers, showing name and salary
   df.querex("recent top 5 where dept == 'Engineering' select name, salary")

   # Hired in last year, sorted by salary descending, fuzzy on 'python'
   df.querex("order by -salary @y-1 # python")

   # Complex: verbose, recent 3, filter, date, select, fuzzy
   df.querex("verbose recent top 3 where salary > 80000 @y-2 select name, dept # alice")
