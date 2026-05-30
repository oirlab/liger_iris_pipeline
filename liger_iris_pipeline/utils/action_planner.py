

class Action:

    def __init__(self, klass : type | str, **kwargs):
        if isinstance(klass, str):
            klass = get_step_class_from_string(klass)
        self.klass = klass
        self.kwargs = kwargs


class ActionPlanner:

    def __init__(self):
        pass
    
    def get_config_file(self, action=None):
        if action == 'assign_wcs':
            return 'assign_wcs_config.yaml'
        else:
            raise ValueError(f"Unknown action: {action}")
        
    def get_action(self, **kwargs):
        pass
    