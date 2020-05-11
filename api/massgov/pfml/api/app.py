#
# The API application
#

import os
from typing import List, Optional, Union

import connexion
import connexion.mock
import flask_cors
from flask import Flask, current_app

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.config import AppConfig, get_config

from .reverse_proxy import ReverseProxied

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_app(config: Optional[AppConfig] = None) -> connexion.FlaskApp:
    logger.info("Creating API Application...")

    if config is None:
        config = get_config()

    # Initialize the db
    db.init(config.db)

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

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    @flask_app.teardown_request
    def close_db(exception=None):
        try:
            logger.debug("Closing DB session")
            db.get_session().remove()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    return app


def get_app_config(app: Optional[Union[connexion.FlaskApp, Flask]] = None) -> AppConfig:
    if app is None:
        app = current_app
    elif isinstance(app, connexion.FlaskApp):
        app = app.app
    else:
        app = app

    return app.config["app_config"]


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "../../../")


def openapi_filenames() -> List[str]:
    return ["openapi.yaml"]
