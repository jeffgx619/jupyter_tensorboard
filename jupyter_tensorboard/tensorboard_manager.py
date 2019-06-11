# -*- coding: utf-8 -*-

import sys
import threading
import time
import tensorboard_proxy_global as tb_global
from collections import namedtuple
import logging

import six

sys.argv = ["tensorboard"]

TensorBoardInstance = namedtuple(
    'TensorBoardInstance', ['name', 'logdir', 'tb_app', 'thread'])


class TensorboardManger:

    def __init__(self):
        self.application = None
        self.lock = threading.Lock()
        self.name = None

    def new_instance(self, name, logdir, reload_interval):
        with self.lock:
            if tb_global.check_tb_exist(name=name):
                return True
            self.name = name
            if not self.application:
                from tensorboard.backend import application
                def start_reloading_multiplexer(multiplexer, path_to_run, reload_interval):
                    def _ReloadForever():
                        current_thread = threading.currentThread()
                        while not current_thread.stop:
                            application.reload_multiplexer(multiplexer, path_to_run)
                            current_thread.reload_time = time.time()
                            time.sleep(reload_interval)

                    thread = threading.Thread(target=_ReloadForever)
                    thread.reload_time = None
                    thread.stop = False
                    thread.daemon = True
                    thread.start()
                    return thread

                def TensorBoardWSGIApp(logdir, plugins, multiplexer,
                                       reload_interval, path_prefix="", reload_task="auto"):
                    path_to_run = application.parse_event_files_spec(logdir)
                    if reload_interval:
                        thread = start_reloading_multiplexer(
                            multiplexer, path_to_run, reload_interval)
                    else:
                        application.reload_multiplexer(multiplexer, path_to_run)
                        thread = None
                    tb_app = application.TensorBoardWSGI(plugins)
                    self.add_instance(logdir, tb_app, thread)
                    return tb_app

                application.TensorBoardWSGIApp = TensorBoardWSGIApp
                self.application = application

            purge_orphaned_data = True
            self.create_tb_app(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data)

            return True

    def add_instance(self, logdir, tb_application, thread):
        instance = TensorBoardInstance(self.name, logdir, tb_application, thread)
        tb_global.add_new_tb_instance(self.name, instance)

    def create_tb_app(self, logdir, reload_interval, purge_orphaned_data):
        try:
            # Tensorboard 0.4.x above series
            from tensorboard import default

            if not hasattr(self.application, "reload_multiplexer"):
                # Tensorflow 1.12 removed reload_multiplexer, patch it
                def reload_multiplexer(multiplexer, path_to_run):
                    for path, name in six.iteritems(path_to_run):
                        multiplexer.AddRunsFromDirectory(path, name)
                    multiplexer.Reload()

                self.application.reload_multiplexer = reload_multiplexer

            if hasattr(default, 'PLUGIN_LOADERS') or hasattr(default, '_PLUGINS'):
                # Tensorflow 1.10 or above series
                logging.debug("Tensorboard 1.10 or above series detected")
                from tensorboard import program

                argv = [
                    "",
                    "--logdir", logdir,
                    "--reload_interval", str(reload_interval),
                    "--purge_orphaned_data", str(purge_orphaned_data),
                ]
                tensorboard = program.TensorBoard()
                tensorboard.configure(argv)
                return self.application.standard_tensorboard_wsgi(
                    tensorboard.flags,
                    tensorboard.plugin_loaders,
                    tensorboard.assets_zip_provider)
            else:
                logging.debug("Tensorboard 0.4.x series detected")

                return self.application.standard_tensorboard_wsgi(
                    logdir=logdir, reload_interval=reload_interval,
                    purge_orphaned_data=purge_orphaned_data,
                    plugins=default.get_plugins())

        except ImportError:
            # Tensorboard 0.3.x series
            from tensorboard.plugins.audio import audio_plugin
            from tensorboard.plugins.core import core_plugin
            from tensorboard.plugins.distribution import distributions_plugin
            from tensorboard.plugins.graph import graphs_plugin
            from tensorboard.plugins.histogram import histograms_plugin
            from tensorboard.plugins.image import images_plugin
            from tensorboard.plugins.profile import profile_plugin
            from tensorboard.plugins.projector import projector_plugin
            from tensorboard.plugins.scalar import scalars_plugin
            from tensorboard.plugins.text import text_plugin
            logging.debug("Tensorboard 0.3.x series detected")

            _plugins = [
                core_plugin.CorePlugin,
                scalars_plugin.ScalarsPlugin,
                images_plugin.ImagesPlugin,
                audio_plugin.AudioPlugin,
                graphs_plugin.GraphsPlugin,
                distributions_plugin.DistributionsPlugin,
                histograms_plugin.HistogramsPlugin,
                projector_plugin.ProjectorPlugin,
                text_plugin.TextPlugin,
                profile_plugin.ProfilePlugin,
            ]

            return self.application.standard_tensorboard_wsgi(
                logdir=logdir, reload_interval=reload_interval,
                purge_orphaned_data=purge_orphaned_data,
                plugins=_plugins)
