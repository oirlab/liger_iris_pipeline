============
Installation
============


Python Environment
------------------

It is highly recommended users create a new Python environment with either `venv <https://docs.python.org/3/library/venv.html>`_ or `Anaconda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_. The pipeline supports Python versions 3.11 or newer; older versions of Python may work but have not been tested. Once configured, activate the new Python environment.


CRDS
----

For now, we rely on the `Calibration Reference Data System <https://hst-crds.stsci.edu/static/users_guide/index.html>`_ (CRDS) API used by Space Telescope Science Intitute (STScI) to retrieve calibration data products necessary for data reduction. The CRDS defines a set of `rules <https://hst-crds.stsci.edu/static/users_guide/overview.html#crds-rules>`_ on how to choose the right calibraiton file(s) given an observation's metadata. The CRDS server-side aspects will eventually be replaced with the appropriate interfaces to Keck and TMT, but we aim to maintain a minimal interface common to both facilities. Below we download and install the CRDS and cache tailored for Liger and IRIS. Note the CRDS cache is not a Python package itself, and is downloaded to the user's home directory.

.. code-block:: bash

    git clone https://github.com/oirlab/liger_iris_crds
    git clone https://github.com/oirlab/liger-iris-crds-cache $HOME/crds_cache
    cd liger_iris_crds
    pip install .


We then define environment variables required by ``CRDS``. Specifically, we will use the local cache instead of trying to connect to the JWST instance:

.. code-block:: bash

    source setup_local_crds.sh


Development Install
-------------------

**Recommended**: Fork the repository `liger_iris_pipeline <https://github.com/oirlab/liger_iris_pipeline>`_ under your account on GitHub, then clone your fork on your machine.

Enter the root folder and create a live installation with:

.. code-block:: bash

  pip install -e .


The ``-e`` option uses the cloned repository's code directly as the source, meaning it will not be installed into ``site-packages/``.


Run the unit tests (optional)
-----------------------------

First install the testing dependencies:

.. code-block:: bash

  pip install -e .[test]


.. code-block:: bash

  pytest -s liger_iris_pipeline/tests/