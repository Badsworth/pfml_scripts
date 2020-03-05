#
# An API application using connexion.
#

import connexion
import connexion.mock

def create_app():
    # Enable mock responses for unimplemented paths.
    resolver = connexion.mock.MockResolver(mock_all=False)

    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("../../openapi.yaml",
                resolver=resolver,
                strict_validation=True,
                validate_responses=True)

    return app
