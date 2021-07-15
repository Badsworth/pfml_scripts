# re-exported for convenience
from bouncer.constants import ALL, CREATE, EDIT, MANAGE, READ, UPDATE  # noqa: F401
from flask_bouncer import Bouncer, can, requires, skip_authorization  # noqa: F401

# implementation pieces
from flask_bouncer import ensure as flask_ensure  # isort:skip
from werkzeug.exceptions import Forbidden  # isort:skip


# Use a custom ensure that does not leak model information in the 403 `message`, which occurs when flask-bouncer raises `Forbidden`
def ensure(action, subject):
    try:
        flask_ensure(action, subject)
    except Forbidden:
        raise Forbidden()
