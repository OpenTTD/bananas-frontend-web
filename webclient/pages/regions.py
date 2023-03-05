import flask

from ..app import app
from ..helpers import get_regions


@app.route("/regions")
def region_search():
    query = flask.request.args.get("search")

    if not query:
        return flask.jsonify({"result": []})

    regions = get_regions()

    query = query.strip()
    if len(query) < 2:
        return flask.jsonify({"result": []})

    matches = []
    for region in regions.values():
        if query.lower() in region["name"].lower():
            matches.append(region)
        if query.lower() in region["code"].lower():
            matches.append(region)

    return flask.jsonify({"result": matches})
