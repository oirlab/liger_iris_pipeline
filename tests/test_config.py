from liger_iris_pipeline.coadd import CoaddFramesStep
from liger_iris_pipeline.stpipe.base_step import LigerIRISStep
from liger_iris_pipeline.pipeline import Stage1Pipeline
import os

from stpipe.cmdline import just_the_step_from_cmdline

def test_step_config(tmp_path):
    
    # Test with no config file or args
    step = CoaddFramesStep()
    assert step.method == 'wmean'
    assert step.sigma_thresh_low == 4.0

    # Initial args
    method = 'median'
    sigma_thresh_low = 10

    # Make config file
    config_tree = {
       'name': 'CoaddFramesStep_config',
       'class' : 'liger_iris_pipeline.coadd.coadd_frames_step.CoaddFramesStep',
       'parameters' : {
            'method': method,
            'sigma_thresh_low': sigma_thresh_low,
       }
    }
    config_path = os.path.join(tmp_path, config_tree['name'] + '.asdf')
    # save_asdf_config(config_tree, config_path)

    # # Test with config file
    step = LigerIRISStep.from_config_file(
        config_file=config_path,
        parent=None, name=None
    )
    assert step.method == method
    assert step.sigma_thresh_low == sigma_thresh_low


def _test_pipeline_config(tmp_path):

    # Test default args
    pipe = Stage1Pipeline()
    assert pipe.ramp_fit.method == 'cython_likely'
    assert pipe.ramp_fit.mcds_num_coadd == 3

    # # Create config file with different values
    # method = 'mcds'
    # mcds_num_coadd = 5
    # config_tree = {
    #     'name': 'Stage1Pipeline_config',
    #     'class': 'liger_iris_pipeline.pipeline.stage1_pipeline.Stage1Pipeline',
    #     'parameters' : {},
    #     'steps' : {
    #         'ramp_fit': {
    #             'class': 'liger_iris_pipeline.ramp_fit.ramp_fit_step.RampFitStep',
    #             'parameters': {
    #                 'method': method,
    #                 'mcds_num_coadd': mcds_num_coadd,
    #             },
    #         },
    #     },
    # }
    # config_path = os.path.join(tmp_path, config_tree['name'] + '.asdf')
    # save_asdf_config(to_stpipe_pipeline_config(config_tree), config_path)

    # # Test with config file
    # pipe = LigerIRISStep.from_config_file(config_file=config_path, parent=None, name=None)
    # assert pipe.ramp_fit.method == method
    # assert pipe.ramp_fit.mcds_num_coadd == mcds_num_coadd

    # Config file with nested config file
    # First make step config file
    method = 'single'
    single_read_num = 5
    config_tree_step = {
       'name': 'RampFitStep_config',
       'class' : 'liger_iris_pipeline.ramp_fit.ramp_fit_step.RampFitStep',
       'parameters' : {
            'method': method,
       }
    }
    config_path_step = os.path.join(tmp_path, config_tree_step['name'] + '.asdf')
    save_asdf_config(config_tree_step, config_path_step)

    # Pipeline config file
    config_tree_pipe = {
        'name': 'Stage1Pipeline_config',
        'class': 'liger_iris_pipeline.pipeline.stage1_pipeline.Stage1Pipeline',
        'parameters' : {},
        'steps' : {
            'ramp_fit': {
                'class': 'liger_iris_pipeline.ramp_fit.ramp_fit_step.RampFitStep',
                'config_file': config_path_step,
                'parameters': {
                    #'single_read_num': single_read_num,
                    #'method': method,
                },
            },
        },
    }

    config_path_pipe = os.path.join(tmp_path, config_tree_pipe['name'] + '.asdf')
    save_asdf_config(to_stpipe_pipeline_config(config_tree_pipe), config_path_pipe)

    breakpoint()

    pipe = LigerIRISStep.from_config_file(config_file=config_path_pipe)

    breakpoint()

    # Test
    assert pipe.ramp_fit.method == method
    assert pipe.ramp_fit.single_read_num == single_read_num