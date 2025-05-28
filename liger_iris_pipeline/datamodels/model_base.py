import os
from pathlib import Path

from astropy.time import Time
from astropy.io import fits
from datetime import datetime
from stdatamodels import DataModel
from stdatamodels import fits_support

import warnings
from .._version import __version__

__all__ = ["LigerIRISDataModel"]


class LigerIRISDataModel(DataModel):
    """
    The base data model for Liger and IRIS data products.
    This class should not be instantiated on its own.
    """
    schema_url = "https://oirlab.github.io/schemas/LigerIRISDataModel.schema"
    

    def get_crds_parameters(self):
        """
        Collect the parameters used by CRDS to select references for this model.

        Returns:
            dict : the CRDS parameters
        """
        return {
            key: val
            for key, val in self.to_flat_dict(include_arrays=False).items()
            if isinstance(val, (str, int, float, complex, bool))
        }
    
    @staticmethod
    def get_sem_id(jd : float) -> str:
        t = Time(jd, format='jd')
        year = t.datetime.year
        month = t.datetime.month
        day = t.datetime.day
        sem = 'A' if (month < 8 or (month == 8 and day < 1)) else 'B'
        return f"{year}{sem}"


    def on_init(self, init):
        """
        Hook invoked by the base class before returning a newly created model instance.
        """
        # Set the filepath and filename
        if isinstance(init, str):
            self._filepath = os.path.abspath(init)
            self.meta.filename = os.path.basename(self._filepath)
        elif isinstance(init, fits.hdu.hdulist.HDUList):
            self._filepath = os.path.abspath(init.filename())
            self.meta.filename = os.path.basename(self._filepath)

        # Set the model type
        self.meta.model_type = self.__class__.__name__

        # Semester ID
        if self.meta.program.sem_id is None and self.meta.exposure.jd_start is not None:
            self.meta.program.sem_id = self.get_sem_id(self.meta.exposure.jd_start)


    def on_save(self):
        """
        Hook invoked by the base class before writing a model
        to a file (FITS or ASDF).
        """
        self.meta.drs_version = __version__
        self.meta.date_created = datetime.now().isoformat()
        self.meta.filename = os.path.basename(self._filepath)
        self.meta.model_type = self.__class__.__name__

        
    @property
    def crds_observatory(self):
        return "ligeriri"
    
    
    @staticmethod
    def _generate_filename(
        instrument : str,
        sem_id : str | None,
        program_number : str | None, obs_number : str | None,
        detector : str, level : int | str = 0,
        exp_num : int | str = '0001', exp_type : str = 'SCI', subarray_id : int | str | None = None,
        suffix : str | None = None
    ) -> str:
        """
        Generates a filename.

        Args:
            instrument (str): The instrument name.
            sem_id (str | None): The semester ID. Defaults to None.
            program_number (str | None): The program number. Defaults to None.
            obs_number (str | None): The observation number. Defaults to None.
            detector (str): The detector name.
            level (int | str): The data level.
            exp_num (int | str, optional): The exposure number. Defaults to '0001'.
            exp_type (str, optional): The exposure type. Defaults to 'SCI'.
            subarray_id (int | str, optional): The subarray ID. Defaults to None for IRIS. Liger does not use subarrays.
        """
        if sem_id is None:
            sem_id = LigerIRISDataModel.get_sem_id(Time.now().jd)
        if program_number is None:
           program_number = 'P001'
        if obs_number is None:
            obs_number = '001'
        if instrument.lower() == 'iris':
            instrument = 'IRIS'
        elif instrument.lower() == 'liger':
            instrument = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument}")
        if isinstance(exp_num, int):
            exp_num = str(exp_num).zfill(4)
        if isinstance(subarray_id, (int, str)):
            subarray_id = '-' + str(subarray_id).zfill(2)
        else:
            if instrument.lower() == 'iris':
                subarray_id = '-00'
            else:
                subarray_id = ''
        if suffix is None:
            suffix = ''
        else:
            suffix = '_' + suffix
        # NOTE: Do not include subarray in filename for now.
        subarray_id = ''
        return f"{sem_id}-{program_number}-{obs_number}_{instrument}_{detector.upper()}_{exp_type}_LVL{int(level)}_{exp_num}{subarray_id}{suffix}.fits"
    

    def generate_filename(self, suffix : str | None = None) -> str:
        """
        Generates a filename for this model instance.
        See LigerIRISDataModel._generate_filename() for details.
        """

        # Get semester ID
        if self.meta.program.sem_id is None:
            self.meta.program.sem_id = self.get_sem_id(self.meta.exposure.jd_start)

        return self._generate_filename(
            instrument=self.meta.instrument.name,
            sem_id=self.meta.program.sem_id, program_number=self.meta.program.program_number, obs_number=self.meta.program.obs_number,
            detector=self.meta.instrument.detector, exp_type=self.meta.exposure.exposure_type,
            level=self.meta.data_level, exp_num=self.meta.exposure.exposure_number, subarray_id=self.meta.subarray.id, suffix=suffix
        )
    

    def get_primary_array_name(self):
        return 'data'


    def save(
        self,
        filepath : str | None = None,
        filename : str | None = None,
        output_dir : str | None = None,
        suffix : str | None = None,
        **kwargs
    ) -> str:
        """
        Save the model to a file.

        Args:
            filepath (str, optional): The filepath to save to. Defaults to self._filepath.
            filename (str, optional): The filename to save to. Defaults to None.
            output_dir (str, optional): The directory to save to. Defaults to the directory of self._filepath, then os.getcwd().
            suffix (str, optional): The suffix to add to the filename. Defaults to None.
        """
        if filepath is not None:
            self._filepath = os.path.abspath(filepath)
        elif output_dir is not None and filename is not None:
            self._filepath = os.path.join(output_dir, filename)
        elif output_dir is not None and filename is None:
            filename = self.generate_filename(suffix=suffix)
            self._filepath = os.path.abspath(os.path.join(output_dir, filename))
        elif output_dir is None and filename is not None:
            self._filepath = os.path.abspath(os.path.join(os.getcwd(), filename))
        else:
            filename = self.generate_filename(suffix=suffix)
            self._filepath = os.path.abspath(os.path.join(os.getcwd(), filename))
        self.on_save()
        self.to_fits(**kwargs)
        return self._filepath
    

    def to_fits(self, **kwargs):
        """
        Write the model to a FITS file using self._filepath as the output_path.

        Args:
            **kwargs: Additional arguments to pass to the fits.writeto() function.
        """
        hdulist = fits_support.to_fits(self._instance, self._schema)
        if 'overwrite' not in kwargs:
            kwargs['overwrite'] = True
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Card is too long')
            if self._no_asdf_extension:
                if "ASDF" in hdulist:
                    del hdulist["ASDF"]
            hdulist.writeto(self._filepath, **kwargs)
    
    # def copy(self, memo=None):
    #     """
    #     Returns a deep copy of this model.
    #     """
    #     result = super().copy(memo=memo)
    #     return self.clone(result, self, deepcopy=True, memo=memo)