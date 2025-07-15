===================
Steps and Pipelines
===================

End-to-end processing of Liger and IRIS data is divided into 3 main stages and largely resembles the JWST nomenclature (for now). The base class for individual data processing steps and collections of steps (pipelines) is :py:class:`~stpipe.base_step.Step`. The base-pipeline object :py:class:`~stpipe.pipeline.base_pipeline.Pipeline` also inherits from :py:class:`~stpipe.base_step.Step`. The Liger IRIS DRS declares :py:class:`~liger_iris_pipeline.base_step.LigerIRISStep` and :py:class:`~liger_iris_pipeline.pipeline.base_pipeline.LigerIRISPipeline` as base classes for steps and pipelines, respectively. Below is a summary of the type inheritance:

.. inheritance-diagram:: liger_iris_pipeline.base_step.LigerIRISStep
   :parts: 1

.. inheritance-diagram:: liger_iris_pipeline.pipeline.base_pipeline.LigerIRISPipeline
   :parts: 1


Specification (spec)
--------------------

Each step is specified by a class attribute called ``spec`` delcared with a single Python triple-quoted string. :py:class:`~liger_iris_pipeline.base_step.LigerIRISStep` specifies a subset of common options that are available to all steps. When a new step inherits from a parent step class, it inherits the parent's ``spec`` attribute. Once a step is constructed, the options from ``spec`` are available as instance attributes (e.g. ``step_instance.output_dir``).

**List of attributes available to all steps:**

* ``skip (bool)``: If ``True``, the step is skipped. Default is False.
* ``output_dir (str | None)``: The directory to save the result(s) to. See :py:meth:`~liger_iris_pipeline.step.base_step.LigerIRISStepStep._make_output_path` for more information.


The base ``Step`` class from ``stpipe`` is a rather sophisticated Python object with functionality not expeceted to be used in the Liger IRIS DRS. Therefore there are several attributes and methods that are dropped from the base class in order to simplify the development of the Liger IRIS DRS. See :py:attr:`~liger_iris_pipeline.base_step.LigerIRISStep.exclude_spec` for more information.


Configuration Files
-------------------

Like steps, pipelines are specify a class attribute called ``spec`` which can also be configured with configuration files. Pipeline configuration files may also specify any configuration for the individual steps in the `[steps]` section. Here, the key is the alias of the step and the values are additional options to pass to the step when it is constructed. Optionally, a separate configuration file can be specified. Additional will then override any present in the config file. Like steps, unspecified options inherit default settings (``spec`` attribute). Eventually, pipeline config files may use YAML syntax.

**Step Configuration File**

.. code-block:: ini

    class = "liger_iris_pipeline.ImagerStage2Pipeline"
    skip = False
    save_results = True
    output_dir = '/my/output/dir/'


**Pipeline Configuration File**

.. code-block:: ini

    class = "liger_iris_pipeline.ImagerStage2Pipeline"
    save_results = True

        [steps]
            [[dark_sub]]
                config_file = "dark_config.cfg"
                save_results = True
            [[flat_field]]
            [[sky_sub]]
            [[assign_wcs]]
                skip = False


Implement new step
------------------

To implement a new step, create a new class that inherits from :py:class:`~liger_iris_pipeline.base_step.LigerIRISStep`. The new class should implement the following method:

``process(self, input : LigerIRISDataModel | str) -> LigerIRISDataModel``:
    The main processing method. It should take in a single input argument which is either a filename (full path) or datamodel. ``process`` should return a datamodel.

The new class should also define the following class attributes:

``spec (str)``:
    A triple-quoted Python string that specifies the options for the step (see below).

``reference_file_types (list[str])``:
    A list of reference file types used by this step. This is used to query CRDS for the appropriate reference files before any processing is performed.

``class_alias (str)``:
    A string that specifies the class alias for pipeline attribute access and pipeline-level configuration for individual steps.

See `the dark subtraction step <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/dark_subtraction/dark_step.py>`_ for an example of a simple step object that calls out to CRDS.


Implement new pipeline
----------------------

Pipelines inherit from the base ``Step`` object, so implementing a new pipeline is similar to implement a new step. A pipeline must implement the following methods:

``process(self, input) -> list[LigerIRISDataModel]``:
    The main processing method. Pipelines also take in a single input argument, but this argument can also now be an association file.

``process_exposure_product(self, exp_product : dict) -> list[LigerIRISDataModel]``:
    This method processes a single exposure.

The new class should also define the ``spec`` and ``class_alias`` attributes (see above). Additionally, a pipeline must define the following attributes:

``step_defs (dict[str, type[LigerIRISStep])``
    This is a Python dictionary that specifies the individual steps to run on the input data. These steps are available within the pipeline as ``pipeline.<step_alias>`` (e.g. ``pipeline.dark_sub``). Step-specific attributes (in this case dark subtraction step) can be accessed with ``pipeline.dark_sub.<attribute>``.

``default_association (type[LigerIRISAssociation])``
    Associations are used in pipelines to group multiple data products together. For example, an association may specificy a set of exposures which are first to be coadded into a single frame before further processing. Currently, associations are crudely implemented for Liger and IRIS until more rules for associating datasets are specified. Associations may not be used in future versions of the DRS. See :mod:`~liger_iris_pipeline.associations` for more information.

    Currently, when an input is passed to ``pipeline.process``, it is converted into an association object specified by the ``default_association`` attribute.


See `the stage 2 imager pipeline <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/pipeline/imager_stage2.py>`_ for an example of a pipeline object.