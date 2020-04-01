#
# Dockerfile for PFML API.
#

FROM python:3.8-slim as build

# core project tools
RUN pip install poetry
RUN apt-get update && apt-get install --no-install-recommends --yes make

# setup user stuff
ARG RUN_UID
ARG RUN_USER

RUN [ "${RUN_USER}" = "root" ] || \
    (useradd -mU --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

USER ${RUN_USER}

FROM build as dev

ARG RUN_USER
USER ${RUN_USER}

WORKDIR /app

# install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# grab the application
COPY . ./

# run the server
CMD poetry run python -m massgov.pfml.api
