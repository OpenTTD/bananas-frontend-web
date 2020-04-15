import datetime
import flask
import secrets

from .helpers import (
    api_get,
    redirect,
)
from .main import app

auth_backend = {"method": "developer", "username": "frosch"}

_sessions = dict()
SESSION_COOKIE = "bananas_sid"
MAX_SESSION_AGE = datetime.timedelta(hours=16)
MAX_CSRF_AGE = datetime.timedelta(minutes=30)


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
                user, error = api_get(("user",), session=session, return_errors=True)
                if error is None:
                    session.is_auth = True
                    session.display_name = user.get("display-name", "")

            if session.is_auth:
                return fun(session, *args, **kwargs)

        return redirect("login")

    wrapper.__name__ = fun.__name__
    return wrapper
