from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field


class Recipient(BaseModel):
    """Recipient model for outbound messages"""

    first_name: Optional[str] = Field("", description="First name of recipient")
    last_name: Optional[str] = Field("", description="Last name of recipient")
    id: Optional[str] = Field("", description="FINEOS User ID")
    email: str = Field(..., description="Recipient email address")


class Claimant(BaseModel):
    """Claimant model for outbound messages"""

    first_name: str = Field("", description="First name of claimant")
    last_name: str = Field("", description="Last name of claimant")
    dob: str = Field("", description="DOB of claimant")
    id: str = Field("", description="Fineos customer id")


class OutboundMessage(BaseModel):
    """Outbound message model"""

    u_absence_id: str = Field(..., description="Absence ID")
    u_organization_name: str = Field(..., description="Organization name")
    u_claimant_info: str = Field(..., description="Encoded JSON of a Claimant object")
    u_document_type: str = Field(..., description="Type of available document")
    u_recipients: List[str] = Field(..., description="List of encoded JSON of Recipient objects")
    u_source: str = Field(..., description="Self-Service or Call Center")
    u_trigger: str = Field(..., description="Status change that required notification")
    u_user_type: str = Field(..., description="Leave Administrator or Claimant")
    u_link: Optional[AnyHttpUrl] = Field(None, description="Link to portal")
    u_employer_customer_number: int = Field(..., description="Fineos employer id")
