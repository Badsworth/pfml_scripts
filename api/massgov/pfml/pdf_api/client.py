#
# PDF client - abstract base class.
#

import abc

from requests.models import Response

from . import models

# from decimal import Decimal
# from typing import Any, List, Optional, Tuple, Union


class AbstractPDFClient(abc.ABC, metaclass=abc.ABCMeta):
    """Abstract base class for a PDF API client."""

    @abc.abstractmethod
    def updateTemplate(self) -> Response:
        pass

    @abc.abstractmethod
    def generate(self, request: models.GeneratePDFRequest) -> Response:
        pass

    @abc.abstractmethod
    def merge(self, request: models.MergePDFRequest) -> Response:
        pass
