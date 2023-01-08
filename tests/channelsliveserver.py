from functools import partial
import threading
import time

from daphne.endpoints import build_endpoint_description_strings
from daphne.server import Server as DaphneServer
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test.utils import modify_settings


def get_open_port() -> int:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def make_application(*, static_wrapper):
    # Module-level function for pickle-ability
    from testproject.asgi import application

    if static_wrapper is not None:
        application = static_wrapper(application)
    return application


class ChannelsLiveServer:

    host = "localhost"
    static_wrapper = ASGIStaticFilesHandler
    serve_static = True

    def __init__(self) -> None:
        self.port = get_open_port()
        for connection in connections.all():
            if connection.vendor == "sqlite" and connection.is_in_memory_db():
                raise ImproperlyConfigured(
                    "ChannelsLiveServer can not be used with in memory databases"
                )

        self._live_server_modified_settings = modify_settings(ALLOWED_HOSTS={"append": self.host})
        self._live_server_modified_settings.enable()

        get_application = partial(
            make_application,
            static_wrapper=self.static_wrapper if self.serve_static else None,
        )
        endpoints = build_endpoint_description_strings(host=self.host, port=self.port)

        self._server = DaphneServer(application=get_application(), endpoints=endpoints)
        t = threading.Thread(target=self._server.run)
        t.start()
        for _ in range(10):
            time.sleep(0.10)
            if self._server.listening_addresses:
                break
        assert self._server.listening_addresses[0]

    def stop(self) -> None:
        self._server.stop()
        self._live_server_modified_settings.disable()

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/graphql"

    @property
    def http_url(self):
        return f"http://{self.host}:{self.port}/graphql"
