from koa_middleware import LocalCalibrationDB
from koa_middleware.selector_base import CalibrationSelector

import os

__all__ = [
    'LigerCalibrationSelector',
    'DQSelector',
    'SaturationSelector',
    'DarkSelector',
    'BiasSelector',
    'ReadNoiseSelector',
    'NonlinearCorrectionSelector',
    'DetectorFlatSelector',
    'GainSelector',
    'WavelengthSolutionSelector',
    'DistortionSelector',
]

class LigerCalibrationSelector(CalibrationSelector):
    """
    Base selector for Liger calibrations.
    Implements common selection logic based on origin, version, and master calibration status
    """

    def __init__(self, origin : str = "ANY", cal_version : str | None = 'LATEST', master_cal : bool | str | None = None, **kwargs):
        """
        Initialize the selector with optional filtering parameters.

        Parameters
        ----------
        origin : str, optional
            The origin to filter by. Can be "ANY", "LOCAL", or "REMOTE". Default is "ANY".
        cal_version : str, optional
            The calibration version to filter by. Can be a specific version string (e.g., "001"), "ANY", "LATEST", or a negative integer string (e.g., "-1" for previous version). Default is "LATEST".
        master_cal : bool | str | None, optional
            Whether to filter for master calibrations. Can be True, False, "PREFER" (prefer master but allow non-master if no master available), or None/"ANY" (no filtering). Default is None.
        **kwargs
            Additional keyword arguments for the selector that are set as attributes.
        """
        super().__init__(origin=origin, **kwargs)
        if cal_version is not None:
            self.cal_version = cal_version
        else:
            self.cal_version = os.getenv('LIGERDRP_CALIBRATION_VERSION')
        if master_cal is not None:
            self.master_cal = master_cal
        else:
            self.master_cal = os.getenv('LIGERDRP_MASTER_CAL')

    def select_best(self, input, candidates : list[dict] | dict, **kwargs) -> dict | None:
        """
        Select the best calibration(s) based on the candidates.
        The default implementation does the following:

            - If ``candidates`` is a list, it applies the origin and versions filters and returns the first candidate if available, or ``None`` if the list is empty.
            - If ``candidates`` is not a list (e.g., a single ``dict``), it returns the element as is.
        
        The input ordering is preserved.
        This can optionally be overridden by subclasses, but care should be taken in doing so to maintain the expected behavior.
        
        Parameters
        ----------
        input
            The input object for which a calibration is to be selected.
            The exact type depends on the specific selector implementation.
        candidates : list[dict] | dict
            Candidate calibrations returned from ``get_candidates()``.
        **kwargs
            Additional filtering parameters as necessary.
        
        Returns
        -------
        dict | None
            Selected calibration metadata record, or None if no candidates available.
        """

        if len(candidates) == 0:
            return None
        if type(candidates) in (dict, None):
            return candidates
        
        candidates = self._filter_origin(candidates)
        if len(candidates) == 0:
            return None
        candidates = self._filter_master(candidates)
        if len(candidates) == 0:
            return None
        
        cal0 = candidates[0]
        candidates_family = []
        for cal in candidates:
            # Check if next cal is in same version family
            # HACK: Spectrograph, cal_type, master_cal already filtered correctly, only need to check date time obs
            # This is a temporary workaround since get_version_family_column_names is implemented in the store and not accessible here.
            if cal0['datetime_obs'] == cal['datetime_obs']:
                candidates_family.append(cal)

        # Narrowed down to single version family, now safely filter by version
        candidates = self._filter_version(candidates_family)
        result = candidates[0] if len(candidates) > 0 else None

        return result

    def _filter_origin(self, rows : list[dict], origin : str | None = None) -> list[dict]:
        """
        Filter the candidate rows based on the origin.

        Parameters
        ----------
        rows : list[dict]
            List of candidate calibration metadata records, each containing an 'origin' key.
        origin : str, optional
            The origin filter to apply. Can be "ANY", "LOCAL", or "REMOTE".
            If None, defaults to `self.origin`.

        Returns
        -------
        list[dict]
            Filtered list of calibration metadata records.
        """
        if origin is None:
            origin = self.origin
        if origin in ("ANY", None):
            return rows
        elif origin == "LOCAL":
            return [row for row in rows if row['origin'] == "LOCAL"]
        elif origin == "REMOTE":
            return [row for row in rows if row['origin'] == "REMOTE"]
        else:
            raise ValueError(f"Invalid origin filter: {origin}. Must be 'ANY', 'LOCAL', or 'REMOTE'.")
        
    def _filter_version(self, rows : list[dict], cal_version : str | None = None) -> list[dict]:
        """
        Filter the candidate rows based on the calibration version.

        Parameters
        ----------
        rows : list[dict]
            List of candidate calibration metadata records, each containing a 'cal_version' key.
        cal_version : str, optional
            The calibration version to filter by. If None, no version filtering is applied.

        Returns
        -------
        list[dict]
            Filtered list of calibration metadata records.
        """

        if cal_version is None:
            cal_version = self.cal_version
        if isinstance(cal_version, str):
            cal_version = cal_version.upper()

        # Extract all versions
        versions = [row['cal_version'] for row in rows]

        # If None, pick latest version
        if cal_version in (None, "ANY", "LATEST"):
            vmax = max(versions)
            return [row for row, v in zip(rows, versions) if v == vmax]
        
        # If specific version provided, filter by that version
        if (
            isinstance(cal_version, str)
            and len(cal_version) == 3
            and cal_version.isdigit()
        ):
            return [row for row in rows if row['cal_version'] == cal_version]

        # If version is a negative integer, roll back to previous version
        if (
            isinstance(cal_version, str)
            and cal_version.startswith("-")
            and cal_version[1:].isdigit()
        ):
            n = int(cal_version)
            unique_versions = sorted(set(versions), reverse=True)
            if -n > len(unique_versions):
                return []  # Not enough versions available
            target_version = unique_versions[-n]
            return [row for row in rows if row['cal_version'] == target_version]
        
        if (
            isinstance(cal_version, int)
            and cal_version < 0
        ):
            n = cal_version
            unique_versions = sorted(set(versions), reverse=True)
            if -n > len(unique_versions):
                return []  # Not enough versions available
            target_version = unique_versions[-n]
            return [row for row in rows if row['cal_version'] == target_version]
    
    def _filter_master(self, rows : list[dict], master_cal : bool | None = None) -> list[dict]:
        """
        Filter the candidate rows to only include master calibrations.

        Parameters
        ----------
        rows : list[dict]
            List of candidate calibration metadata records, each containing a 'master_cal' key.

        Returns
        -------
        list[dict]
            Filtered list of calibration metadata records where 'master_cal' is True.
        """
        if master_cal is None:
            master_cal = self.master_cal

        if master_cal is True:
            return [row for row in rows if row['master_cal'] == 1]
        elif master_cal is False:
            return [row for row in rows if row['master_cal'] == 0]
        elif master_cal in ("ANY", None):
            return rows
        elif isinstance(master_cal, str):
            master_cal = master_cal.upper()
            if master_cal == "PREFER":
                master_cals = [row for row in rows if row['master_cal'] == 1]
                if master_cals:
                    return master_cals
                else:
                    non_master_cals = [row for row in rows if row['master_cal'] == 0]
                    return non_master_cals
            else:
                raise ValueError(f"Invalid master_cal filter: {master_cal}. Must be 'PREFER', 'ANY', True, or False.")
        else:
            return rows

