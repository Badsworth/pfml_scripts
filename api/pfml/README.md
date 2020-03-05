# Connexion prototype

This is a spec-first framework for Python.

The OpenAPI spec is in mock_api.yaml.

## Setup

```
pip3 install --requirement=requirements.txt
```

Alternatively using Docker:
```
docker build --tag=pfml_api_connexion:latest .
```

## Run

```
./api.py
```

Alternatively using Docker:
```
docker run --disable-content-trust --publish=1550:1550 --rm pfml_api_connexion:latest
```

## Try it out

The /status path is not implemented and connexion returns the example
response defined in mock_api.yaml:

```
$ curl http://localhost:1550/v1/status
{
  "status": "ok",
  "version": "2020-01-29"
}
```

The /split path is implemented in handler.split_get(). See operationId in
mock_api.yaml:

```
$ curl http://localhost:1550/v1/split?message=abc+def+ghi
{
  "words": [
    "abc",
    "def",
    "ghi"
  ]
}
```

A UI is available at http://localhost:1550/v1/ui/

The spec is available at http://localhost:1550/v1/openapi.json (JSON) or
http://localhost:1550/v1/openapi.yaml (YAML).
