# import copy
# from collections import OrderedDict
# from collections.abc import Sequence
# import os.path as op
# import re
# import logging

# import numpy as np
# from astropy.io import fits
# from asdf import AsdfFile

# from jwst.associations import load_asn
# from stdatamodels.jwst.datamodels.util import is_association
# from stdatamodels import properties

# from .model_base import LigerIRISDataModel
# from .utils import open as datamodel_open

# __all__ = ['LigerIRISModelContainer']

# _ONE_MB = 1 << 20
# RECOGNIZED_MEMBER_FIELDS = ['group_id']

# # Configure logging
# logger = logging.getLogger(__name__)
# logger.addHandler(logging.NullHandler())


# class LigerIRISModelContainer(LigerIRISDataModel, Sequence):
#     """
#     A list-like container for storing `LigerIRISDataModel`'s.

#     Args:
#     init:
#     - file path, list of DataModels, or None
#     - file path: initialize from an association table
#     - list: a list of DataModels of any type
#     - None: initializes an empty `ModelContainer` instance, to which DataModels can be added via the ``append()`` method.
#     asn_exptypes (str): list of exposure types from the asn file to read into the ModelContainer, if None read all the given files.
#     asn_n_members (int): Open only the first N qualifying members.
#     iscopy (bool): Presume this model is a copy. Members will not be closed when the model is closed/garbage-collected.
#     """
#     schema_url = None

#     def __init__(self, init=None, asn_exptypes=None, asn_n_members=None,
#                  iscopy=False, **kwargs):

#         self._models = []
#         self._iscopy = iscopy
#         super().__init__(init=None, **kwargs)
#         self.asn_exptypes = asn_exptypes
#         self.asn_n_members = asn_n_members
#         self.asn_table = {}
#         self.asn_table_name = None
#         self.asn_pool_name = None
#         self.asn_file_path = None

#         self._memmap = kwargs.get("memmap", False)
#         self._return_open = kwargs.get('return_open', True)
#         self._save_open = kwargs.get('save_open', True)
        

#         if init is None:
#             # Don't populate the container with models
#             pass
#         elif isinstance(init, fits.HDUList):
#             if self._save_open:
#                 model = [datamodel_open(init, memmap=self._memmap)]
#             else:
#                 model = init._file.name
#                 init.close()
#             self._models.append(model)
#         elif isinstance(init, list):
#             if all(isinstance(x, (str, fits.HDUList, LigerIRISDataModel)) for x in init):
#                 if self._save_open:
#                     init = [datamodel_open(m, memmap=self._memmap) for m in init]
#             else:
#                 raise TypeError("list must contain items that can be opened "
#                                 "with liger_iris_pipeline.datamodels.open()")
#             self._models = init
#         elif isinstance(init, self.__class__):
#             instance = copy.deepcopy(init._instance)
#             self._schema = init._schema
#             self._shape = init._shape
#             self._asdf = AsdfFile(instance)
#             self._instance = instance
#             self._ctx = self
#             self._models = init._models
#             self._iscopy = True
#         elif is_association(init):
#             self.from_asn(init)
#         elif isinstance(init, str):
#             init_from_asn = self.read_asn(init)
#             self.asn_file_path = init
#             self.from_asn(init_from_asn)
#         else:
#             raise TypeError('Input {0!r} is not a list of LigerIRISDataModels or '
#                             'an ASN file'.format(init))

#     def __len__(self):
#         return len(self._models)

#     def __getitem__(self, index):
#         m = self._models[index]
#         if not isinstance(m, LigerIRISDataModel) and self._return_open:
#             m = datamodel_open(m, memmap=self._memmap)
#         return m

#     def __setitem__(self, index, model):
#         self._models[index] = model

#     def __delitem__(self, index):
#         del self._models[index]

#     def __iter__(self):
#         for model in self._models:
#             if not isinstance(model, LigerIRISDataModel) and self._return_open:
#                 model = datamodel_open(model, memmap=self._memmap)
#             yield model

#     def insert(self, index, model):
#         self._models.insert(index, model)

