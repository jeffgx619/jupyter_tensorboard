from tornado import web
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.gen
from tornado.options import options, define
from tensorboard_proxy_handler import TensorboardProxyHandler
import tensorboard_proxy_global as tb_global
from configs import GlobalConfigs

# srv settings
define("port", default=GlobalConfigs.TB_PROXY_SERVER_PORT, help="run on the given port", type=int)

class ServiceCheckerHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        self.finish({'operation': 'get', 'message': 'Successfully connect to TensorboardProxyServer!'})

class TensorboardProxyService(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", ServiceCheckerHandler),
            (r"/tensorboard", TensorboardProxyHandler),
        ]
        super(TensorboardProxyService, self).__init__(handlers)

    def register_handlers(self):
        pass


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(TensorboardProxyService())
    http_server.listen(port=options.port)
    srv_instance = tornado.ioloop.IOLoop.instance()

    try:
        tb_global.init()
        srv_instance.start()
    except KeyboardInterrupt as e:
        print "server instance is forced to quit."
        srv_instance.stop()

if __name__ == "__main__":
    main()