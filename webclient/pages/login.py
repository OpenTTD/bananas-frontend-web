import flask

from ..app import app
from ..helpers import (
    api_get,
    api_post,
    external_url_for,
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

    answer = api_get(
        ("user", "login"),
        params={"method": auth_backend.get("method"), "redirect-uri": external_url_for("manager_package_list")},
    )

    session.api_token = answer.get("bearer-token")

    if auth_backend.get("method") == "developer":
        api_post(
            ("user", "developer"),
            json={"username": auth_backend.get("developer-username")},
            session=session,
            return_errors=True,
        )

    url = answer.get("authorize-url")
    if url:
        return flask.redirect(url)

    return redirect("manager_package_list")


@app.route("/logout")
def logout():
    session = get_session()
    if session is not None:
        api_get(("user", "logout"), session=session, return_errors=True)
        stop_session()

    return redirect("root")