#     def append(self, model):
#         self._models.append(model)

#     def extend(self, model):
#         self._models.extend(model)

#     def pop(self, index=-1):
#         self._models.pop(index)

#     def copy(self, memo=None):
#         """
#         Returns a deep copy of the models in this model container.
#         """
#         result = self.__class__(
#             init=None,
#             pass_invalid_values=self._pass_invalid_values,
#             strict_validation=self._strict_validation
#         )
#         instance = copy.deepcopy(self._instance, memo=memo)
#         result._asdf = AsdfFile(instance)
#         result._instance = instance
#         result._iscopy = self._iscopy
#         result._schema = self._schema
#         result._ctx = result
#         for m in self._models:
#             if isinstance(m, LigerIRISDataModel):
#                 result.append(m.copy())
#             else:
#                 result.append(m)
#         return result

#     @staticmethod
#     def read_asn(filepath):
#         """
#         Load fits files from a Liger or IRIS association file.

#         Parameters:
#         filepath (str): The path to an association file.
#         """

#         filepath = op.abspath(op.expanduser(op.expandvars(filepath)))
#         try:
#             with open(filepath) as asn_file:
#                 asn_data = load_asn(asn_file)
#         except AssociationNotValidError as e:
#             raise IOError("Cannot read ASN file.") from e
#         return asn_data

#     def from_asn(self, asn_data):
#         """
#         Load fits files from a JWST association file.

#         Parameters
#         ----------
#         asn_data : ~jwst.associations.Association
#             An association dictionary
#         """
#         # match the asn_exptypes to the exptype in the association and retain
#         # only those file that match, as a list, if asn_exptypes is set to none
#         # grab all the files
#         if self.asn_exptypes:
#             infiles = []
#             logger.debug('Filtering datasets based on allowed exptypes {}:'
#                          .format(self.asn_exptypes))
#             for member in asn_data['products'][0]['members']:
#                 if any([x for x in self.asn_exptypes if re.match(member['exptype'],
#                                                                  x, re.IGNORECASE)]):
#                     infiles.append(member)
#                     logger.debug('Files accepted for processing {}:'.format(member['expname']))
#         else:
#             infiles = [member for member
#                        in asn_data['products'][0]['members']]

#         if self.asn_file_path:
#             asn_dir = op.dirname(self.asn_file_path)
#         else:
#             asn_dir = ''

#         # Only handle the specified number of members.
#         if self.asn_n_members:
#             sublist = infiles[:self.asn_n_members]
#         else:
#             sublist = infiles
#         try:
#             for member in sublist:
#                 filepath = op.join(asn_dir, member['expname'])
#                 update_model = any(attr in member for attr in RECOGNIZED_MEMBER_FIELDS)
#                 if update_model or self._save_open:
#                     m = datamodel_open(filepath, memmap=self._memmap)
#                     m.meta.asn.exptype = member['exptype']
#                     for attr, val in member.items():
#                         if attr in RECOGNIZED_MEMBER_FIELDS:
#                             if attr == 'tweakreg_catalog':
#                                 if val.strip():
#                                     val = op.join(asn_dir, val)
#                                 else:
#                                     val = None

#                             setattr(m.meta, attr, val)

#                     if not self._save_open:
#                         m.save(filepath, overwrite=True)
#                         m.close()
#                 else:
#                     m = filepath

#                 self._models.append(m)

#         except IOError:
#             self.close()
#             raise

#         # Pull the whole association table into meta.asn_table
#         self.meta.asn_table = {}
#         properties.merge_tree(
#             self.meta.asn_table._instance, asn_data
#         )

#         if self.asn_file_path is not None:
#             self.asn_table_name = op.basename(self.asn_file_path)
#             self.asn_pool_name = asn_data['asn_pool']
#             for model in self:
#                 try:
#                     model.meta.asn.table_name = self.asn_table_name
#                     model.meta.asn.pool_name = self.asn_pool_name
#                 except AttributeError:
#                     pass

#     def save(self,
#              path=None,
#              dir_path=None,
#              save_model_func=None,
#              **kwargs):
#         """
#         Write out models in container to FITS or ASDF.

