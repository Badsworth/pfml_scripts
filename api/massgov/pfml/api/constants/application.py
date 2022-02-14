from datetime import date

from massgov.pfml.db.models.applications import DocumentType

CARING_LEAVE_EARLIEST_START_DATE = date(2021, 7, 1)
PFML_PROGRAM_LAUNCH_DATE = date(2021, 1, 1)

ID_DOC_TYPES = [
    DocumentType.PASSPORT,
    DocumentType.DRIVERS_LICENSE_MASS,
    DocumentType.DRIVERS_LICENSE_OTHER_STATE,
    DocumentType.IDENTIFICATION_PROOF,
]


CERTIFICATION_DOC_TYPES = [
    DocumentType.OWN_SERIOUS_HEALTH_CONDITION_FORM,
    DocumentType.CHILD_BONDING_EVIDENCE_FORM,
]
