from ..app import app
from ..helpers import (
    api_get,
    template,
)
from ..session import protected


@app.route("/package/<content_type>")
def package_list(content_type):
    packages = api_get(("package", content_type))

    for package in packages:
        package["latest"] = max(package.get("versions", []), default=None, key=lambda v: v.get("upload-date", ""))

    packages.sort(key=lambda p: p.get("name", ""))
    packages.sort(reverse=True, key=lambda p: p["latest"].get("upload-date", "") if p["latest"] else "")

    return template("package_list.html", content_type=content_type, packages=packages)


@app.route("/manager")
@protected
def manager_package_list(session):
    packages = api_get(("package", "self"), session=session)

    for package in packages:
        versions = package.setdefault("versions", [])
        newgame = [v for v in versions if v.get("availability", "") == "new-games"]
        package["num-all"] = len(versions)
        package["num-newgame"] = len(newgame)
        package["latest-all"] = max(versions, default=None, key=lambda v: v.get("upload-date", ""))
        package["latest-newgame"] = max(newgame, default=None, key=lambda v: v.get("upload-date", ""))

    packages.sort(key=lambda p: p.get("name", ""))
    packages.sort(reverse=True, key=lambda p: p["latest-all"].get("upload-date", "") if p["latest-all"] else "")

    return template("manager_package_list.html", session=session, packages=packages)
