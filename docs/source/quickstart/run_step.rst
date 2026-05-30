=============
Running Steps
=============

The following examples demonstrate how to run a single step within the DRP.
Files are retrieved from the shared Liger/IRIS Google Drive data folder.

For more information, see stpipe's documentation on `Running Steps and Pipelines <https://stpipe.readthedocs.io/en/latest/call_via_call.html>`_.

Run a Step
----------

This example subtracts a dark frame from a level 0 input frame (rate map) using the `DarkSubtractionStep`. A dark calibration is needed for this step and for now is retrieved from the Google Drive testing data and . Calibrations are typically associated and retrieved automatically by the DRP (see :doc:`calibrations <../calibrations/calibrations>` and :doc:`Step Design <../development/steps>`). Below we show the different methods for associated calibrations through a step's configuration.

.. code-block:: python

    # Imports
    from liger_iris_pipeline.dark_subtraction.dark_step import DarkSubtractionStep
    from liger_iris_pipeline.utils import download_gdrive_file
    from liger_iris_pipeline import datamodels

    # Input files
    sci_path = download_gdrive_file('HB.20231006.00000.00_rate-TELLURICS-FIB1.fits')
    dark_path = download_gdrive_file('HB.20260212.00000.00.mastercal-dark.001.fits')
    dark_model = datamodels.open(dark_path)

    # Use default behavior
    dark_step = DarkSubtractionStep()
    model_result = dark_step.run(sci_path, dark=dark_model) # or dark=dark_path


liger_iris_pipeline supports stpipe's ``Step.call()`` and ``step = Step(); step.run()`` interfaces.

The associated dark calibration can be found with:

.. code-block:: python

    # Returns dictionary with calibration information
    dark_info = model_result.get_calibration_from_role('dark')


Step Configuration
------------------

Steps are configurable with different parameters for data processing to fully specify the data processing behavior, including step parameters, calibrations, and logging behavior. Step arguments and calibrations can be set in several ways.


Python Interface
++++++++++++++++

Passed in as keyword arguments to the class constructor:

.. code-block:: python

    dark_step = DarkSubtractionStep(
        dark=dark_path,
        output_dir='/path/to/output/dir/',
    )
    model_result = dark_step.run(sci_path)

Passed in as keyword arguments to the class constructor or ``run`` method, set directly as class attributes:

.. code-block:: python

    dark_step = DarkSubtractionStep()
    model_result = dark_step.run(
        sci_path,
        dark=dark_path, save_result=True, output_dir='/path/to/output/dir/'
    )

Configuration Files
+++++++++++++++++++

Step configuration files are YAML files that specify step behavior. Anything not set within the configuration file will be set to the default value specified in the step's ``spec`` string.

.. code-block:: yaml

    %YAML 1.2
    ---

    class: DarkSubtractionStep

    parameters:
        save_result: True
        output_dir: /path/to/output/dir/
        dark: /path/to/dark_calibration.fits

The step can be initialized with a path to the configuration file, or with a dictionary containing the configuration, both using the ``config`` kwarg.

.. code-block:: python

    dark_step = DarkSubtractionStep(config='/path/to/config.yaml')
    model_result = dark_step.run(sci_path)


Optionally, the class name can be added to the top of the config file to specify which step the configuration is for. This is useful for invoking steps from configuration files alone and will be used for automation (*under development*).

Parameters
~~~~~~~~~~

All step parameters are specified through a step's ``spec`` string. All steps use a set of common parameters defined within stpipe's core Step class and `LigerIRISStep`:

pre_hooks          = list(default=list())        # List of Step classes to run before step
post_hooks         = list(default=list())        # List of Step classes to run after step
output_file        = output_file(default=None)   # File to save output to.
output_dir         = string(default=None)        # Directory path for output files (created if nonexistent)
output_ext         = string()                    # Default type of output
output_use_model   = boolean(default=False)      # When saving use ``model.meta.filename``
output_use_index   = boolean(default=True)       # Append index.
save_results       = boolean(default=False)      # Force save results
skip               = boolean(default=False)      # Skip this step
suffix             = string(default=None)        # Default suffix for output files
search_output_file = boolean(default=True)       # Use outputfile define in parent step
input_dir          = string(default=None)        # Input directory
output_ext         = string(default='.fits')     # Output file extension


Steps can also define additional parameters to fully specify behavior.

Logging
~~~~~~~

liger_iris_pipelines adopts stpipe's logging infrastructure.

See `stpipe's logging documentation <https://stpipe.readthedocs.io/en/latest/user_logging.html>`_ for more information.