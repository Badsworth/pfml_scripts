#
# Dockerfile for PFML API.
#

FROM python:3.9.7-slim-bullseye as build

# core project tools
RUN pip install poetry
RUN apt-get update \
 && apt-get install --no-install-recommends --yes \
        libffi-dev make bsdmainutils \
        build-essential git curl \
        postgresql libpq-dev gnupg ghostscript graphviz

# setup user stuff
ARG RUN_UID
ARG RUN_USER

RUN : "${RUN_USER:?RUN_USER and RUN_UID need to be set and non-empty.}" && \
    [ "${RUN_USER}" = "root" ] || \
    (useradd -mU --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

USER ${RUN_USER}

#-------------------------------------------------------------------------------
# Development build environment
#-------------------------------------------------------------------------------
FROM build as dev

ARG RUN_USER

# Set up friendly bash configuration
USER root
COPY ./local/bashrc /home/${RUN_USER}/.bashrc
COPY ./local/inputrc /home/${RUN_USER}/.inputrc
RUN rm /etc/bash.bashrc

USER ${RUN_USER}
WORKDIR /app

# install dependencies
# note: explicitly create a new virtualenv to avoid getting overridden by mounted .venv folders.
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project false && poetry env use python
RUN poetry install --no-root --extras "api-only-dependencies"

# grab the application
COPY . ./

# run the server
CMD ["poetry", "run", "python", "-m", "massgov.pfml.api"]

#-------------------------------------------------------------------------------
# Non-development build environment
#-------------------------------------------------------------------------------
FROM build as app-build

ARG RUN_USER
USER ${RUN_USER}

WORKDIR /app

# install dependencies
# use a project-local virtualenv to be easy to find
ENV POETRY_VIRTUALENVS_IN_PROJECT true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-dev --extras "api-only-dependencies"

# for simplicity, grab the whole project
COPY . ./
# then install just the application by building and installing the project
# Python package (excludes non-essential files, like tests)
RUN poetry build --format wheel && poetry run pip install 'dist/massgov.pfml.api-0.1.0-py3-none-any.whl'

#-------------------------------------------------------------------------------
# Application only
#-------------------------------------------------------------------------------
# now copy over just the installed components into the final image
FROM scratch as app

ARG RUN_USER
USER ${RUN_USER}

COPY --from=app-build /etc/passwd /etc/group /etc/
COPY --from=app-build /app/.venv /app/.venv

# Include GPG for the DOR Import task.
# Ideally this isn't included for every other ECS task/service, but we'll do it for now.
COPY --from=app-build /usr/lib/gnupg/* /usr/lib/gnupg/
COPY --from=app-build /usr/lib/gnupg2/* /usr/lib/gnupg2/
COPY --from=app-build /usr/bin/gpg /usr/bin/gpg
COPY --from=app-build /usr/bin/gpg-agent /usr/bin/gpg-agent

COPY --from=app-build /etc/ssl/* /etc/ssl/
COPY --from=app-build /usr/share/ca-certificates/* /usr/share/ca-certificates/
COPY --from=app-build /usr/local/bin/python* /usr/local/bin/

# Include etc files that link to /usr/local/lib/
COPY --from=app-build /etc/ld.so.conf /etc/ld.so.cache /etc/
COPY --from=app-build /etc/ld.so.conf.d/ /etc/ld.so.conf.d/

# Include required libs
COPY --from=app-build /usr/lib/x86_64-linux-gnu/ /usr/lib/x86_64-linux-gnu/
COPY --from=app-build /lib/* /lib/
COPY --from=app-build /usr/local/lib/ /usr/local/lib/
COPY --from=app-build /usr/local/include/python* /usr/local/include/
COPY --from=app-build /lib64/* /lib64/
COPY --from=app-build --chown=${RUN_USER} /tmp/ /tmp/

# Include ghostscript executable
COPY --from=app-build  /usr/bin/gs /usr/bin/gs
COPY --from=app-build /usr/share/ghostscript /usr/share/ghostscript
COPY --from=app-build /usr/share/man /usr/share/man
COPY --from=app-build /usr/share/fonts /usr/share/fonts
COPY --from=app-build /usr/share/fontconfig /usr/share/fontconfig
COPY --from=app-build /usr/share/color /usr/share/color

ENV PATH="/app/.venv/bin:$PATH"

# run the application
CMD ["massgov-pfml-api"]
