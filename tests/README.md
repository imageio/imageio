In imageio all tests are contained in a single directory. There should
be one test module per plugin.

We aim for 100% test coverage for imageio.core, and over 90% for each plugin.

We use the excelent test.py package, use a hook to Travis for continuous 
integration, and to Coveralls for coverage reporting.

To run tests locally run:
    
    python make test unit
    python make test style

To show coverage locally, run:
    
    python make test cover
