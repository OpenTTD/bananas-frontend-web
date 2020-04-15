import flask
import re

from ..helpers import (
    api_delete,
    api_get,
    api_post,
    api_put,
    app,
    redirect,
    template,
)
from ..session import protected


_licenses = [
    "GPL v2",
    "GPL v3",
    "LGPL v2.1",
    "CC-0 v1.0",
    "CC-BY v3.0",
    "CC-BY-SA v3.0",
    "CC-BY-NC-SA v3.0",
    "CC-BY-NC-ND v3.0",
    "Custom",
]
_branches = ["master"]
_dep_pattern = re.compile("([-a-z]*)/([0-9a-f]{8})/([0-9a-f]{8})$")


def get_compatibility(version):
    data = dict((c["name"], c["conditions"]) for c in version.get("compatibility", []))

    res = []
    for b in _branches:
        c = ["", ""]
        for s in data.get(b, []):
            if s.startswith(">="):
                c[0] = s
            elif s.startswith("<"):
                c[1] = s

        res.append((b, c[0], c[1]))
    return res


def record_change(changes, data, key, value, empty_values=False):
    if value is None:
        return

    o = data.get(key)
    if o == value:
        return

    if empty_values and (o is None) and (not value):
        return

    changes[key] = value


def record_change_compatibility(changes, data, form):
    compat = []
    for b in _branches:
        conds = []
        c1 = form.get("compatibility_{}_min".format(b), "").strip()
        c2 = form.get("compatibility_{}_max".format(b), "").strip()

        if c1:
            conds.append(c1)
        if c2:
            conds.append(c2)

        if conds:
            compat.append({"name": b, "conditions": conds})

    record_change(changes, data, "compatibility", compat, True)


def record_change_dependencies(changes, data, form, messages):
    valid_data = True
    deps = set()
    for d in form.get("dependencies").splitlines():
        d = d.strip()
        if len(d) == 0:
            continue
        m = _dep_pattern.match(d)
        if m:
            deps.add((m.group(1), m.group(2), m.group(3)))
        else:
            valid_data = False
            messages.append("Invalid dependency: {}".format(d))
    deps = sorted(deps)
    deps = [{"content-type": d[0], "unique-id": d[1], "md5sum-partial": d[2]} for d in deps]
    record_change(changes, data, "dependencies", deps, True)

    return valid_data


def record_change_tags(changes, data, tags):
    tags = tags.strip().splitlines()
    tags = set(t.strip() for t in tags)
    tags.discard("")
    tags = sorted(tags)
    record_change(changes, data, "tags", tags, True)


def record_change_descripton(changes, data, desc):
    desc = "\n".join(t.rstrip() for t in desc.strip().splitlines())
    record_change(changes, data, "description", desc, True)


@app.route("/package/<content_type>/<unique_id>/<upload_date>")
def version_info(content_type, unique_id, upload_date):
    version = api_get(("package", content_type, unique_id, upload_date))
    package = api_get(("package", content_type, unique_id))

    latest = max(package.get("versions", []), default=None, key=lambda v: v.get("upload-date", ""))
    if latest and latest.get("upload-date", "") == version.get("upload-date", ""):
        latest = None

    upgrade = package.get("replaced-by")
    if upgrade and "unique-id" in upgrade:
        upgrade_info, _ = api_get(("package", content_type, upgrade["unique-id"]), return_errors=True)
        if upgrade_info:
            upgrade.update(upgrade_info)

    for dep in version.get("dependencies", []):
        dep_package, _ = api_get(("package", dep.get("content-type", ""), dep.get("unique-id", "")), return_errors=True)
        if dep_package:
            dep_version = list(
                filter(lambda v: v.get("md5sum-partial") == dep.get("md5sum-partial"), dep_package.get("versions", []))
            )
            dep.update(dep_package)
            if len(dep_version) == 1:
                dep.update(dep_version[0])

    return template("version_info.html", package=package, version=version, latest=latest)


@app.route("/manager/<content_type>/<unique_id>/<upload_date>")
@protected
def manager_version_info(session, content_type, unique_id, upload_date):
    version = api_get(("package", content_type, unique_id, upload_date), session=session)
    package = api_get(("package", content_type, unique_id), session=session)

    for dep in version.get("dependencies", []):
        dep_package, _ = api_get(
            ("package", dep.get("content-type", ""), dep.get("unique-id", "")), session=session, return_errors=True
        )
        if dep_package:
            dep_version = list(
                filter(lambda v: v.get("md5sum-partial") == dep.get("md5sum-partial"), dep_package.get("versions", []))
            )
            dep.update(dep_package)
            if len(dep_version) == 1:
                dep.update(dep_version[0])

    return template("manager_version_info.html", session=session, package=package, version=version)


