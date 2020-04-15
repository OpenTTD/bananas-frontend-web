import click
import datetime
import flask

from . import pages  # noqa
from .app import app
from .helpers import (
    set_api_url,
    set_frontend_url,
)
from .session import (
    set_auth_backend,
    set_max_age,
)


@click.group(cls=flask.cli.FlaskGroup, create_app=lambda: app)
@click.option(
    "--api-url", help="BaNaNaS API URL.", default="https://api.bananas.openttd.org", show_default=True, metavar="URL",
)
@click.option(
    "--frontend-url",
    help="Frontend URL (this server).",
    default="https://bananas.openttd.org",
    show_default=True,
    metavar="URL",
)
@click.option(
    "--authentication-method",
    help="Authentication method to use.",
    type=click.Choice(["developer", "github", "openttd"], case_sensitive=False),
    default="github",
    show_default=True,
)
@click.option("--developer-username", help="Username to use if authentication is set to 'developer'.")
@click.option(
    "--session-expire",
    help="Time for a session to expire.",
    default=60 * 60 * 14,
    show_default=True,
    metavar="SECONDS",
)
@click.option(
    "--csrf-expire", help="Time for the CSRF token to expire.", default=60 * 30, show_default=True, metavar="SECONDS",
)
def cli(api_url, frontend_url, authentication_method, developer_username, session_expire, csrf_expire):
    if authentication_method == "developer" and not developer_username:
        raise click.UsageError("'developer-username' should be set if 'authentication-method' is 'developer'")

    set_api_url(api_url)
    set_frontend_url(frontend_url)
    set_auth_backend(authentication_method, developer_username)
    set_max_age(datetime.timedelta(seconds=session_expire), datetime.timedelta(seconds=csrf_expire))


if __name__ == "__main__":
    cli(auto_envvar_prefix="WEBCLIENT")
