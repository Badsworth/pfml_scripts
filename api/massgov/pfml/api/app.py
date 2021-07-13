#
# The API application
#

import os
import time
from contextlib import contextmanager
from typing import Generator, List, Optional, Union

import connexion
import connexion.mock
import flask
import flask_cors
import newrelic.api.time_trace
from flask import Flask, current_app, g, session
from sqlalchemy.orm import Session

import massgov.pfml.api.authorization.flask
import massgov.pfml.api.authorization.rules
import massgov.pfml.api.dashboards
import massgov.pfml.api.validation.formats
import massgov.pfml.util.logging
import massgov.pfml.util.logging.access
from massgov.pfml import db
from massgov.pfml.api.config import AppConfig, get_config
from massgov.pfml.api.validation import add_error_handlers_to_app, get_custom_validator_map
from massgov.pfml.db.models.employees import User

from .reverse_proxy import ReverseProxied

import msal

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_app(
    config: Optional[AppConfig] = None,
    check_migrations_current: bool = True,
    db_session_factory: Optional[Session] = None,
    do_close_db: bool = True,
) -> connexion.FlaskApp:
    logger.info("Creating API Application...")

    if config is None:
        config = get_config()

    # Initialize the db
    if db_session_factory is None:
        db_session_factory = db.init(
            config.db, sync_lookups=True, check_migrations_current=check_migrations_current
        )

    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    options = {"swagger_url": "/docs"}

    validator_map = get_custom_validator_map()

    app = connexion.FlaskApp(__name__, specification_dir=get_project_root_dir(), options=options)
    add_error_handlers_to_app(app)

    app.add_api(
        openapi_filenames()[0],
        resolver=resolver,
        validator_map=validator_map,
        strict_validation=True,
        validate_responses=True,
    )

    flask_app = app.app
    flask_app.config["app_config"] = config

    flask_cors.CORS(flask_app, origins=config.cors_origins, supports_credentials=True)

    #« session?
    # Set up bouncer
    authorization_path = massgov.pfml.api.authorization.rules.create_authorization(
        config.enable_employee_endpoints
    )
    bouncer = massgov.pfml.api.authorization.flask.Bouncer(flask_app)
    bouncer.authorization_method(authorization_path)

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    @flask_app.before_request
    def push_db():
        g.db = db_session_factory
        g.start_time = time.monotonic()
        massgov.pfml.util.logging.access.access_log_start(flask.request)
        newrelic.agent.add_custom_parameter(
            "api_release_version", os.environ.get("RELEASE_VERSION")
        )

    @flask_app.teardown_request
    def close_db(exception=None):
        if not do_close_db:
            logger.debug("Not closing DB session")
            return

        try:
            logger.debug("Closing DB session")
            db = g.pop("db", None)

            if db is not None:
                db.remove()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    @flask_app.after_request
    def access_log_end(response):
        response_time_ms = 1000 * (time.monotonic() - g.get("start_time"))
        massgov.pfml.util.logging.access.access_log_end(
            flask.request, response, response_time_ms, get_app_config().enable_full_error_logs
        )
        return response

    massgov.pfml.api.dashboards.init(app, config.dashboard_password)

    # @app.route("/admin/login")
    def login():
        # Technically we could use empty list [] as scopes to do just sign in,
        # here we choose to also collect end user consent upfront
        session["flow"] = _build_auth_code_flow(scopes=config.azure_sso.scopes)
        auth_url = session["flow"]["auth_uri"]
        return auth_url

    # Its absolute URL must match your app's redirect_uri set in AAD
    # @app.route(config.azure_sso.redirectUri)  
    def authorized():
        try:
            cache = _load_cache()
            result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
                session.get("flow", {}), request.args)
            if "error" in result:
                return render_template("auth_error.html", result=result)
            session["user"] = result.get("id_token_claims")
            _save_cache(cache)
        except ValueError:  # Usually caused by CSRF
            pass  # Simply ignore them
        return redirect(url_for("index"))

    # @app.route("/admin/logout")
    def logout():
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            config.azure_sso.authority + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("index", _external=True)
        )


    def _build_auth_code_flow(authority=None, scopes=None):
        return _build_msal_app(authority=authority).initiate_auth_code_flow(
            scopes or [],
            redirect_uri=url_for("authorized", _external=True))

    def _build_msal_app(cache=None, authority=None):
        return msal.ConfidentialClientApplication(
            config.azure_sso.clientId, authority=authority or config.azure_sso.authority,
            client_credential=config.azure_sso.clientSecret, token_cache=cache)

    def _save_cache(cache):
        if cache.has_state_changed:
            session["token_cache"] = cache.serialize()

    def _load_cache():
        cache = msal.SerializableTokenCache()
        if session.get("token_cache"):
            cache.deserialize(session["token_cache"])
        return cache

    def _get_token_from_cache(scope=None):
        cache = _load_cache()  # This web app maintains one cache per session
        sso = _build_msal_app(cache=cache)
        accounts = sso.get_accounts()
        if accounts:  # So all account(s) belong to the current signed-in user
            result = sso.acquire_token_silent(scope, account=accounts[0])
            _save_cache(cache)
            return result
    
    return app


def get_app_config(app: Optional[Union[connexion.FlaskApp, Flask]] = None) -> AppConfig:
    if app is None:
        app = current_app

    elif isinstance(app, connexion.FlaskApp):
        app = app.app
    else:
        app = app

    return app.config["app_config"]


def db_session_raw() -> db.Session:
    """Get a plain SQLAlchemy Session."""
    session = g.get("db")
    if session is None:
        raise Exception("No database session available in application context")

    return session


@contextmanager
def db_session(close: bool = False) -> Generator[db.Session, None, None]:
    """Get a SQLAlchemy Session wrapped in some transactional management.

    This commits session when done, rolls back transaction on exceptions,
    optionally closing the session (which disconnects any entities in the
    session, so be sure closing is what you want).
    """

    session = db_session_raw()
    with db.session_scope(session, close) as session_scoped:
        yield session_scoped


def current_user() -> Optional[User]:
    return g.get("current_user")


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "../../..")


def openapi_filenames() -> List[str]:
    return ["openapi.yaml"]
