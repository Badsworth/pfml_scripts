from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field


class Recipient(BaseModel):
    """ Recipient model for outbound messages """

    first: Optional[str] = Field("", description="First name of recipient")
    last: Optional[str] = Field("", description="Last name of recipient")
    fineos_id: Optional[str] = Field("", description="FINEOS User ID")
    email: str = Field(..., description="Recipient email address")
    phone: Optional[str] = Field("", description="Recipient phone number")


class OutboundMessage(BaseModel):
    """ Outbound message model -- still not finalized """

    # TODO: Finalize structure of OutboundMessage - https://lwd.atlassian.net/browse/EMPLOYER-400

    recipients: List[Recipient] = Field(..., description="List of recipients for message")
    trigger: str = Field(..., description="Source trigger of message")
    absence_id: str = Field(..., description="Absence ID")
    document_id: Optional[str] = Field(None, description="Document ID for claim")
    portal_url: Optional[AnyHttpUrl] = Field(None, description="Link to portal")
