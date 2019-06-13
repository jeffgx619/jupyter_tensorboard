from .handlers import notebook_dir
import itertools, os, threading, logging, time
from .configs import GlobalConfigs

class TensorBoardDict(dict):
    def __init__(self):
        self._logdir_dict = {}
        self.tb_proxy_server_process = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def new_instance(self, logdir, reload_interval):
        with self.lock:
            if not os.path.isabs(logdir) and notebook_dir:
                logdir = os.path.join(notebook_dir, logdir)

            if logdir not in self._logdir_dict:
                reload_interval = reload_interval or 30
                name = self._next_available_name()
                attr = {
                    'name': name,
                    'logdir': logdir,
                    'reload_time': reload_interval
                }
                self[name] = attr
                self._logdir_dict[logdir] = attr

            return self._logdir_dict[logdir]

    def _next_available_name(self):
        for n in itertools.count(start=1):
            name = "%d" % n
            if name not in self:
                return name

    def terminate(self, name, force=True):
        with self.lock:
            if name in self:
                entry = self[name]
                del self[name], self._logdir_dict[entry['logdir']]
            else:
                raise Exception("There's no tensorboard instance named %s" % name)

    def start_tb_proxy_server_process(self):
        with self.lock:
            if not self.tb_proxy_server_process:
                import subprocess, shlex
                command_line = GlobalConfigs.TB_PROXY_SERVER_LAUNCH_COMMAND
                args = shlex.split(command_line)
                self.tb_proxy_server_process = subprocess.Popen(args=args)
                import requests
                attempt = 1
                server_started = False
                while attempt <= GlobalConfigs.TB_PROXY_SERVER_CHECKING_MAX_ATTEMPTS:
                    try:
                        res = requests.get(url=GlobalConfigs.TB_PROXY_SERVER_CHECKING_URL)
                        if res.status_code == requests.codes.ok:
                            self.logger.info('The tb proxy server has been started!')
                            server_started = True
                            break
                        else:
                            self.logger.info('The tb proxy server is not started. Retry after 2s')
                            time.sleep(2)
                            attempt += 1
                    except requests.ConnectionError as e:
                        self.logger.info(e)
                        time.sleep(2)
                        attempt += 1
                if not server_started:
                    self.logger.info("Failed to start tb proxy Server")
                    self.tb_proxy_server_process = None


    def shutdown_tb_proxy_server_process(self):
        with self.lock:
            if self.tb_proxy_server_process and len(self._logdir_dict) == 0:
                self.tb_proxy_server_process.kill()
                self.tb_proxy_server_process.wait()
                self.tb_proxy_server_process = None
                self.logger.info("Shutdown the tb proxy server")


manager_dict = TensorBoardDict()