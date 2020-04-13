from webclient.main import app, template, protected, api_get


@app.route("/package/<content_type>")
def package_list(content_type):
    packages = api_get(("package", content_type))

    for p in packages:
        p["latest"] = max(p.get("versions", []), default=None, key=lambda v: v.get("upload-date", ""))

    # TODO filter for archived = False ?
    packages.sort(key=lambda p: p.get("name", ""))
    packages.sort(reverse=True, key=lambda p: p["latest"].get("upload-date", "") if p["latest"] else "")

    return template("package_list.html", content_type=content_type, packages=packages)


@app.route("/manager")
@protected
def manager_package_list(session):
    packages = api_get(("package", "self"), session=session)

    for p in packages:
        versions = p.setdefault("versions", [])
        newgame = [v for v in versions if v.get("availability", "") == "new-games"]
        p["num-all"] = len(versions)
        p["num-newgame"] = len(newgame)
        p["latest-all"] = max(versions, default=None, key=lambda v: v.get("upload-date", ""))
        p["latest-newgame"] = max(newgame, default=None, key=lambda v: v.get("upload-date", ""))

    packages.sort(key=lambda p: p.get("name", ""))
    packages.sort(reverse=True, key=lambda p: p["latest-all"].get("upload-date", "") if p["latest-all"] else "")

    return template("manager_package_list.html", session=session, packages=packages)
