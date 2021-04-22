"""Module for interacting with the Massachusetts EOLWD's Data Mart.

The "Data Mart" is a Microsoft SQL Server database providing read-only access to
data in MMARS. Data Mart is a representation of CIW (Commonwealth Information
Warehouse), which in turn is a representation of Comptroller's MMARS.
"""

from .client import Client, RealClient  # noqa: F401
from .core import (  # noqa: F401
    DataMartConfig,
    EFTStatus,
    VendorActiveStatus,
    VendorInfoResult,
    change_password_unsafe,
    get_vendor_info,
    init,
)
