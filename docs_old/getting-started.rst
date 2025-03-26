***************
Getting Started
***************


Python Environment
==================

It is highly recommended users create a new Python environment with either `venv <https://docs.python.org/3/library/venv.html>`_ or `Anaconda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_. The pipeline supports Python versions 3.11 or newer; older versions of Python may work but have not been tested. Once configured, activate the new Python environment.


CRDS
====

For now, we rely on the `Calibration Reference Data System <https://hst-crds.stsci.edu/static/users_guide/index.html>`_ (CRDS) API used by Space Telescope Science Intitute (STScI) to retrieve calibration data products necessary for data reduction. The CRDS defines a set of `rules <https://github.com/oirlab/liger-iris-crds-cache/blob/master/mappings/ligeriri/liger_iris_iris_flat_0001.rmap>`_ on how to choose the right calibraiton file(s) given an observation's metadata. The CRDS will eventually be replaced with the appropriate interfaces to Keck and TMT, but we aim to maintain a minimal interface common to both facilities. Below we download and install the CRDS and cache tailored for Liger & IRIS:

.. code-block:: bash

    git clone https://github.com/oirlab/liger_iris_crds
    git clone https://github.com/oirlab/liger-iris-crds-cache $HOME/crds_cache
    cd liger_iris_crds
    pip install .

We then must define several environment variables so that ``CRDS`` will use the local cache instead of trying to connect to the JWST instance:

.. code-block:: bash

    source setup_local_crds.sh


Compilation of Readout Code
===========================

`liger_iris_pipeline` also includes the `liger_iris_readout` C library wrapped with `Cython`. Therefore we require `GCC`, `autotools` and `libcfitsio` to compile the Python extension.

In Debian/Ubuntu, the `cfitsio` headers are installed under a prefix, so we need to include that folder in the search path:

.. code-block:: bash

    export C_INCLUDE_PATH=/usr/include/cfitsio/

In macOS, `cfitsio` can be installed with a package manager such as `HomeBrew <https://brew.sh/>`_. Once installed, the path to `cfitsio` can be found with ``brew info cfitsio``.


Development Install
===================

**Recommended**: Fork the repository `liger_iris_pipeline <https://github.com/oirlab/liger_iris_pipeline>`_ under your account on GitHub, then clone your fork on your machine.

Initialize the `git` submodule for the `liger_iris_readout` C library:

.. code-block:: bash

    cd liger_iris_pipeline
    git submodule init
    git submodule update

Then enter the root folder and create a development install with:

.. code-block:: bash

  pip install -e .

The option `-e` will use the cloned repo's code directly as the source code (i.e. it will **not** be installed to site-packages/).

Lastly, we manually add the scripts to the path:

.. code-block:: bash

    export PATH=$(pwd)/scripts/:$PATH


Run the unit tests
==================

Some of the unit tests of ``liger_iris_pipeline`` are Jupyter Notebooks and they need the `nbval py.test plugin <https://github.com/computationalmodelling/nbval>`_ to be executed. Once ``py.test`` and ``nbval`` are installed, execute from the root of the package:

.. code-block:: bash

    python setup.py test
