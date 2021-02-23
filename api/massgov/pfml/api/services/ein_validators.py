from typing import Optional

import massgov.pfml.db as db
from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.db.models.applications import Employer


def get_contributing_employer_issue(
    db_session: db.Session, maybe_employer_fein: Optional[str]
) -> Optional[Issue]:
    """Validate an Employer exists in the API and CPS for the given EIN"""

    # Requiring an EIN be present is handled by a separate validation rule
    if maybe_employer_fein is not None:
        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == maybe_employer_fein)
            .one_or_none()
        )

        # Employer was not in DOR data, or we haven't yet created the corresponding record in FINEOS
        if employer is None or employer.fineos_employer_id is None:
            return Issue(
                field="employer_fein",
                type=IssueType.require_contributing_employer,
                message="Confirm that you have the correct EIN, and that the Employer is contributing to Paid Family and Medical Leave.",
            )

    return None
