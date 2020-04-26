import click
import flask
import logging

from werkzeug import serving

from . import pages  # noqa
from .api import click_api
from .app import app
from .click import click_additional_options
from .helpers import click_urls
from .sentry import click_sentry
from .session import click_max_age


# Patch the werkzeug logger to only log errors
def log_request(self, code="-", size="-"):
    if str(code).startswith(("2", "3")):
        return
    original_log_request(self, code, size)


original_log_request = serving.WSGIRequestHandler.log_request
serving.WSGIRequestHandler.log_request = log_request


@click_additional_options
def click_logging():
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO
    )


@click.group(cls=flask.cli.FlaskGroup, create_app=lambda: app)
@click_logging
@click_sentry
@click_urls
@click_api
@click_max_age
def cli():
    pass


if __name__ == "__main__":
    cli(auto_envvar_prefix="WEBCLIENT")
