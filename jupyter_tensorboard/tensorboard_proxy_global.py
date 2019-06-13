from .tensorboard_manager import TensorboardManger


def init():
    global _proxy_manager_dict
    _proxy_manager_dict = {
        'tb_manager':TensorboardManger(),
        'tb_apps':{}
    }


def get_tb_proxy_manager():
    return _proxy_manager_dict['tb_manager']


def add_new_tb_instance(name, zb_app):
    _proxy_manager_dict['tb_apps'][name] = zb_app


def get_tb_instance(name):
    if name in _proxy_manager_dict['tb_apps']:
        return _proxy_manager_dict['tb_apps'][name]
    return None


def delete_tb_instance(name):
    instance = _proxy_manager_dict['tb_apps'].pop(name, None)
    if instance:
        if instance.thread is not None:
            instance.thread.stop = True
    print(_proxy_manager_dict['tb_apps'])


def check_tb_exist(name):
    return name in _proxy_manager_dict['tb_apps']
