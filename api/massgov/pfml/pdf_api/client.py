#
# PDF client - abstract base class.
#

import abc
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Union

from requests.models import Response

from . import models


class AbstractPDFClient(abc.ABC, metaclass=abc.ABCMeta):
    """Abstract base class for a PDF API client."""

    # @abc.abstractmethod
    # def generate(self, d: str) -> models.OCOrganisation:
    #     pass
