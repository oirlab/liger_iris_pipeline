============
Installation
============


Python Environment
------------------

It is highly recommended users create a new Python environment with either `venv <https://docs.python.org/3/library/venv.html>`_, `Anaconda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_, or `uv <https://docs.astral.sh/uv/pip/environments/>`_. The pipeline supports Python versions 3.12 or newer. Once configured, activate the new Python environment.

To create a uv environment specifically for the latest stable release of ``liger_iris_pipeline`` (in this example, called liger_iris)::

    uv venv liger_iris --python 3.13

This will create a fresh Python 3.13 environment in which you can install the ``liger_iris_pipeline`` package.

Once you have created your uv environment, activate it::

    source liger_iris/bin/activate


Development Install
-------------------

**Recommended**: Fork the repository `liger_iris_pipeline <https://github.com/oirlab/liger_iris_pipeline>`_ under your account on GitHub, then clone your fork on your machine.

Enter the root folder and create a live installation with:

.. code-block:: bash

  pip install -e .


The ``-e`` option uses the cloned repository's code directly as the source, meaning it will not be installed into ``site-packages/``.


Run the unit tests (optional)
-----------------------------

First install the testing dependencies. Quotes are needeed for some shells:

.. code-block:: bash

  pip install -e ".[test]"

Then run the tests with:

.. code-block:: bash

  pytest -s