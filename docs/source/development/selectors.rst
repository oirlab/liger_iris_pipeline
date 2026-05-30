=====================
Calibration Selectors
=====================

Calibration Selectors are Python classes that specify and run the logic to select the most appropriate calibration file from the local calibration cache.

- All *Liger* selectors within liger_iris_pipeline should inherit from `LigerCalibrationSelector`.

*IRIS Selectors under development*

See the `KOA Middleware documentation  <https://oirlab.github.io/KOA_Middleware/selectors.html>`_ for more information on selectors and how to create a new selector class.

For example, the `DarkSelector` for Liger class is implemented as follows:


.. code-block:: python

    class DarkSelector(LigerCalibrationSelector):
        """
        Selector for dark calibration files.

        **Reference Type:** dark

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
                mode = :mode
                ifs_mode = :ifs_mode
                """,
                {
                    "cal_type": "dark",
                    "era": meta["instrument.era"],
                    "mode": meta["instrument.mode"],
                    "ifs_mode": meta["instrument.ifs_mode"],
                    "mjd_start": meta["exposure.mjd_start"],
                },
                order_by="ABS(mjd_start - :mjd_start)"
            )

            return list(rows)

Typically, ``get_candidates()`` should **not** filter based on ``master_cal``, ``origin`` (i.e, 'KECK' or 'LOCAL'), or ``cal_version``.

After ``get_candidates()`` is called, a `LigerCalibrationSelector` automatically filters on the calibration ``origin``, whether or not the calibration is a master calibration, and finally the calibration version based on environment variables or inputs to the selector class contructor.