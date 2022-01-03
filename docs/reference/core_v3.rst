-----------
Core API v3
-----------

.. py:currentmodule:: imageio.core.v3_api

.. note::
    For migration instructions from the v2 API check :ref:`our migration guide
    <migration_from_v2>`.

These functions represent imageio's main interface for the user. They
provide a common API to read and write image data for a large
variety of formats. All read and write functions accept keyword
arguments, which are passed on to the backend that does the actual work.

Migrating from v2
-----------------