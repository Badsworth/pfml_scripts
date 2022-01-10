from massgov.pfml.db.models.applications import DocumentType

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
