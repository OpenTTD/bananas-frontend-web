import datetime
import secrets
import flask
import urllib
import requests

_api_url = "http://localhost:8080"  # TODO environment or something
_frontend_url = "https://localhost:5000"  # TODO
auth_backend = {"method": "developer", "username": "frosch"}

_sessions = dict()
SESSION_COOKIE = "bananas_sid"
MAX_SESSION_AGE = datetime.timedelta(hours=16)
MAX_CSRF_AGE = datetime.timedelta(minutes=30)

app = flask.Flask("webclient")


class SessionData:
    """
    User session storage.

    @ivar sid:          Session id (cookie)
    @ivar expires:      Session expire date
    @ivar is_auth:      Whether user is authenticated.
    @ivar display_name: User's displayname, or None
    @ivar api_token:    Token for backend API.
    @ivar csrf_token:   CSRF tokens.
    """

    def __init__(self):
        self.sid = secrets.token_hex(32)
        self.expires = datetime.datetime.utcnow() + MAX_SESSION_AGE
        self.is_auth = False
        self.display_name = None
        self.api_token = None
        self.csrf_tokens = dict()

    def create_csrf_token(self, context):
        if not self.is_auth:
            return None

        token = secrets.token_hex(8)
        expires = datetime.datetime.utcnow() + MAX_SESSION_AGE
        self.csrf_tokens[token] = (context, expires)
        return token

    def validate_csrf_token(self, token, context):
        item = self.csrf_tokens.get(token)
        if item is None:
            return False

        del self.csrf_tokens[token]
        return (item[0] == context) and (datetime.datetime.utcnow() < item[1])


def cleanup_sessions():
    now = datetime.datetime.utcnow()
    for sid, session in _sessions.items():
        if now > session.expires:
            del _sessions[sid]


def start_session():
    cleanup_sessions()

    session = SessionData()
    _sessions[session.sid] = session

    @flask.after_this_request
    def set_cookie(response):
        response.set_cookie(SESSION_COOKIE, session.sid, expires=session.expires, httponly=True)
        return response

    return session


def get_session():
    sid = flask.request.cookies.get(SESSION_COOKIE)
    if sid is not None:
        session = _sessions.get(sid)
        if session is not None:
            if datetime.datetime.utcnow() < session.expires:
                return session
            else:
                stop_session()
    return None


def stop_session():
    sid = flask.request.cookies.get(SESSION_COOKIE)
    if sid is not None and sid in _sessions:
        del _sessions[sid]

    @flask.after_this_request
    def del_cookie(response):
        response.set_cookie(SESSION_COOKIE, "", max_age=0, httponly=True)
        return response


def protected(fun):
    def wrapper(*args, **kwargs):
        session = get_session()
        if session and session.api_token:
            if not session.is_auth:
                user, error = api_get(("user", ), session=session, return_errors=True)
                if error is None:
                    session.is_auth = True
                    session.display_name = user.get("display-name", "")

            if session.is_auth:
                return fun(session, *args, **kwargs)

        return redirect("login")

    wrapper.__name__ = fun.__name__
    return wrapper


def template(*args, **kwargs):
    if 'message' in kwargs:
        kwargs.setdefault('messages', []).append(kwargs['message'])

    response = flask.make_response(flask.render_template(*args, **kwargs))
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response


def external_url_for(*args, **kwargs):
    return _frontend_url + flask.url_for(*args, **kwargs)


def redirect(*args, **kwargs):
    return flask.redirect(flask.url_for(*args, **kwargs))


def not_found():
    flask.abort(404)


def api_error():
    flask.abort(500)


def api_call(method, path, params=None, json=None, session=None, return_errors=False):
    url = _api_url + "/" + "/".join(urllib.parse.quote(p, safe='') for p in path)
    headers = None
    if session and session.api_token:
        headers = {"Authorization": "Bearer " + session.api_token}
    try:
        app.logger.info("API request to '{}': {}".format(url, json))
        r = method(url, params=params, headers=headers, json=json)

        success = r.status_code in (200, 201, 204)
        if not success:
            app.logger.warning("API failed: {}".format(r.text))

        if success:
            result = None
            try:
                result = r.json()
            except Exception:
                result = None
            if return_errors:
                return (result, None)
            else:
                return result
        elif return_errors:
            error = str(r.json().get("errors", "API call failed"))
            return (None, error)
        elif r.status_code == 404:
            not_found()
        elif r.status_code == 401:
            if session and session.is_auth:
                redirect("root", message="Access denied")
            else:
                redirect("login")
    except Exception:
        pass

    if return_errors:
        return (None, "API call failed")
    else:
        api_error()


def api_get(*args, **kwargs):
    return api_call(requests.get, *args, **kwargs)


def api_post(*args, **kwargs):
    return api_call(requests.post, *args, **kwargs)


def api_put(*args, **kwargs):
    return api_call(requests.put, *args, **kwargs)


def api_delete(*args, **kwargs):
    return api_call(requests.delete, *args, **kwargs)
