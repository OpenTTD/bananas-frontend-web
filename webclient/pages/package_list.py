from webclient.main import app, template, notfound, protected


@app.route("/package/<content_type>")
def package_list(content_type):
    # TODO parse content_type

    # TODO filter for archived = False

    packages = [
        {"content-type": content_type, "unique-id": "aabbccdd", "name": "Another banana content daemon", "url": "",
         "latest": {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"}},
        {"content-type": content_type, "unique-id": "ff117755", "name": "Finnish industrial replacement syndicate", "url": "https://opentt\">d.org", "latest": None},
    ]

    return template("package_list.html", content_type=content_type, packages=packages)


@app.route("/manager")
@protected
def manager_package_list(session):

    # TODO count num-all, num-newgame
    # TODO fetch info for latest-all and latest-newgame

    packages = [
        {"content-type": "NewGRF", "unique-id": "aabbccdd", "name": "Another banana content daemon", "url": "",
         "num-all": 12, "num-newgame": 1,
         "latest-all": {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"},
         "latest-newgame": {"version": "0.1", "upload-date": "2020-02-29T11:11:11", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"}},
        {"content-type": "NewGRF", "unique-id": "ff117755", "name": "Finnish industrial replacement syndicate", "url": "https://opentt\">d.org",
         "num-all": 31, "num-newgame": 0,
         "latest-all": {"version": "3.5", "upload-date": "2010-02-29T11:11:11", "license": "custom", "download-url": "https://openttd.org", "filesize": "123456"},
         "latest-newgame": None
         },
    ]

    return template("manager_package_list.html", session=session, packages=packages)