class DQSelector(LigerCalibrationSelector):
    """
    Selector for data quality calibration files.

    **Calibration Type:** dq

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "dq",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class SaturationSelector(LigerCalibrationSelector):
    """
    Selector for saturation calibration files.

    **Calibration Type:** saturation

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "saturation",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class DarkSelector(LigerCalibrationSelector):
    """
    Selector for dark calibration files.

    **Calibration Type:** dark

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "dark",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"],
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class BiasSelector(LigerCalibrationSelector):
    """
    Selector for bias calibration files.

    **Calibration Type:** bias

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "bias",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class ReadNoiseSelector(LigerCalibrationSelector):
    """
    Selector for read noise calibration files.

    **Calibration Type:** rn

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "rn",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class NonlinearCorrectionSelector(LigerCalibrationSelector):
    """
    Selector for nonlinear correction calibration files.

    **Calibration Type:** nonlin

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "nonlin",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class DetectorFlatSelector(LigerCalibrationSelector):
    """
    Selector for detector flat calibration files.

    **Calibration Type:** detflat

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "detflat",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class GainSelector(LigerCalibrationSelector):
    """
    Selector for detector gain calibration files.

    **Calibration Type:** gain

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "gain",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"],
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class WavelengthSolutionSelector(LigerCalibrationSelector):
    """
    Selector for wavelength solution calibration files.

    *UNDER DEVELOPMENT*

    **Calibration Type:** Configurable (default: lfc_wavesol)

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time

    Parameters
    ----------
    cal_type : str, optional
        The type of wavelength calibration to select. Default: lfc_wavesol
    """

    def __init__(self, cal_type : str = 'lfc_wavesol'):
        super().__init__()
        self.cal_type = cal_type

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": self.cal_type,
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)

class DistortionSelector(LigerCalibrationSelector):
    """
    Selector for distortion calibration files.

    **Calibration Type:** distortion

    **Selection Logic:**

    - Match instrument era
    - Match detector
    - Closest in observation time
    """

    def get_candidates(self, meta : dict, db : LocalCalibrationDB):
        rows = db.rows_where(
            """
            cal_type = :cal_type AND
            instrument_era = :era AND
            detector = :detector
            """,
            {
                "cal_type": "distortion",
                "era": meta["instrument.era"],
                "detector": meta["instrument.detector"],
                "mjd_start": meta["exposure.mjd_start"]
            },
            order_by="ABS(mjd_start - :mjd_start)"
        )

        return list(rows)