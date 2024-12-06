
from functools import wraps
import warnings
import logging

from stpipe import Step
from . import datamodels
from . import __version__, __version_commit__

from jwst.lib.suffix import remove_suffix
from stpipe import crds_client

__all__ = [
    "LigerIRISStep"
]

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class LigerIRISStep(Step):

    spec = """
        output_ext = string(default='.fits')  # Output file type
    """


    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return datamodels.open(init, **kwargs)


    # def load_as_level2_asn(self, obj):
    #     """Load object as an association

    #     Loads the specified object into a Level2 association.
    #     If necessary, prepend `Step.input_dir` to all members.

    #     Parameters
    #     ----------
    #     obj : object
    #         Object to load as a Level2 association

    #     Returns
    #     -------
    #     association : jwst.associations.lib.rules_level2_base.DMSLevel2bBase
    #         Association
    #     """
    #     # Prevent circular import:
    #     from ..associations.load_as_asn import LoadAsLevel2Asn
    #     from ..associations.lib.update_path import update_key_value

    #     asn = LoadAsLevel2Asn.load(obj, basename=self.output_file)
    #     update_key_value(asn, 'expname', (), mod_func=self.make_input_path)
    #     return asn

    def finalize_result(self, result, reference_files_used):
        if isinstance(result, datamodels.LigerIRISDataModel):
            result.meta.calibration_software_revision = __version_commit__ or 'RELEASE'
            result.meta.calibration_software_version = __version__

            if len(reference_files_used) > 0:
                for ref_name, filename in reference_files_used:
                    if hasattr(result.meta.ref_file, ref_name):
                        getattr(result.meta.ref_file, ref_name).name = filename
                result.meta.ref_file.crds.sw_version = crds_client.get_svn_version()
                result.meta.ref_file.crds.context_used = crds_client.get_context_used(result.crds_observatory)
                if self.parent is None:
                    log.info(f"Results used CRDS context: {result.meta.ref_file.crds.context_used}")


    def remove_suffix(self, name):
        return remove_suffix(name)

    @wraps(Step.run)
    def run(self, *args, **kwargs):
        result = super().run(*args, **kwargs)
        if not self.parent:
            log.info(f"Results used liger_iris_pipeline version: {__version__}")
        return result

    @wraps(Step.__call__)
    def __call__(self, *args, **kwargs):
        if not self.parent:
            warnings.warn(
                "Step.__call__ is deprecated. It is equivalent to Step.run "
                "and is not recommended. See "
                "https://jwst-pipeline.readthedocs.io/en/latest/jwst/"
                "user_documentation/running_pipeline_python.html"
                "#advanced-use-pipeline-run-vs-pipeline-call for more details.",
                UserWarning
            )
        return super().__call__(*args, **kwargs)
    pass