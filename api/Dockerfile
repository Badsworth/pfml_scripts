#
# Dockerfile for PFML API.
#

FROM python:3.8-slim

# install just dependencies
RUN pip install poetry
WORKDIR /tmp/myapp
COPY pyproject.toml poetry.lock ./
RUN cd /tmp/myapp && poetry install --no-root

# copy in everything else and install app
COPY . ./
RUN poetry install

# run the server
CMD poetry run python -m massgov.pfml.api
