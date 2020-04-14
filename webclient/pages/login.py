from webclient.main import app, redirect, get_session, start_session, stop_session, api_get, api_post, external_url_for
import flask


@app.route("/login")
def login():
    s = get_session()
    if s is None:
        s = start_session()

    if s.is_auth:
        return redirect("manager_package_list")
    else:
        answer = api_get(("user", "login"), params={
            "method": "developer",  # TODO github
            "redirect-uri": external_url_for("manager_package_list").replace("http://", "https://")  # TODO replace is debug only
        })

        s.api_token = answer.get("bearer-token")

        # TODO debug only
        api_post(("user", "developer"), json={"username": "frosch"}, session=s, return_errors=True)

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
