#
# Import modules used by the API.
#
# These modules are only referenced from openapi.yaml in `operationId:` lines. Connexion normally
# imports these automatically, but certain kinds of import errors are handled by Connexion and it
# falls back to example responses.
#
# This file ensures that the modules are imported at server start and errors are raised immediately.
#

import massgov.pfml.api.applications  # noqa: F401
import massgov.pfml.api.claims  # noqa: F401
import massgov.pfml.api.eligibility.handler  # noqa: F401
import massgov.pfml.api.employees  # noqa: F401
import massgov.pfml.api.employers  # noqa: F401
import massgov.pfml.api.notifications  # noqa: F401
import massgov.pfml.api.rmv_check  # noqa: F401
import massgov.pfml.api.status  # noqa: F401
import massgov.pfml.api.users  # noqa: F401
import massgov.pfml.api.verifications  # noqa: F401
