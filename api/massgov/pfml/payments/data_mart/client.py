import abc
from typing import Optional

from massgov.pfml.payments.data_mart.core import (
    DataMartConfig,
    VendorInfoResult,
    get_vendor_info,
    init,
)


class Client(abc.ABC, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_vendor_info(self, vendor_tin: str) -> Optional[VendorInfoResult]:
        return None


class RealClient(Client):
    def __init__(self, config: Optional[DataMartConfig] = None):
        if not config:
            config = DataMartConfig()

        self.config = config
        self.engine = init(config)

    def get_vendor_info(self, vendor_tin: str) -> Optional[VendorInfoResult]:
        with self.engine.connect() as data_mart_conn:
            return get_vendor_info(data_mart_conn, vendor_tin)
