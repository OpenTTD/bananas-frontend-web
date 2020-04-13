import flask
from webclient.main import app, template, protected, api_get, api_put


@app.route("/package/<content_type>/<unique_id>")
def package_info(content_type, unique_id):
    package = api_get(("package", content_type, unique_id))

    upgrade = package.get("replaced-by")
    if upgrade and "unique-id" in upgrade:
        upgrade_info, _ = api_get(("package", content_type, upgrade["unique-id"]), return_errors=True)
        if upgrade_info:
            upgrade.update(upgrade_info)

    package.setdefault("versions", []).sort(reverse=True, key=lambda v: v.get("upload-date", ""))

    return template("package_info.html", package=package)


def record_change(changes, data, key, value):
    if value is not None:
        o = data.get(key)
        if o is None or o != value:
            changes[key] = value


@app.route("/manager/<content_type>/<unique_id>", methods=['GET', 'POST'])
@protected
def manager_package_info(session, content_type, unique_id):
    csrf_context = ("manager_package_info", content_type, unique_id)
    package = api_get(("package", content_type, unique_id), session=session)
    messages = []

    if flask.request.method == 'POST':
        form = flask.request.form
        valid_csrf = session.validate_csrf_token(form.get("csrf_token"), csrf_context)

        any_changes = False
        success = True
        for v in package.get("versions", []):
            key = v.get("upload-date")
            if key:
                changes = dict()
                record_change(changes, v, "availability", form.get("availability_" + key))
                v.update(changes)

                if len(changes) > 0 and valid_csrf:
                    any_changes = True
                    _, error = api_put(("package", content_type, unique_id, key),
                                       json=changes, session=session, return_errors=True)
                    if error:
                        messages.append(error)
                        success = False

        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")
        elif any_changes and success:
            messages.append("Data updated")

    package.setdefault("versions", []).sort(reverse=True, key=lambda v: v.get("upload-date", ""))

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_package_info.html", session=session, package=package,
                    messages=messages, csrf_token=csrf_token)


@app.route("/manager/<content_type>/<unique_id>/edit", methods=['GET', 'POST'])
@protected
def manager_package_edit(session, content_type, unique_id):
    csrf_context = ("manager_package_edit", content_type, unique_id)
    package = api_get(("package", content_type, unique_id), session=session)
    messages = []

    if flask.request.method == 'POST':
        form = flask.request.form
        valid_csrf = session.validate_csrf_token(form.get("csrf_token"), csrf_context)

        changes = dict()
        record_change(changes, package, "name", form.get("name").strip())
        record_change(changes, package, "url", form.get("url").strip())

        tags = form.get("tags").strip().splitlines()
        tags = set(t.strip() for t in tags)
        tags.discard("")
        tags = sorted(tags)
        record_change(changes, package, "tags", tags)

        desc = "\n".join(t.rstrip() for t in form.get("description").strip().splitlines())
        record_change(changes, package, "description", desc)

        package.update(changes)
        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")
        elif len(changes) > 0:
            _, error = api_put(("package", content_type, unique_id), json=changes, session=session, return_errors=True)
            if error:
                messages.append(error)
            else:
                messages.append("Data updated")

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_package_edit.html", session=session, package=package,
                    messages=messages, csrf_token=csrf_token)
