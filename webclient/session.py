import click
import datetime
import flask
import secrets

from .click import click_additional_options
from .helpers import redirect

_max_session_age = None
_max_csrf_age = None
_sessions = dict()

SESSION_COOKIE = "bananas_sid"


@click_additional_options
@click.option(
    "--session-expire",
    help="Time for a session to expire.",
    default=60 * 60 * 14,
    show_default=True,
    metavar="SECONDS",
)
@click.option(
    "--csrf-expire", help="Time for the CSRF token to expire.", default=60 * 30, show_default=True, metavar="SECONDS",
)
def click_max_age(session_expire, csrf_expire):
    global _max_session_age, _max_csrf_age

    _max_session_age = datetime.timedelta(seconds=session_expire)
    _max_csrf_age = datetime.timedelta(seconds=csrf_expire)


class SessionData:
    """
    User session storage.

    @ivar sid:          Session id (cookie)
    @ivar expires:      Session expire date
    @ivar is_auth:      Whether user is authenticated.
    @ivar audience:     Dict with "name" and "settings-url".
    @ivar display_name: User's displayname, or None
    @ivar api_token:    Token for backend API.
    @ivar code_verifier: Code used during authentication (part of OAuth2 PCKE flow).
    @ivar csrf_token:   CSRF tokens.
    """

    def __init__(self):
        self.sid = secrets.token_hex(32)
        self.expires = datetime.datetime.utcnow() + _max_session_age
        self.is_auth = False
        self.audience = None
        self.display_name = None
        self.api_token = None
        self.code_verifier = secrets.token_hex(32)
        self.csrf_tokens = dict()

    def create_csrf_token(self, context):
        if not self.is_auth:
            return None

        token = secrets.token_hex(8)
        expires = datetime.datetime.utcnow() + _max_csrf_age
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
    for sid, session in list(_sessions.items()):
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
        if session and session.is_auth:
            return fun(session, *args, **kwargs)

        return redirect("login")

    wrapper.__name__ = fun.__name__
    return wrapper
