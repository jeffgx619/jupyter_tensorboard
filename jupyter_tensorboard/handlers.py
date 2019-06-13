# -*- coding: utf-8 -*-

from tornado import web
from .utils import concat_params_to_str
from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import path_regex
import tornado.web
from .configs import GlobalConfigs

notebook_dir = None


def load_jupyter_server_extension(nb_app):

    global notebook_dir
    # notebook_dir should be root_dir of contents_manager
    notebook_dir = nb_app.contents_manager.root_dir

    web_app = nb_app.web_app
    base_url = web_app.settings['base_url']

    try:
        from .tensorboard_dict import manager_dict
    except ImportError:
        nb_app.log.info("import tensorboard error, check tensorflow install")
        handlers = [
            (ujoin(
                base_url, r"/tensorboard.*"),
                TensorboardErrorHandler),
        ]
    else:
        web_app.settings["tensorboard_manager_dict"] = manager_dict
        from . import api_handlers

        handlers = [
            (ujoin(
                base_url, r"/tensorboard/(?P<name>\w+)%s" % path_regex),
                TensorboardHandler),
            (ujoin(
                base_url, r"/api/tensorboard"),
                api_handlers.TbRootHandler),
            (ujoin(
                base_url, r"/api/tensorboard/(?P<name>\w+)"),
                api_handlers.TbInstanceHandler),
        ]

    web_app.add_handlers('.*$', handlers)
    nb_app.log.info("jupyter_tensorboard extension loaded.")


class TensorboardHandler(IPythonHandler):

    def handle_response(self, response):
        if response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
            print("response has error %s", response.error)
            self.set_status(500)
            self.write("Internal server error:\n" + str(response.error))
            self.finish()
        else:
            self.set_status(response.code)
            for header in response.headers:
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            if response.body:
                self.write(response.body)
            self.finish()

    @web.authenticated
    @tornado.web.asynchronous
    def get(self, name, path):

        if path == "":
            uri = self.request.path + "/"
            if self.request.query:
                uri += "?" + self.request.query
            self.redirect(uri, permanent=True)
            return

        self.request.path = (
            path if self.request.query
            else "%s?%s" % (path, self.request.query))
        manager = self.settings["tensorboard_manager_dict"]
        if name in manager:
            try:
                body = concat_params_to_str({'name':str(name),
                                             'uri':self.request.uri,
                                             'path':self.request.path,
                                             'method':self.request.method
                                             }
                                            )
                tornado.httpclient.AsyncHTTPClient().fetch(
                    tornado.httpclient.HTTPRequest(
                        url=GlobalConfigs.TB_PROXY_SERVER_OP_URL,
                        method='POST',
                        headers=self.request.headers,
                        decompress_response=False,
                        follow_redirects=True, body=body
                        ),
                    self.handle_response)
            except tornado.httpclient.HTTPError as x:
                print("tornado signalled HTTPError %s", x)
                if hasattr(x, response) and x.response:
                    self.handle_response(x.response)
            except tornado.httpclient.CurlError as x:
                print("tornado signalled CurlError %s", x)
                self.set_status(500)
                self.write("Internal server error:\n" + ''.join(traceback.format_exception(*sys.exc_info())))
                self.finish()
            except:
                self.set_status(500)
                self.write("Internal server error:\n" + ''.join(traceback.format_exception(*sys.exc_info())))
                self.finish()

        else:
            raise web.HTTPError(404)


class TensorboardErrorHandler(IPythonHandler):
    pass
