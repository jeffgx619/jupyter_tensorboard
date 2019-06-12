import socket

class GlobalConfigs:
    HOST_NAME = socket.gethostname()

    TB_PROXY_SERVER_PORT = 6505

    TB_PROXY_SERVER_CHECKING_URL = 'http://' + HOST_NAME + ":" + str(TB_PROXY_SERVER_PORT)

    TB_PROXY_SERVER_OP_URL = 'http://' + HOST_NAME + ":" + str(TB_PROXY_SERVER_PORT) + '/tensorboard'

    TB_PROXY_SERVER_CHECKING_MAX_ATTEMPTS = 10

    TB_PROXY_SERVER_LAUNCH_COMMAND = 'python -m jupyter_tensorboard.tensorboard_proxy_server'