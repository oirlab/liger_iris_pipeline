====================================
Create Simulated Liger and IRIS Data
====================================

This example shows how to create a subset of simulated Liger and IRIS data.


Creating UTR Cubes
------------------

.. code-block:: python

    from liger_iris_pipeline.simulations import create_ramp

    max_cores = 1
    max_slope = 50  # e-/s
    readtime = 1.7  # seconds
    n_reads = 10
    ny, nx = 4096, 4096 # size of the detector
    nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity

    gain = 1.0  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)

    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)

    dark_current = 10  # e-/s
    dark_map = np.random.normal(loc=dark_current, scale=dark_current / 10, size=(ny, nx)).astype(np.float32)

    ramp_data = create_ramp(
        native_rate_map,  # in e-/s
        readtime=readtime, n_reads=n_reads,
        nonlin_coeffs=nonlin_coeffs,
        gain=gain_map,  # in e-/s
        flat=detflat_map,
        dark=dark_map,  # in e-/s
        bias=bias_map,  # in e-/s
        kTC_noise=50,  # in e-/s
        poisson_noise=False, read_noise=0,  # in e-/s
        convert_to_uint16=False, clip_ramps=True,
        max_cores=max_cores
    )