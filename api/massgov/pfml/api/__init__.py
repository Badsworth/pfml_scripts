#
# An API application using connexion.
#

import os

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

    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    project_root_dir = os.path.join(os.path.dirname(__file__), "../../../")

    app = connexion.FlaskApp(__name__, specification_dir=project_root_dir)
    app.add_api(
        "openapi.yaml", resolver=resolver, strict_validation=True, validate_responses=True,
    )
    flask_app = app.app
    flask_cors.CORS(flask_app, origins=config["cors_origins"], supports_credentials=True)

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    logger.info("Initializing orm object with flask app context")
    db.init(flask_app)

    return app
