from stpipe import Pipeline
from .base_step import LigerIRISStep
from ..datamodels import LigerIRISDataModel

from ..utils.config_library import ConfigLibrary

from stpipe import config_parser

import logging

logger = logging.getLogger(__name__)

__all__ = [
    "LigerIRISPipeline"
]

class LigerIRISPipeline(Pipeline, LigerIRISStep):
    """
    Base class for all LigerIRIS Pipelines.
    """

    def _precache_references(self, input):
        """
        Precache all of the expected reference files before the Step's process method is called.
        Handles opening `input_file` as a model if it is a filename.

        Parameters
        ----------
        input
            The input file to prefetch references for.
        """
        pass
        # try:
        #     crds_parameters, observatory = self._get_crds_parameters(input_file)
        # except (ValueError, TypeError, OSError):
        #     logger.info("First argument %s does not appear to be a model", input_file)
        #     return

        # ovr_refs = {
        #     reftype: self.get_ref_override(reftype)
        #     for reftype in self.calibrations
        #     if self.get_ref_override(reftype) is not None
        # }

        # fetch_types = sorted(set(self.calibrations) - set(ovr_refs.keys()))

        # logger.info(
        #     "Prefetching reference files for dataset: %r reftypes = %r",
        #     self._get_filename(input_file),
        #     fetch_types,
        # )
        # crds_refs = crds_client.get_multiple_reference_paths(
        #     crds_parameters, fetch_types, observatory
        # )

        # ref_path_map = dict(list(crds_refs.items()) + list(ovr_refs.items()))

        # for reftype, refpath in sorted(ref_path_map.items()):
        #     how = "Override" if reftype in ovr_refs else "Prefetch"
        #     logger.info(
        #         "%s for %s reference file is '%s'.", how, reftype.upper(), refpath
        #     )
        #     crds_client.check_reference_open(refpath)

    @classmethod
    def get_config_from_reference(cls, dataset, disable=None, crds_observatory=None):
        """
        Retrieve pipeline parameters from the reference database.

        Parameters
        ----------
        cls : LigerIRISStep
            Either a class or instance of a class derived
            from ``Step``.
        dataset : AbstractDataModel or dict
            A model of the input file.  Metadata on this input file will
            be used by the CRDS "bestref" algorithm to obtain a reference
            file. If a dict, crds_observatory must be a non-None value.
        disable: bool or None
            Do not retrieve parameters from CRDS. If None, check global settings.
        crds_observatory : str
            Observatory name ('jwst' or 'roman').

        Returns
        -------
        step_parameters : configobj
            The parameters as retrieved from CRDS. If there is an issue, log as such
            and return an empty config obj.
        """
        # TODO: Call out to config library
        action = None
        with ConfigLibrary() as conf_lib:
           conf_lib.get_config()
        #breakpoint()
        #reftype = cls.get_config_reftype()
        #logger.debug("No %s reference files found.", reftype.upper())
        return config_parser.ConfigObj()
    
    def finalize_result(self, result, reference_files_used : list[tuple[str, str]] | None = None):
        """
        Update the result with the software version and reference files used.
        Implemented for compatibility with stpipe.

        Parameters
        ----------
        result
            The result to finalize.
        reference_files_used : list[tuple[str, str]] | None
            List of 2-tuples (reference file type, filename) used during processing.
        """
        pass
        #if isinstance(result, LigerIRISDataModel):
                # # Remove the step logs as they're captured by the pipeline log
                # for _, step in self.step_defs.items():
                #     if hasattr(result.cal_logs, step.class_alias):
                #         delattr(result.cal_logs, step.class_alias)

                #setattr(result.cal_logs, self.class_alias, self._log_records)