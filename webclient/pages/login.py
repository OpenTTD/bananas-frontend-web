import flask

from ..helpers import (
    api_get,
    api_post,
    app,
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
    s = get_session()
    if s is None:
        s = start_session()

    if s.is_auth:
        return redirect("manager_package_list")
    else:
        answer = api_get(
            ("user", "login"),
            params={"method": auth_backend.get("method"), "redirect-uri": external_url_for("manager_package_list")},
        )

        s.api_token = answer.get("bearer-token")

        if auth_backend.get("method") == "developer":
            api_post(
                ("user", "developer"), json={"username": auth_backend.get("username")}, session=s, return_errors=True
            )

        url = answer.get("authorize-url")
        if url:
            return flask.redirect(url)
        else:
            return redirect("manager_package_list")


@app.route("/logout")
def logout():
    s = get_session()
    if s is not None:
        api_get(("user", "logout"), session=s, return_errors=True)
        stop_session()

    return redirect("root")
