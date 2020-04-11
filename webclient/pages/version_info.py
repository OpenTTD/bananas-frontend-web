import flask
from webclient.main import app, template, redirect, notfound, protected


# TODO get list of licenses from the API
_licenses = ["GPL v2", "GPL v3", "LGPL v2.1", "CC-0 v1.0", "CC-BY v3.0", "CC-BY-SA v3.0", "CC-BY-NC-SA v3.0", "CC-BY-NC-ND v3.0", "Custom"]

# TODO get list of ottd branches from the API
_branches = ["master"]


def get_compatibility(version):
    data = dict((c["name"], c["conditions"]) for c in version["compatibility"])

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


@app.route("/package/<content_type>/<unique_id>/<upload_date>")
def version_info(content_type, unique_id, upload_date):
    # TODO filter for archived = False

    # TODO query package info and replaced-by as well

    # TODO query dependencies for name/version/upload-date

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}]
    }

    latest = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "upload-date": upload_date,
        "md5sum-partial": "12346678",
    }

    version = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "upload-date": "2020-02-29T11:11:11",
        "md5sum-partial": "31415927",

        "name": "Another banana content daemon",
        "version": "0.1",
        "description": "bla bla",
        "url": "",
        "tags": ["old", "deprecated", "better"],
        "license": "custom",

        "download-url": "https://openttd.org",
        "filesize": "123456",

        "dependencies": [{"content-type": "newgrf", "unique-id": "ffffffff", "md5sum-partial": "55443322", "upload-date": "2020-02-01T01:01:01", "name": "yolo", "version": "1.23"}],
        "compatibility": [{"name": "master", "conditions": [">= 1.2", "< 1.5"]}]
    }

    # TODO figure out how to display version requirements

    return template("version_info.html", package=package, version=version, latest=latest)


@app.route("/manager/<content_type>/<unique_id>/<upload_date>")
@protected
def manager_version_info(session, content_type, unique_id, upload_date):
    # TODO query package info and replaced-by as well

    # TODO query dependencies for name/version/upload-date

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}]
    }

    latest = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "upload-date": upload_date,
        "md5sum-partial": "12346678",
    }

    version = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "upload-date": "2020-02-29T11:11:11",
        "md5sum-partial": "31415927",

        "name": "Another banana content daemon",
        "version": "0.1",
        "description": "bla bla",
        "url": "",
        "tags": ["old", "deprecated", "better"],
        "license": "custom",

        "download-url": "https://openttd.org",
        "filesize": "123456",

        "dependencies": [{"content-type": "newgrf", "unique-id": "ffffffff", "md5sum-partial": "55443322", "upload-date": "2020-02-01T01:01:01", "name": "yolo", "version": "1.23"}],
        "compatibility": [{"name": "master", "conditions": [">= 1.2", "< 1.5"]}]
    }

    # TODO figure out how to display version requirements

    return template("manager_version_info.html", session=session, package=package, version=version, latest=latest)


@app.route("/manager/<content_type>/<unique_id>/<upload_date>/edit", methods=['GET', 'POST'])
@protected
def manager_version_edit(session, content_type, unique_id, upload_date):
    csrf_context = ("manager_version_edit", content_type, unique_id, upload_date)

    if flask.request.method == 'POST':
        # TODO strip whitespace

        pass

    # TODO query dependencies for name/version/upload-date

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}]
    }

    version = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "upload-date": "2020-02-29T11:11:11",
        "md5sum-partial": "31415927",

        "name": "Another banana content daemon",
        "version": "0.1",
        "description": "bla bla",
        "url": "",
        "tags": ["old", "deprecated", "better"],
        "license": "custom",

        "download-url": "https://openttd.org",
        "filesize": "123456",

        "dependencies": [{"content-type": "newgrf", "unique-id": "ffffffff", "md5sum-partial": "55443322", "upload-date": "2020-02-01T01:01:01", "name": "yolo", "version": "1.23"}],
        "compatibility": [{"name": "master", "conditions": [">= 1.2", "< 1.5"]}]
    }

    deps_editable = True  # content_type in {"ai", "game-script"}
    compatibility = get_compatibility(version)

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_version_edit.html", session=session, package=package, version=version, compatibility=compatibility, deps_editable=deps_editable, csrf_token=csrf_token)


@app.route("/manager/new-package")
@protected
def manager_new_package(session):
    # TODO
    # TODO process optional args, like uniqueid...

    return redirect("manager_new_package_upload", token=123)


@app.route("/manager/new-package/<token>", methods=['GET', 'POST'])
@protected
def manager_new_package_upload(session, token):
    csrf_context = ("manager_new_package_upload", token)

    if flask.request.method == 'POST':
        # TODO strip whitespace

        pass

    # TODO distinguish upload package/version

    # TODO query package meta data

    package = None

    version = {
        "content-type": "newgrf",
        "unique-id" : "00FFCCDD",
        "md5sum-partial": "31415927",

        "name": "Another banana content daemon",
        "version": "0.1",
        "description": "bla bla",
        "url": "",
        "tags": ["old", "deprecated", "better"],
        "license": "Custom",
        "availability": "new-games",

        "dependencies": [{"content-type": "newgrf", "unique-id": "ffffffff", "md5sum-partial": "55443322", "upload-date": "2020-02-01T01:01:01", "name": "yolo", "version": "1.23"}],
        "compatibility": [{"name": "master", "conditions": [">= 1.2", "< 1.5"]}],

        "files": [
            {"uuid": "1", "filename": "foo.grf", "filesize": "12345"},
            {"uuid": "2", "filename": "license.txt", "filesize": "2345", "errors": ["Invalid UTF-8 encoding."]},
        ],
        "warnings": ["Don't lick pixels!"],
        "errors": ["Universe stopped expanding."]
    }

    accept_tos = False
    deps_editable = version["content-type"] in {"ai", "game-script"}
    compatibility = get_compatibility(version)

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_new_package.html", session=session, package=package, version=version, compatibility=compatibility, licenses=_licenses, accept_tos=accept_tos, deps_editable=deps_editable, csrf_token=csrf_token)
