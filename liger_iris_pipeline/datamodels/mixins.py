"""
Mixin classes from JWST ported for liger_iris_pipeline.
"""

from stdatamodels import DataModel as _DataModel


__all__ = [
    'DefaultDQMixin',
    'DefaultDQRawMixin',
    'DefaultErrMixin',
    'DefaultSubarrayMapMixin',
    'DefaultReceiptTableMixin',
    'DefaultCalibrationsTableMixin',
]


class DefaultDQMixin(_DataModel):
    """
    Mixin for models that have a data quality arrray
    called "dq" which matches the input shape.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "dq" not in self._schema["properties"]:
            raise AttributeError(
                "dq is not in the schema for this model, cannot use DefaultDQMixin"
            )

        # If data array hasn't been initialized, do not initialize DQ
        if getattr(self, self.get_primary_array_name(), None) is None:
            return

        # Otherwise, ensure DQ array exists
        if getattr(self, "dq", None) is None:
            self.dq = self.get_default("dq")

        # if dq_def is in the schema, attempt to apply dq flag mapping
        # NOTE: Needed for dynamic DQ flags
        #if getattr(self, "dq_def", None) is not None:
            #self.dq = dynamic_mask(self, 'pixel')


class DefaultDQRawMixin(_DataModel):
    """
    Mixin for models that have a data quality arrray
    called "dq_raw" which matches the input shape.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "dq_raw" not in self._schema["properties"]:
            raise AttributeError(
                "dq_raw is not in the schema for this model, cannot use DefaultDQRawMixin"
            )

        # If data array hasn't been initialized, do not initialize DQ
        if getattr(self, self.get_primary_array_name(), None) is None:
            return

        # Otherwise, ensure DQ array exists
        if getattr(self, "dq_raw", None) is None:
            self.dq_raw = self.get_default("dq_raw")

        # if dq_def is in the schema, attempt to apply dq flag mapping
        #if getattr(self, "dq_def", None) is not None:
            #self.dq_raw = dynamic_mask(self, 'pixel')


class DefaultErrMixin(_DataModel):
    """
    Mixin for models that have a an error array
    called "err" which matches the input shape.

    Optionally, if var_poisson and var_rnoise are in the schema,
    those will also be initialized with default values if not already set.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "err" not in self._schema["properties"]:
            raise AttributeError(
                "err is not in the schema for this model, cannot use DefaultErrMixin"
            )

        # If data array hasn't been initialized, do not initialize error array
        if getattr(self, self.get_primary_array_name(), None) is None:
            return

        # Otherwise, ensure error array exists
        if getattr(self, "err", None) is None:
            self.err = self.get_default("err")

        # Initialize var_poisson and var_rnoise if they are in the schema
        if "var_poisson" in self._schema["properties"]:
            if getattr(self, "var_poisson", None) is None:
                self.var_poisson = self.get_default("var_poisson")

        if "var_rnoise" in self._schema["properties"]:
            if getattr(self, "var_rnoise", None) is None:
                self.var_rnoise = self.get_default("var_rnoise")


class DefaultReceiptTableMixin(_DataModel):
    """
    Mixin for models that have a receipt table.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "receipt" not in self._schema["properties"]:
            raise AttributeError(
                "receipt is not in the schema for this model, cannot use DefaultReceiptTableMixin"
            )

        if getattr(self, "receipt", None) is None:
            self.receipt = self.get_default("receipt")


class DefaultCalibrationsTableMixin(_DataModel):
    """
    Mixin for models that have a calibrations table.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "calibrations" not in self._schema["properties"]:
            raise AttributeError(
                "calibrations is not in the schema for this model, cannot use DefaultCalibrationsTableMixin"
            )

        if getattr(self, "calibrations", None) is None:
            self.calibrations = self.get_default("calibrations")


class DefaultSubarrayMapMixin(_DataModel):
    """
    Mixin for models that should have subarray_map array initialized on init.
    This is only implemented for IRIS datamodels.
    """

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)

        if "subarray_map" not in self._schema["properties"]:
            raise AttributeError(
                "subarray_map is not in the schema for this model, cannot use DefaultSubarrayMapMixin"
            )

        # If data array hasn't been initialized, do not initialize subarray_map
        if getattr(self, self.get_primary_array_name(), None) is None:
            return
        
        # Only initialize for IRIS
        if getattr(self, "instrument_name", None) != "IRIS":
            return

        # Otherwise, ensure subarray_map array exists
        if getattr(self, "subarray_map", None) is None:
            self.subarray_map = self.get_default("subarray_map")