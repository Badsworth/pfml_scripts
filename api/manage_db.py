# - overriding, model is being used by Migrate object
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

import massgov.pfml.api.db.models  # noqa: F401
from massgov.pfml.api import create_app, db


def main():
    app = create_app()
    flask_app = app.app
    db.init(flask_app)
    Migrate(flask_app, db.orm)
    manager = Manager(flask_app)
    manager.add_command("db", MigrateCommand)
    manager.run()


if __name__ == "__main__":
    main()
