from tornado import web
import tornado.web
import json
import logging
from tornado.wsgi import WSGIContainer
import tensorboard_proxy_global as tb_global
from utils import split_params_to_dict

class TensorboardProxyHandler(tornado.web.RequestHandler):
    logger = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def post(self):
        self.logger.info("Get the request from: %s", str(self.request))
        if not self.request.body:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return
        params = split_params_to_dict(self.request.body)
        if 'name' not in params or not params['name']:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return

        tb_instance = tb_global.get_tb_instance(params['name'])
        print(tb_instance)
        if not tb_instance:
            self.set_status(400)
            self.finish("The tensorboard item with the name:{} does not exist.".format(params['name']))
            return
        self.request.uri = params.get('uri')
        self.request.path = params.get('path')
        self.request.method = params.get('method')
        WSGIContainer(tb_instance.tb_app)(self.request)


    @tornado.gen.coroutine
    def put(self):
        if not self.request.body:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return
        params = json.loads(self.request.body)
        if 'name' not in params or not params['name'] or \
                'logdir' not in params or not params['logdir'] or \
                'reload_interval' not in params or not params['reload_interval']:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return
        self.logger.info("Get the request from: %s", str(self.request))
        tb_global.get_tb_proxy_manager().new_instance(name=params['name'],
                                                      logdir=params['logdir'],
                                                      reload_interval=params['reload_interval']
                                                      )
        self.set_status(200)
        self.finish({'status': 'Success', 'message': "Create tb instance successfully"})

    @tornado.gen.coroutine
    def delete(self):
        if not self.request.body:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return
        params = json.loads(self.request.body)
        if 'name' not in params or not params['name']:
            self.set_status(400)
            self.finish("Should provide tensorboard name")
            return
        tb_global.delete_tb_instance(params['name'])