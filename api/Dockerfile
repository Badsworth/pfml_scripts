#
# Dockerfile for PFML API.
#

FROM python:3.8-slim as build

# core project tools
RUN pip install poetry
RUN apt-get update && apt-get install --no-install-recommends --yes make postgresql build-essential

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
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# grab the application
COPY . ./

# run the server
CMD poetry run python -m massgov.pfml.api

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
RUN poetry install --no-root --no-dev

# for simplicity, grab the whole project
COPY . ./
# then install just the application by building and installing the project
# Python package (excludes non-essential files, like tests)
RUN poetry build --format wheel && poetry run pip install dist/*.whl

#-------------------------------------------------------------------------------
# Application only
#-------------------------------------------------------------------------------
# now copy over just the installed components into the final image
FROM python:3.8-slim as app

ARG RUN_USER
USER ${RUN_USER}

COPY --from=app-build /etc/passwd /etc/group /etc/
COPY --from=app-build /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

# run the application
CMD massgov-pfml-api