@app.route("/manager/<content_type>/<unique_id>/<upload_date>/edit", methods=["GET", "POST"])
@protected
def manager_version_edit(session, content_type, unique_id, upload_date):
    csrf_context = ("manager_version_edit", content_type, unique_id, upload_date)
    version = api_get(("package", content_type, unique_id, upload_date), session=session)
    package = api_get(("package", content_type, unique_id), session=session)
    messages = []

    if flask.request.method == "POST":
        form = flask.request.form
        valid_csrf = session.validate_csrf_token(form.get("csrf_token"), csrf_context)

        valid_data = True
        changes = dict()
        record_change(changes, version, "name", form.get("name").strip(), True)
        record_change(changes, version, "url", form.get("url").strip(), True)
        record_change(changes, version, "version", form.get("version").strip())
        record_change_compatibility(changes, version, form)
        if not record_change_dependencies(changes, version, form, messages):
            valid_data = False
        record_change_tags(changes, version, form.get("tags"))
        record_change_descripton(changes, version, form.get("description"))

        version.update(changes)
        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")
        elif valid_data and len(changes):
            _, error = api_put(
                ("package", content_type, unique_id, upload_date), json=changes, session=session, return_errors=True
            )
            if error:
                messages.append(error)
            else:
                messages.append("Data updated")

    deps_editable = True
    compatibility = get_compatibility(version)

    csrf_token = session.create_csrf_token(csrf_context)
    return template(
        "manager_version_edit.html",
        session=session,
        package=package,
        version=version,
        compatibility=compatibility,
        deps_editable=deps_editable,
        messages=messages,
        csrf_token=csrf_token,
    )


@app.route("/manager/new-package")
@protected
def manager_new_package(session):
    new = api_post(("new-package",), json={}, session=session)
    return redirect("manager_new_package_upload", token=new.get("upload-token", ""))


@app.route("/manager/new-package/<token>", methods=["GET", "POST"])
@protected
def manager_new_package_upload(session, token):
    csrf_context = ("manager_new_package_upload", token)
    version = api_get(("new-package", token), session=session)
    accept_tos = False
    messages = []

    if flask.request.method == "POST":
        form = flask.request.form
        valid_csrf = session.validate_csrf_token(form.get("csrf_token"), csrf_context)
        accept_tos = form.get("tos", "") == "accepted"

        valid_data = True
        changes = dict()
        record_change(changes, version, "name", form.get("name").strip(), True)
        record_change(changes, version, "url", form.get("url").strip(), True)
        record_change(changes, version, "version", form.get("version").strip())
        if form.get("license", "empty") != "empty":
            record_change(changes, version, "license", form.get("license").strip())
        record_change_compatibility(changes, version, form)
        if not record_change_dependencies(changes, version, form, messages):
            valid_data = False
        record_change_tags(changes, version, form.get("tags"))
        record_change_descripton(changes, version, form.get("description"))

        version.update(changes)
        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")
        elif valid_data and len(changes):
            _, error = api_put(("new-package", token), json=changes, session=session, return_errors=True)
            if error:
                messages.append(error)
            else:
                # rerun validation
                version = api_get(("new-package", token), session=session)
                messages.append("Data updated")

        new_files = []
        for f in version.get("files", []):
            if form.get("delete_{}".format(f["uuid"])) is not None:
                _, error = api_delete(("new-package", token, f["uuid"]), session=session, return_errors=True)
            else:
                new_files.append(f)
        version["files"] = new_files

        if not accept_tos:
            version.setdefault("errors", []).append("TOS not accepted")

        if accept_tos and valid_data and form.get("publish") is not None:
            _, error = api_put(("new-package", token, "publish"), json=changes, session=session, return_errors=True)
            if error:
                messages.append(error)
            else:
                content_type = version.get("content-type")
                unique_id = version.get("unique-id")
                redirect("manager_package_info", content_type=content_type, unique_id=unique_id)

    content_type = version.get("content-type")
    unique_id = version.get("unique-id")
    if content_type and unique_id:
        package = api_get(("package", content_type, unique_id), session=session)
    else:
        package = None

    deps_editable = True
    compatibility = get_compatibility(version)

    csrf_token = session.create_csrf_token(csrf_context)
    return template(
        "manager_new_package.html",
        session=session,
        package=package,
        version=version,
        compatibility=compatibility,
        licenses=_licenses,
        accept_tos=accept_tos,
        deps_editable=deps_editable,
        messages=messages,
        csrf_token=csrf_token,
    )