#         Parameters
#         ----------
#         path : str or func or None
#             - If None, the `meta.filename` is used for each model.
#             - If a string, the string is used as a root and an index is
#               appended.
#             - If a function, the function takes the two arguments:
#               the value of model.meta.filename and the
#               `idx` index, returning constructed file name.

#         dir_path : str
#             Directory to write out files.  Defaults to current working dir.
#             If directory does not exist, it creates it.  Filenames are pulled
#             from `.meta.filename` of each datamodel in the container.

#         save_model_func: func or None
#             Alternate function to save each model instead of
#             the models `save` method. Takes one argument, the model,
#             and keyword argument `idx` for an index.

#         Returns
#         -------
#         output_paths: [str[, ...]]
#             List of output file paths of where the models were saved.
#         """
#         output_paths = []
#         if path is None:
#             def path(filename, idx=None):
#                 return filename
#         elif not callable(path):
#             path = make_file_with_index

#         for idx, model in enumerate(self):
#             if len(self) <= 1:
#                 idx = None
#             if save_model_func is None:
#                 outpath, filename = op.split(
#                     path(model.meta.filename, idx=idx)
#                 )
#                 if dir_path:
#                     outpath = dir_path
#                 save_path = op.join(outpath, filename)
#                 try:
#                     output_paths.append(
#                         model.save(save_path, **kwargs)
#                     )
#                 except IOError as err:
#                     raise err

#             else:
#                 output_paths.append(save_model_func(model, idx=idx))
#         return output_paths

#     @property
#     def models_grouped(self):
#         """
#         Returns a list of a list of datamodels grouped by exposure.
#         Assign a grouping ID by exposure, if not already assigned.

#         If ``model.meta.group_id`` does not exist or it is `None`, then data
#         from different detectors of the same exposure will be assigned the
#         same group ID, which allows grouping by exposure in the ``tweakreg`` and
#         ``skymatch`` steps. The following metadata is used when
#         determining grouping:

#         meta.observation.program_number
#         meta.observation.observation_number
#         meta.observation.visit_number
#         meta.observation.visit_group
#         meta.observation.sequence_id
#         meta.observation.activity_id
#         meta.observation.exposure_number

#         If a model already has ``model.meta.group_id`` set, that value will be
#         used for grouping.
#         """
#         unique_exposure_parameters = [
#             'program_number',
#             'observation_number',
#             'visit_number',
#             'visit_group',
#             'sequence_id',
#             'activity_id',
#             'exposure_number'
#         ]

#         group_dict = OrderedDict()
#         for i, model in enumerate(self._models):
#             params = []
#             if not self._save_open:
#                 model = datamodel_open(model, memmap=self._memmap)

#             if (hasattr(model.meta, 'group_id') and
#                         model.meta.group_id not in [None, '']):
#                 group_id = model.meta.group_id

#             else:
#                 for param in unique_exposure_parameters:
#                     params.append(getattr(model.meta.observation, param))
#                 try:
#                     group_id = (
#                         'jw' + '_'.join(
#                             [
#                                 ''.join(params[:3]),
#                                 ''.join(params[3:6]),
#                                 params[6],
#                             ]
#                         )
#                     )
#                     model.meta.group_id = group_id
#                 except TypeError:
#                     model.meta.group_id = 'exposure{0:04d}'.format(i + 1)

#                 group_id = model.meta.group_id

#             if not self._save_open and not self._return_open:
#                 model.close()
#                 model = self._models[i]

#             if group_id in group_dict:
#                 group_dict[group_id].append(model)
#             else:
#                 group_dict[group_id] = [model]

#         return group_dict.values()

#     @property
#     def group_names(self):
#         """
#         Return list of names for the JwstDataModel groups by exposure.
#         """
#         result = []
#         for group in self.models_grouped:
#             result.append(group[0].meta.group_id)
#         return result

#     def close(self):
#         """Close all datamodels."""
#         if not self._iscopy:
#             for model in self._models:
#                 if isinstance(model, LigerIRISDataModel):
#                     model.close()

