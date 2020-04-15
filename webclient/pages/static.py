from ..app import app
from ..helpers import (
    not_found,
    redirect,
    template,
)

_tos_versions = {"1.2": "tos-1.2.html"}


@app.route("/")
def root():
    return template("main.html")


@app.route("/manager/tos")
def tos_latest():
    return redirect("tos", version="1.2")


@app.route("/manager/tos/<version>")
def tos(version):
    tos = _tos_versions.get(version)
    if not tos:
        return not_found()

    return template(tos)
