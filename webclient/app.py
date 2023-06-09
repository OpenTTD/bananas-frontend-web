import flask

REMOTE_IP_HEADER = None


class ProxyFix:
    def __init__(self, app) -> None:
        self.app = app

    def __call__(self, environ, start_response):
        if REMOTE_IP_HEADER:
            remote_ip = environ.get(REMOTE_IP_HEADER)
            if remote_ip:
                environ["REMOTE_ADDR"] = remote_ip

        return self.app(environ, start_response)


app = flask.Flask("webclient")
app.wsgi_app = ProxyFix(app.wsgi_app)
