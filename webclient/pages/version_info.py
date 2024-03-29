import flask
import re

from ..app import app
from ..api import (
    api_delete,
    api_get,
    api_post,
    api_put,
)
from ..helpers import (
    get_regions,
    redirect,
    template,
    tus_host,
    tus_url,
)
from ..session import protected

_dep_pattern = re.compile("([-a-z]*)/([0-9a-f]{8})/([0-9a-f]{8})$")
_branches = None
_licenses = None


def get_branches():
    global _branches
    if not _branches:
        _branches = api_get(("config", "branches"))
    return _branches


def get_licenses():
    global _licenses
    if not _licenses:
        _licenses = api_get(("config", "licenses"))
    return _licenses


def get_compatibility(version):
    data = dict((c["name"], c["conditions"]) for c in version.get("compatibility", []))

    result = []
    for branch in get_branches():
        conditions = ["", ""]
        for condition in data.get(branch["name"], []):
            if condition.startswith(">="):
                conditions[0] = condition
            elif condition.startswith("<"):
                conditions[1] = condition

        result.append((branch, conditions[0], conditions[1]))
    return result


def record_change(changes, data, key, value, empty_values=False):
    if value is None:
        return

    original = data.get(key)
    if original == value:
        return

    if empty_values and original is None and not value:
        return

    changes[key] = value


def record_change_compatibility(changes, data, form):
    compatability = []
    for branch in get_branches():
        conditions = []
        condition_min = form.get("compatibility_{}_min".format(branch["name"]), "").strip()
        condition_max = form.get("compatibility_{}_max".format(branch["name"]), "").strip()

        if condition_min:
            conditions.append(condition_min)
        if condition_max:
            conditions.append(condition_max)

        if conditions:
            compatability.append({"name": branch["name"], "conditions": conditions})

    record_change(changes, data, "compatibility", compatability, True)


def record_change_dependencies(changes, data, form, messages):
    valid_data = True
    dependencies = set()
    for dependency in form.get("dependencies").splitlines():
        dependency = dependency.strip()
        if not len(dependency):
            continue

        match = _dep_pattern.match(dependency)
        if match:
            dependencies.add((match.group(1), match.group(2), match.group(3)))
        else:
            valid_data = False
            messages.append("Invalid dependency: {}".format(dependency))

    dependencies = sorted(dependencies)
    dependencies = [{"content-type": d[0], "unique-id": d[1], "md5sum-partial": d[2]} for d in dependencies]
    record_change(changes, data, "dependencies", dependencies, True)

    return valid_data


def record_change_regions(changes, data, regions, messages):
    valid_data = True

    regions = regions.strip().splitlines()
    regions = set(r.strip() for r in regions)
    regions.discard("")
    regions = sorted(regions)

    known_regions = get_regions()
    for region in regions:
        if region not in known_regions:
            valid_data = False
            messages.append("Invalid region: {}".format(region))

    record_change(changes, data, "regions", regions, True)

    return valid_data


def record_change_description(changes, data, desc):
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

    compatibility = get_compatibility(version)

    return template("version_info.html", package=package, version=version, latest=latest, compatibility=compatibility)


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

    compatibility = get_compatibility(version)

    return template(
        "manager_version_info.html", session=session, package=package, version=version, compatibility=compatibility
    )


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
        record_change_description(changes, version, form.get("description"))

        version.update(changes)
        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")
        elif valid_data and changes:
            _, error = api_put(
                ("package", content_type, unique_id, upload_date), json=changes, session=session, return_errors=True
            )
            if error:
                messages.append(error)
            else:
                return redirect(
                    "manager_version_info",
                    content_type=content_type,
                    unique_id=unique_id,
                    upload_date=upload_date,
                    message="Data updated",
                )
        elif valid_data:
            return redirect(
                "manager_version_info", content_type=content_type, unique_id=unique_id, upload_date=upload_date
            )

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
        if not record_change_regions(changes, version, form.get("regions"), messages):
            valid_data = False
        record_change_description(changes, version, form.get("description"))

        version.update(changes)
        if not valid_csrf:
            messages.append("CSRF token expired. Please reconfirm your changes.")

        revalidate = False
        if valid_csrf:
            remove_files = set(form.get("removed_files", "").split(","))
            new_files = []
            for f in version.get("files", []):
                if f["uuid"] in remove_files:
                    api_delete(("new-package", token, f["uuid"]), session=session, return_errors=True)
                    revalidate = True
                else:
                    new_files.append(f)
            version["files"] = new_files

        if valid_csrf and valid_data and changes:
            revalidate = True
            _, error = api_put(("new-package", token), json=changes, session=session, return_errors=True)
            if error:
                messages.append(error)
                revalidate = False  # keep pending form data
            else:
                messages.append("Data updated")

        if revalidate:
            # rerun validation
            version = api_get(("new-package", token), session=session)

        if not accept_tos:
            version.setdefault("errors", []).append("TOS not accepted")

        if accept_tos and valid_csrf and valid_data and form.get("publish") is not None:
            published, error = api_post(
                ("new-package", token, "publish"), json=changes, session=session, return_errors=True
            )
            if error:
                messages.append(error)
            else:
                content_type = published.get("content-type")
                unique_id = published.get("unique-id")
                return redirect("manager_package_info", content_type=content_type, unique_id=unique_id)

    content_type = version.get("content-type")
    unique_id = version.get("unique-id")
    if content_type and unique_id:
        package, _ = api_get(("package", content_type, unique_id), session=session, return_errors=True)
    else:
        package = None

    version.setdefault("files", []).sort(key=lambda v: v.get("filename", ""))

    deps_editable = True
    compatibility = get_compatibility(version)
    licenses = get_licenses()

    csrf_token = session.create_csrf_token(csrf_context)
    response = template(
        "manager_new_package.html",
        session=session,
        package=package,
        version=version,
        compatibility=compatibility,
        licenses=licenses,
        accept_tos=accept_tos,
        deps_editable=deps_editable,
        messages=messages,
        tus_url=tus_url(),
        upload_token=token,
        csrf_token=csrf_token,
    )

    # Allow connecting to the tus host from this page. It is always on a
    # different domain than we are.
    response.headers["Content-Security-Policy"] = f"default-src 'self'; connect-src 'self' {tus_host()}"
    return response
