import base64
import hashlib

from flask import request

from ..app import app
from ..helpers import (
    api_get,
    api_login_redirect,
    api_login_token,
    redirect,
)
from ..session import (
    auth_backend,
    get_session,
    start_session,
    stop_session,
)


@app.route("/login")
def login():
    session = get_session()
    if session is None:
        session = start_session()

    if session.is_auth:
        return redirect("manager_package_list")

    digest = hashlib.sha256(session.code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

    return api_login_redirect(auth_backend.get("method"), code_challenge)


@app.route("/login-callback")
def login_callback():
    code = request.args.get("code")

    session = get_session()
    if session is None:
        return redirect("login")

    if session.is_auth:
        return redirect("manager_package_list")

    answer, error = api_login_token(code, session.code_verifier)
    if error:
        return redirect("login")

    session.api_token = answer.get("access_token")
    return redirect("manager_package_list")


@app.route("/logout")
def logout():
    session = get_session()
    if session is not None:
        api_get(("user", "logout"), session=session, return_errors=True)
        stop_session()

    return redirect("root")
