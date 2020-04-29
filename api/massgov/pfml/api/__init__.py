#
# An API application using connexion.
#

import os
from typing import List

import connexion
import connexion.mock
import flask_cors

import massgov.pfml.util.logging
from massgov.pfml.api import db

from .config import config
from .reverse_proxy import ReverseProxied

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_app():
    logger.info("Starting API ...")

    # Initialize the db
    db.init()

    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    options = {"swagger_url": "/docs"}
    app = connexion.FlaskApp(__name__, specification_dir=get_project_root_dir(), options=options)
    app.add_api(
        openapi_filenames()[0], resolver=resolver, strict_validation=True, validate_responses=True,
    )

    flask_app = app.app
    flask_cors.CORS(flask_app, origins=config["cors_origins"], supports_credentials=True)

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    return app


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "../../../")


def openapi_filenames() -> List[str]:
    return ["openapi.yaml"]
