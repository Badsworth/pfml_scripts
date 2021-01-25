import urllib.parse
from datetime import date
from enum import Enum
from typing import Optional

import sqlalchemy
from pydantic import BaseModel, BaseSettings, Field
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)

# Disable PyODBC's internal pooling
# https://docs.sqlalchemy.org/en/14/dialects/mssql.html#pyodbc-pooling-connection-close-behavior
import pyodbc  # noqa: E402 isort:skip

pyodbc.pooling = False

##########################################
# Establish Connection
##########################################


class DataMartConfig(BaseSettings):
    host: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    port: str = Field("1433", min_length=1)
    name: str = Field("DFML_DB", min_length=1)

    class Config:
        env_prefix = "CTR_DATA_MART_"


def init(config: DataMartConfig) -> Engine:
    params = urllib.parse.quote_plus(
        ";".join(
            [
                "DRIVER={ODBC Driver 17 for SQL Server}",
                f"SERVER={config.host},{config.port}",
                f"DATABASE={config.name}",
                f"UID={config.username}",
                f"PWD={config.password}",
            ]
        )
    )
    return sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)


##########################################
# Use Connection
##########################################

# Value of the valid_to_date Data Mart column that indicates "this row is
# current/latest"
VALID_TO_DATE_FOR_CURRENT = "9999-12-31"


class VendorActiveStatus(Enum):
    NULL = -9
    NOT_APPLICABLE = 0
    INACTIVE = 1
    ACTIVE = 2
    DELETE = 9


class EFTStatus(Enum):
    NOT_APPLICABLE = 0
    PRENOTE_REQUESTED = 1
    PRENOTE_PENDING = 2
    ELIGIBILE_FOR_EFT = 3
    PRENOTE_REJECTED = 4
    NOT_ELIGIBILE_FOR_EFT = 5
    EFT_HOLD = 6


class VendorInfoResult(BaseModel):
    # The unique identifier assigned to the vendor/customer. In ADVANTAGE
    # Financial, a vendor can also be a customer, allowing you to enter
    # information only one time when a particular contact is both a vendor
    # (payable) and a customer (receivable).
    vendor_customer_code: Optional[str]
    vendor_active_status: Optional[VendorActiveStatus]

    eft_status: Optional[EFTStatus]
    # Indicates that the vendor/customer accepts electronic fund transfers (EFTs).
    #
    # In the Data Mart DB, this is represented by the string character Y or N.
    generate_eft_payment: Optional[bool]
    # The American Banking Association (routing) number assigned to the bank.
    aba_no: Optional[str]
    # The reason for the prenote rejection or the electronic funds transfer
    # (EFT) hold.
    #
    # Up to 1500 characters.
    prenote_hold_reason: Optional[str]
    prenote_requested_date: Optional[date]
    # The code provided by the Automated Clearing House (ACH) Rules book to
    # identify the bank's reason for returning information related to a vendor?s
    # prenote request. Examples of codes include Rejection Reason Codes or
    # Notification of Change codes.
    #
    # 3 characters.
    prenote_return_reason: Optional[str]

    # Will always be the value of `payments_util.Constants.COMPTROLLER_AD_ID`
    # (AD010 at time of writing), but used to distinguish between "no address
    # row exists" and "address row exists, but with no information" (since some
    # or all of the address fields we select could be null)
    address_id: Optional[str]
    street_1: Optional[str]
    street_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    # 3 character country code, NULL or ... (literally a string value of three dots)
    country_code: Optional[str]


def get_vendor_info(data_mart_conn: Connection, vendor_tin: str) -> Optional[VendorInfoResult]:
    """Get information about a Vendor in MMARS via Data Mart.

    This grabs the currently valid information for the provided TIN.

    The query behavior is similar to the one_or_none() SQLAlchemy method:
    - If no rows are returned from Data Mart, None is returned
    - If multiple rows are returned from Data Mart, MultipleResultsFound is raised
    - If one row is returned from Data Mart, it will be returned from this function after parsing
    """
    results = data_mart_conn.execute(
        sqlalchemy.text(
            """
        SELECT
            vend.vendor_customer_code,
            vend.vendor_active_status,

            vend.eft_status,
            vend.generate_eft_payment,
            vend.aba_no,
            vend.prenote_hold_reason,
            vend.prenote_requested_date,
            vend.prenote_return_reason,

            vad.address_id,
            vad.street_1,
            vad.street_2,
            vad.city,
            vad.state,
            vad.zip_code,
            vad.country_code
        FROM m_reference_vendor vend
        LEFT JOIN m_reference_vendor_address vad
            ON vad.vendor_customer_code = vend.vendor_customer_code
            AND vad.address_id = :address_id
            AND vad.address_type = :address_type
            AND vad.valid_to_date = :valid_to_date_for_current
        WHERE vend.valid_to_date = :valid_to_date_for_current
          AND vend.tin = :vendor_tin
    """
        ),
        address_id=payments_util.Constants.COMPTROLLER_AD_ID,
        address_type=payments_util.Constants.COMPTROLLER_AD_TYPE,
        valid_to_date_for_current=VALID_TO_DATE_FOR_CURRENT,
        vendor_tin=vendor_tin,
    ).fetchall()

    if len(results) == 0:
        return None

    if len(results) > 1:
        raise MultipleResultsFound(
            "Multiple rows in Data Mart were returned for Vendor query when exactly one or none were expected."
        )

    result = results[0]

    return VendorInfoResult.parse_obj(dict(result.items()))


def change_password_unsafe(
    data_mart_conn: Connection, username: str, old_password: str, new_password: str
) -> None:
    """Issue ALTER LOGIN query for given user to change their password.

    Due to the way ALTER LOGIN works, this function does not properly escape
    values in the query and so should not be used with untrusted inputs.
    """
    if new_password == old_password:
        return

    data_mart_conn.execute(
        sqlalchemy.text(
            f"ALTER LOGIN [{username}] WITH PASSWORD = '{new_password}' OLD_PASSWORD = '{old_password}'"
        ),
    )
