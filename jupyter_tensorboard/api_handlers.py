# -*- coding: utf-8 -*-

import json
import os

from tornado import web
from notebook.base.handlers import APIHandler
import requests
from .handlers import notebook_dir
from .configs import GlobalConfigs


def _trim_notebook_dir(dir):
    if not dir.startswith("/"):
        return os.path.join(
            "<notebook_dir>", os.path.relpath(dir, notebook_dir)
        )
    return dir


class TbRootHandler(APIHandler):

    @web.authenticated
    def get(self):
        terms = [
            {
                'name': entry['name'],
                'logdir': _trim_notebook_dir(entry['logdir']),
                "reload_time": entry['reload_time'],
            } for entry in
            self.settings["tensorboard_manager_dict"].values()
        ]
        self.finish(json.dumps(terms))

    @web.authenticated
    def post(self):
        data = self.get_json_body()
        reload_interval = data.get("reload_interval", None)

        # check whether we need to spawn a separate process to start tensorboard_proxy_server
        self.settings["tensorboard_manager_dict"].start_tb_proxy_server_process()

        entry = (
            self.settings["tensorboard_manager_dict"]
            .new_instance(data["logdir"], reload_interval=reload_interval)
        )

        params = {'name':entry.get('name'),
                  'logdir':entry.get('logdir'),
                  'reload_interval':entry.get('reload_time')}

        res = requests.put(url=GlobalConfigs.TB_PROXY_SERVER_OP_URL,json=params)
        if res.status_code == requests.codes.ok:
            self.finish(json.dumps({
                    'name': entry.get('name'),
                    'logdir':  _trim_notebook_dir(entry.get('logdir')),
                    'reload_time': entry.get('reload_time')}))
        else:
            raise web.HTTPError(
                404, "TensorBoard instance can not be created: %r" % entry.get('name'))

class TbInstanceHandler(APIHandler):

    SUPPORTED_METHODS = ('GET', 'DELETE')

    @web.authenticated
    def get(self, name):
        manager_dict = self.settings["tensorboard_manager_dict"]
        if name in manager_dict:
            entry = manager_dict[name]
            self.finish(json.dumps({
                'name': entry['name'],
                'logdir':  _trim_notebook_dir(entry['logdir']),
                'reload_time': entry['reload_time']}))
        else:
            raise web.HTTPError(
                404, "TensorBoard instance not found: %r" % name)

    @web.authenticated
    def delete(self, name):
        manager_dict = self.settings["tensorboard_manager_dict"]
        if name in manager_dict:
            manager_dict.terminate(name, force=True)
            # http request call
            params = {'name':name}
            requests.delete(url=GlobalConfigs.TB_PROXY_SERVER_OP_URL, json=params)
            self.settings["tensorboard_manager_dict"].shutdown_tb_proxy_server_process()
            self.set_status(204)
            self.finish()
        else:
            raise web.HTTPError(
                404, "TensorBoard instance not found: %r" % name)
