from webclient.main import app, redirect, get_session, start_session, stop_session


@app.route("/login")
def login():
    s = get_session()
    if s is None:
        s = start_session()

    if s.is_auth:
        return redirect("manager_package_list")
    else:
        # TODO
        return redirect("oauth2")


@app.route("/logout")
def logout():
    # TODO
    stop_session()
    return redirect("root")


@app.route("/oauth2")
def oauth2():
    s = get_session()
    if s is None:
        return redirect("root")
    elif s.is_auth:
        return redirect("manager_package_list")
    else:
        # TODO
        s.is_auth = True
        s.display_name = "Debuguser"
        return redirect("manager_package_list")
