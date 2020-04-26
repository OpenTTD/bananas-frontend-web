import base64
import hashlib
import flask

from ..app import app
from ..api import (
    api_get,
    api_login_redirect,
    api_login_token,
)
from ..helpers import (
    redirect,
    template,
)
from ..session import (
    get_session,
    start_session,
    stop_session,
)

_audiences = None


def get_audiences():
    global _audiences
    if not _audiences:
        _audiences = api_get(("config", "user-audiences"))
    return _audiences


@app.route("/login", methods=["GET", "POST"])
def login():
    session = get_session()
    if session is None:
        session = start_session()

    if session and session.is_auth:
        return redirect("manager_package_list")

    audiences = get_audiences()

    if flask.request.method == "POST":
        form = flask.request.form

        if session.audience:
            # Don't authenticate twice for the same session.
            session = start_session()

        for audience in audiences:
            if audience["name"] in form:
                session.audience = audience
                break

        if session.audience:
            digest = hashlib.sha256(session.code_verifier.encode()).digest()
            code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
            return api_login_redirect(session.audience["name"], code_challenge)

    return template("login.html", audiences=audiences)


@app.route("/login-callback")
def login_callback():
    code = flask.request.args.get("code")

    session = get_session()
    if session is None:
        return redirect("login")

    if session.is_auth:
        return redirect("manager_package_list")

    answer, error = api_login_token(code, session.code_verifier)
    if error:
        return redirect("login")

    session.api_token = answer.get("access_token")

    user, error = api_get(("user",), session=session, return_errors=True)
    if error is None:
        session.is_auth = True
        session.display_name = user.get("display-name", "")

    return redirect("manager_package_list")


@app.route("/logout")
def logout():
    session = get_session()
    if session is not None:
        api_get(("user", "logout"), session=session, return_errors=True)
        stop_session()

    return redirect("root")
