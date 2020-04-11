import flask
from webclient.main import app, template, redirect, notfound, protected


@app.route("/package/<content_type>/<unique_id>")
def package_info(content_type, unique_id):
    # TODO query replaced-by for name

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla <b>bla\" bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}],
        "versions": [
            {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"},
            {"version": "0.0", "upload-date": "2016-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": None, "filesize": None}
        ]
    }

    return template("package_info.html", package=package)


@app.route("/manager/<content_type>/<unique_id>", methods=['GET', 'POST'])
@protected
def manager_package_info(session, content_type, unique_id):
    csrf_context = ("manager_package_info", content_type, unique_id)

    if flask.request.method == 'POST':
        # TODO
        pass

    # TODO query replaced-by for name

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla <b>bla\" bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}],
        "versions": [
            {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"},
            {"version": "0.0", "upload-date": "2016-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": None, "filesize": None}
        ]
    }

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_package_info.html", session=session, package=package, csrf_token=csrf_token)


@app.route("/manager/<content_type>/<unique_id>/edit", methods=['GET', 'POST'])
@protected
def manager_package_edit(session, content_type, unique_id):
    csrf_context = ("manager_package_edit", content_type, unique_id)

    if flask.request.method == 'POST':
        # TODO strip whitespace

        pass

    package = {
        "content-type": content_type,
        "unique-id" : unique_id,
        "name": "Another banana content daemon",
        "description": "bla <b>bla\" bla",
        "url": "",
        "archived": True,
        "replaced-by": {"unique-id": "ff112233", "name": "BaNaNaS 8"},
        "tags": ["old", "deprecated", "better"],
        "authors": [{"display-name": "anna"}, {"display-name": "berta"}],
        "versions": [
            {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"},
            {"version": "0.0", "upload-date": "2016-02-29T11:11:11", "md5sum-partial": "12346678", "license": "custom", "download-url": None, "filesize": None}
        ]
    }

    csrf_token = session.create_csrf_token(csrf_context)
    return template("manager_package_edit.html", session=session, package=package, csrf_token=csrf_token)
