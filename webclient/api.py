import click
import flask
import requests
import urllib

from .app import app
from .click import click_additional_options
from .helpers import (
    api_host,
    external_url_for,
    redirect,
)
from .session import stop_session

_client_id = None


@click_additional_options
@click.option("--client-id", help="Client-id to use for authentication", default="webclient", show_default=True)
def click_api(client_id):
    global _client_id
    _client_id = client_id


def api_login_redirect(audience, code_challenge):
    params = {
        "audience": audience,
        "response_type": "code",
        "client_id": _client_id,
        "redirect_uri": external_url_for("login_callback"),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = api_host() + "/user/authorize?" + urllib.parse.urlencode(params)
    return flask.redirect(url)


def api_login_token(code, code_verifier):
    return api_post(
        ("user", "token"),
        json={
            "client_id": _client_id,
            "code_verifier": code_verifier,
            "code": code,
            "redirect_uri": external_url_for("login_callback"),
            "grant_type": "authorization_code",
        },
        return_errors=True,
    )


def api_call(method, path, params=None, json=None, session=None, return_errors=False):
    url = api_host() + "/" + "/".join(urllib.parse.quote(p, safe="") for p in path)
    headers = None
    if session and session.api_token:
        headers = {"Authorization": "Bearer " + session.api_token}

    error_response = redirect("root", message="Something failed, sorry for the inconvenience")
    try:
        r = method(url, params=params, headers=headers, json=json)

        success = r.status_code in (200, 201, 204)
        if not success:
            app.logger.warning("API failed: {} {}".format(r.status_code, r.text))

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
        elif r.status_code == 404:
            if return_errors:
                return (None, "Data not found")
            error_response = redirect("root", message="Data not found")
        elif r.status_code == 401:
            # No login yet, or API key expired. Reset session.
            stop_session()
            if return_errors:
                return (None, "Login required")
            error_response = redirect("login")
        elif return_errors:
            error = str(r.json().get("errors", "API call failed"))
            return (None, error)
    except Exception:
        # If anything failed we did not capture, return the latest error we
        # have to the caller
        pass

    if not return_errors:
        flask.abort(error_response)

    return (None, "API call failed")


def api_get(*args, **kwargs):
    return api_call(requests.get, *args, **kwargs)


def api_post(*args, **kwargs):
    return api_call(requests.post, *args, **kwargs)


def api_put(*args, **kwargs):
    return api_call(requests.put, *args, **kwargs)


def api_delete(*args, **kwargs):
    return api_call(requests.delete, *args, **kwargs)
