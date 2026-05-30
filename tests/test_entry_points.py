from stpipe.entry_points import get_steps
import liger_iris_pipeline
import importlib

def import_class(path: str):
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def test_get_steps():

    # Get all steps and pipelines
    step_info_by_class = {s.class_name: s for s in get_steps() if s.package_name == "liger_iris_pipeline"}

    # Test each step
    for class_module_path in step_info_by_class:
        try:
            _class = import_class(class_module_path)
        except Exception as e:
            print(f"Failed to import {class_module_path}: {e}")
            raise e
        step_info = step_info_by_class[class_module_path]
        assert step_info.class_alias == _class.class_alias
        assert step_info.is_pipeline is issubclass(_class, liger_iris_pipeline.stpipe.base_pipeline.LigerIRISPipeline)
        assert step_info.package_name == "liger_iris_pipeline"
        assert step_info.package_version == liger_iris_pipeline.__version__