#     @property
#     def crds_observatory(self):
#         """
#         Get the CRDS observatory for this container.  Used when selecting
#         step/pipeline parameter files when the container is a pipeline input.

#         Returns:
#         str
#         """
#         return "ligeriri"

#     def get_crds_parameters(self):
#         """
#         Get CRDS parameters for this container.
#         Used when selecting step/pipeline parameter files when the container is a pipeline input.

#         Returns:
#         dict
#         """
#         with self._open_first_science_exposure() as model:
#             return model.get_crds_parameters()

#     def _open_first_science_exposure(self):
#         """
#         Open first model with exptype SCIENCE, or the first model if none exists.

#         Returns:
#         LigerIRISDataModel
#         """
#         for exposure in self.meta.asn_table.products[0].members:
#             if exposure.exptype.upper() == "SCIENCE":
#                 first_exposure = exposure.expname
#                 break
#         else:
#             first_exposure = self.meta.asn_table.products[0].members[0].expname

#         return datamodel_open(first_exposure)

#     def ind_asn_type(self, asn_exptype):
#         """
#         Determine the indices of models corresponding to ``asn_exptype``.

#         Parameters:
#         asn_exptype (str): Exposure type as defined in an association, e.g. "science".

#         Returns:
#         list: Indices of models in ModelContainer._models matching ``asn_exptype``.
#         """
#         ind = []
#         for i, model in enumerate(self._models):
#             if model.meta.asn.exptype.lower() == asn_exptype:
#                 ind.append(i)
#         return ind

#     def set_buffer(self, buffer_size, overlap=None):
#         """Set buffer size for scrolling section-by-section access.

#         Parameters:
#         ----------
#         buffer_size (float | None): Define size of buffer in MB for each section. If `None`, a default buffer size of 1MB will be used.
#         overlap (int | optional): Define the number of rows of overlaps between sections. If `None`, no overlap will be used.
#         """
#         self.overlap = 0 if overlap is None else overlap
#         self.grow = 0

#         with datamodel_open(self._models[0]) as model:
#             imrows, imcols = model.data.shape
#             data_item_size = model.data.itemsize
#             data_item_type = model.data.dtype
#             model.close()
#         del model
#         min_buffer_size = imcols * data_item_size

#         self.buffer_size = min_buffer_size if buffer_size is None else (buffer_size * _ONE_MB)

#         section_nrows = min(imrows, int(self.buffer_size // min_buffer_size))

#         if section_nrows == 0:
#             self.buffer_size = min_buffer_size
#             logger.warning("WARNING: Buffer size is too small to hold a single row."
#                            f"Increasing buffer size to {self.buffer_size / _ONE_MB}MB")
#             section_nrows = 1

#         nbr = section_nrows - self.overlap
#         nsec = (imrows - self.overlap) // nbr
#         if (imrows - self.overlap) % nbr > 0:
#             nsec += 1

#         self.n_sections = nsec
#         self.nbr = nbr
#         self.section_nrows = section_nrows
#         self.imrows = imrows
#         self.imcols = imcols
#         self.imtype = data_item_type

#     def get_sections(self):
#         """Iterator to return the sections from all members of the container."""

#         for k in range(self.n_sections):
#             e1 = k * self.nbr
#             e2 = e1 + self.section_nrows

#             if k == self.n_sections - 1:  # last section
#                 e2 = min(e2, self.imrows)
#                 e1 = min(e1, e2 - self.overlap - 1)

#             data_list = np.empty((len(self._models), e2 - e1, self.imcols),
#                                  dtype=self.imtype)
#             wht_list = np.empty((len(self._models), e2 - e1, self.imcols),
#                                 dtype=self.imtype)
#             for i, model in enumerate(self._models):
#                 model = datamodel_open(model, memmap=self._memmap)

#                 data_list[i, :, :] = model.data[e1:e2].copy()
#                 wht_list[i, :, :] = model.wht[e1:e2].copy()
#                 model.close()
#                 del model

#             yield (data_list, wht_list, (e1, e2))