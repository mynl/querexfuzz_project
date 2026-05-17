API Reference
=============

.. contents::
   :local:
   :depth: 1

----

Public API
----------

These are the names exported by ``import querexfuzz``.

.. autofunction:: querexfuzz.querexfuzz_from_df

.. autofunction:: querexfuzz.querexfuzz_help

----

Querexfuzz class
----------------

.. autoclass:: querexfuzz.Querexfuzz
   :members:
   :undoc-members:
   :show-inheritance:

----

Configuration
-------------

.. autoclass:: querexfuzz.config.QuerexfuzzConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: querexfuzz.config.FuzzyConfig
   :members:
   :undoc-members:
   :show-inheritance:

----

Parser
------

.. autofunction:: querexfuzz.parser.parser

----

Engine
------

.. autofunction:: querexfuzz.engine.execute_query

.. autoclass:: querexfuzz.engine.QuerexfuzzConfigurationWarning
   :show-inheritance:

----

Date utilities
--------------

.. autofunction:: querexfuzz.dates.resolve_date_range
