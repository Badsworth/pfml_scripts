#
# The API application
#

import os
from contextlib import contextmanager
from typing import Generator, List, Optional, Union

import connexion
import connexion.mock
import flask
import flask_cors
from flask import Flask, current_app, g

import massgov.pfml.api.authorization.flask
import massgov.pfml.api.authorization.rules
import massgov.pfml.util.logging
import massgov.pfml.util.logging.access
from massgov.pfml import db
from massgov.pfml.api.config import AppConfig, get_config
from massgov.pfml.db.models.employees import User

from .reverse_proxy import ReverseProxied

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_app(config: Optional[AppConfig] = None) -> connexion.FlaskApp:
    logger.info("Creating API Application...")

    if config is None:
        config = get_config()

    # Initialize the db
    db_session_factory = db.init(config.db)

    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    options = {"swagger_url": "/docs"}
    app = connexion.FlaskApp(__name__, specification_dir=get_project_root_dir(), options=options)
    app.add_api(
        openapi_filenames()[0], resolver=resolver, strict_validation=True, validate_responses=True,
    )

    flask_app = app.app
    flask_app.config["app_config"] = config

    flask_cors.CORS(flask_app, origins=config.cors_origins, supports_credentials=True)

    # Set up bouncer
    bouncer = massgov.pfml.api.authorization.flask.Bouncer(flask_app)
    bouncer.authorization_method(massgov.pfml.api.authorization.rules.define_authorization)

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    @flask_app.before_request
    def push_db():
        g.db = db_session_factory

    @flask_app.teardown_request
    def close_db(exception=None):
        try:
            logger.debug("Closing DB session")
            db = g.pop("db", None)

            if db is not None:
                db.remove()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    @flask_app.after_request
    def access_log(response):
        massgov.pfml.util.logging.access.access_log(
            flask.request, response, get_app_config().enable_full_error_logs
        )
        return response

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
