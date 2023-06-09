import click
import flask

from openttd_helpers.logging_helper import click_logging
from openttd_helpers.sentry_helper import click_sentry
from werkzeug import serving

from . import pages  # noqa
from . import app
from .api import click_api
from .helpers import click_urls
from .session import click_max_age


# Patch the werkzeug logger to only log errors
def log_request(self, code="-", size="-"):
    if str(code).startswith(("2", "3")):
        return
    original_log_request(self, code, size)


original_log_request = serving.WSGIRequestHandler.log_request
serving.WSGIRequestHandler.log_request = log_request


@click.group(cls=flask.cli.FlaskGroup, create_app=lambda: app.app)
@click_logging  # Should always be on top, as it initializes the logging
@click_sentry
@click_urls
@click_api
@click_max_age
@click.option(
    "--remote-ip-header",
    help="Header which contains the remote IP address. Make sure you trust this header!",
)
def cli(remote_ip_header):
    if remote_ip_header:
        app.REMOTE_IP_HEADER = f"HTTP_{remote_ip_header.upper().replace('-', '_')}"


if __name__ == "__main__":
    cli(auto_envvar_prefix="WEBCLIENT")
