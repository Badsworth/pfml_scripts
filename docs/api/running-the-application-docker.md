# Running the Application (Docker)

- [Initializing system dependencies](#initializing-system-dependencies)
- [Common commands](#common-commands)
- [Managing the container environment](#managing-the-container-environment)
- [Create application DB users](#create-application-db-users)

## Initializing system dependencies

The application requires a running database with some minimum level of
migrations already run as well as database users created and various other
things.

`make init` will perform the prep tasks necessary to get the application off the
ground.

## Common commands

```sh
make start    # Start the API
make logs     # View API logs
make login    # Login to the container, where you can run development tools
make login-db # Start a psql prompt in the container, where you can run SQL queries. requires make login.
make build    # Rebuild container and pick up new environment variables
make stop     # Stop all running containers
```

## Managing the container environment

Under most circumstances, a local copy of the API will run with `use_reloader=True`,
a flag given to Connexion that automatically restarts the the API's Python process if any modules have changed.
Most of the time, the `use_reloader` flag should take care of things for you, but there are
a few scenarios where you'll need to make a manual intervention in order to properly manage your container's state.

If you're doing work on a local environment, please be aware that any changes to *environment variables* or *config files*
will require a _rebuild_ of the API's Docker image. Do this with `make stop` followed by `make build.`

If you're only changing application code, you won't need to rebuild anything,
_unless_ you're changing code that runs before the `connexion_app.run` command in
[__main__.py](https://github.com/EOLWD/pfml/blob/main/api/massgov/pfml/api/__main__.py#L57).
In this case only, you'll need to restart the Docker containers with `make stop` followed by `make start`.

These scenarios are most relevant to developers who habitually work in `DOCKER_EXEC` mode,
with long-lived application and DB containers.

## Create application DB users

The migrations set up the DB roles and permissions. After the migrations have
been run, actual DB users need to be connected for the application to use.  This is typically done as part of the `make init` or `make init-db` commands and does not need to be run manually.

```sh
make db-create-users
```