# adapted from http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
    """
    Middleware that wraps the application. This allows a reverse-proxy
    like AWS API Gateway to identify the extended URL (i.e. /api/ instead of /)
    so that the Swagger UI uses the correct URL when getting the OpenAPI spec and
    making example requests against the API.

    :param app: the WSGI application
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_FORWARDED_PATH", "")
        if script_name:
            environ["SCRIPT_NAME"] = "/" + script_name.lstrip("/")

            path_info = environ["PATH_INFO"]
            if path_info.startswith(script_name):
                environ["PATH_INFO_OLD"] = path_info
                environ["PATH_INFO"] = path_info[len(script_name) :]

        scheme = environ.get("HTTP_X_SCHEME", "")
        if scheme:
            environ["wsgi.url_scheme"] = scheme

        server = environ.get("HTTP_X_FORWARDED_SERVER", "")
        if server:
            environ["HTTP_HOST"] = server

        return self.app(environ, start_response)
