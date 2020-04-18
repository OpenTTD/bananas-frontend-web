import click
import flask
import requests
import urllib

from .app import app
from .click import click_additional_options

_api_url = None
_frontend_url = None
_tus_url = None  # None means equal to _api_url


@click_additional_options
@click.option(
    "--api-url", help="BaNaNaS API URL.", default="https://api.bananas.openttd.org", show_default=True, metavar="URL",
)
@click.option(
    "--tus-url",
    help="Tus upload URL. Only set this, if different from API URL.",
    default=None,
    show_default=False,
    metavar="URL",
)
@click.option(
    "--frontend-url",
    help="Frontend URL (this server).",
    default="https://bananas.openttd.org",
    show_default=True,
    metavar="URL",
)
def click_urls(api_url, frontend_url, tus_url):
    global _api_url, _frontend_url, _tus_url
    _api_url = api_url
    _frontend_url = frontend_url
    _tus_url = tus_url


def template(*args, **kwargs):
    if "message" in kwargs:
        kwargs.setdefault("messages", []).append(kwargs["message"])

    response = flask.make_response(flask.render_template(*args, **kwargs))
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


def external_url_for(*args, **kwargs):
    return _frontend_url + flask.url_for(*args, **kwargs)


def tus_host():
    return _tus_url


def tus_url():
    return urllib.parse.urljoin(_tus_url or _api_url, "/new-package/tus/")


def redirect(*args, **kwargs):
    return flask.redirect(flask.url_for(*args, **kwargs))


def not_found():
    flask.abort(404)


def api_error():
    flask.abort(500)


def api_call(method, path, params=None, json=None, session=None, return_errors=False):
    url = _api_url + "/" + "/".join(urllib.parse.quote(p, safe="") for p in path)
    headers = None
    if session and session.api_token:
        headers = {"Authorization": "Bearer " + session.api_token}
    try:
        r = method(url, params=params, headers=headers, json=json)

        success = r.status_code in (200, 201, 204)
        if not success:
            app.logger.warning("API failed: {}".format(r.text))

        if success:
            result = None
            try:
                result = r.json()
            except Exception:
                result = None
            if return_errors:
                return (result, None)
            else:
                return result
        elif return_errors:
            error = str(r.json().get("errors", "API call failed"))
            return (None, error)
        elif r.status_code == 404:
            not_found()
        elif r.status_code == 401:
            if session and session.is_auth:
                redirect("root", message="Access denied")
            else:
                redirect("login")
    except Exception:
        pass

    if return_errors:
        return (None, "API call failed")
    else:
        api_error()


def api_get(*args, **kwargs):
    return api_call(requests.get, *args, **kwargs)


def api_post(*args, **kwargs):
    return api_call(requests.post, *args, **kwargs)


def api_put(*args, **kwargs):
    return api_call(requests.put, *args, **kwargs)


def api_delete(*args, **kwargs):
    return api_call(requests.delete, *args, **kwargs)
