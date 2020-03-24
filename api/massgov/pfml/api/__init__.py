#
# An API application using connexion.
#

import os

import connexion
import connexion.mock

import logging
from .reverse_proxy import ReverseProxied

import massgov.pfml.api.db as db

def create_app():
    logging.info("Starting API ...")

    # DB
    db.init_db()

    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    project_root_dir = os.path.join(os.path.dirname(__file__), "../../../")

    app = connexion.FlaskApp(__name__, specification_dir=project_root_dir)
    app.add_api(
        "openapi.yaml", resolver=resolver, strict_validation=True, validate_responses=True,
    )

    # Set up middleware to allow the Swagger UI to use the correct URL
    # when proxied behind the AWS API Gateway.
    flask_app = app.app
    flask_app.wsgi_app = ReverseProxied(flask_app.wsgi_app)

    return app
