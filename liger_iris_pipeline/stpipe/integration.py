
__all__ = ["install", "get_steps"]

# NOTE:
# This intentionally does not import any of the step or pipeline classes
# This is hardcoded for performance reasons, but TBD on the the impact
#   of this and how stpipe is used at the telescope.

def get_steps():
    return [

        # Assign WCS
        ("liger_iris_pipeline.assign_wcs.assign_wcs_step.AssignWCSStep", "assign_wcs", False),

        # Background subtraction
        ("liger_iris_pipeline.background.calc_background_imager_step.CalculateBackgroundImagerStep", "background_calc", False),
        ("liger_iris_pipeline.background.subtract_background_imager_step.BackgroundSubtractionImagerStep", "background_sub", False),

        # Bias subtraction
        ("liger_iris_pipeline.bias_subtraction.bias_step.BiasSubtractionStep", "bias_sub", False),
        ("liger_iris_pipeline.bias_subtraction.make_bias_step.MakeBiasStep", "make_bias", False),

        # Coadding
        ("liger_iris_pipeline.coadd.coadd_frames_step.CoaddFramesStep", "coadd_frames", False),

        # Dark subtraction
        ("liger_iris_pipeline.dark_subtraction.dark_step.DarkSubtractionStep", "dark_sub", False),
        ("liger_iris_pipeline.dark_subtraction.make_dark_step.MakeDarkStep", "make_dark", False),

        # Detector flat field correction
        ("liger_iris_pipeline.detector_flat.detector_flat_step.DetectorFlatStep", "detflat", False),
        ("liger_iris_pipeline.detector_flat.make_detector_flat_step.MakeDetectorFlatStep", "make_detflat", False),

        # Distortion correction
        ("liger_iris_pipeline.distortion.distortion_step.DistortionCorrectionStep", "distortion", False),

        # DQ initialization
        ("liger_iris_pipeline.dq_init.dq_init_step.DQInitStep", "dq_init", False),

        # Detector gain correction
        ("liger_iris_pipeline.gain.gain_step.GainStep", "gain", False),
        ("liger_iris_pipeline.gain.make_gain_step.MakeGainStep", "make_gain", False),

        # Jump detection
        ("liger_iris_pipeline.jump_detection.jump_detection_step.JumpDetectionStep", "jump_detection", False),

        # Merge subarrays
        ("liger_iris_pipeline.merge_subarrays.merge_subarrays_step.MergeSubarraysStep", "merge_subarrays", False),

        # Nonlinear correction
        ("liger_iris_pipeline.nonlinear_correction.nonlincorr_step.NonlinearCorrectionStep", "nonlin_corr", False),
        ("liger_iris_pipeline.nonlinear_correction.make_nonlin_step.MakeNonLinStep", "make_nonlin", False),

        # Normalize
        ("liger_iris_pipeline.normalize.normalize_step.NormalizeStep", "normalize", False),

        # Parse subarray map
        ("liger_iris_pipeline.parse_subarray_map.parse_subarray_map_step.ParseSubarrayMapStep", "parse_subarrays", False),

        # Ramp fitting
        ("liger_iris_pipeline.ramp_fitting.fit_ramp_step.RampFitStep", "ramp_fit", False),

        # Read noise
        ("liger_iris_pipeline.read_noise.make_read_noise_step.MakeReadNoiseStep", "make_rn", False),

        # Reference pixel correction
        ("liger_iris_pipeline.refpix.refpix_step.RefPixelCorrectionStep", "refpix", False),

        # Register calibration locally
        ("liger_iris_pipeline.calibrations.register_calibration_step.RegisterCalibrationStep", "register_cal", False),

        # Saturation flagging
        ("liger_iris_pipeline.saturation.saturation_step.SaturationCheckStep", "sat_check", False),
        ("liger_iris_pipeline.saturation.make_saturation_step.MakeSaturationStep", "make_sat", False),

        ###################################################

        # Science pipelines
        ("liger_iris_pipeline.pipeline.stage1_pipeline.Stage1Pipeline", "stage1", True),
        ("liger_iris_pipeline.pipeline.stage2_imager_pipeline.Stage2ImagerPipeline", "stage2_imager", True),

        # Calibration pipelines
        ("liger_iris_pipeline.pipeline.process_bias_pipeline.ProcessBiasPipeline", "process_bias", True),
        ("liger_iris_pipeline.pipeline.process_darks_pipeline.ProcessDarksPipeline", "process_darks", True),
        ("liger_iris_pipeline.pipeline.process_detflats_pipeline.ProcessDetFlatsPipeline", "process_detflats", True),
        ("liger_iris_pipeline.pipeline.process_satdetflats_pipeline.ProcessSatDetFlatsPipeline", "process_satdetflats", True),
    ]