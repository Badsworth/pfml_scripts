import connexion

import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.fineos.transforms.eforms import TransformEmployerClaimReview


@requires(READ, "EMPLOYER_API")
def employer_update_claim(claim_id):
    body = connexion.request.json

    claim_request = EmployerClaimReview.parse_obj(body)

    TransformEmployerClaimReview.to_fineos(claim_request)

    claim_response = {"claim_id": claim_id}

    return response_util.success_response(
        message="Successfully updated claim", data=claim_response,
    ).to_api_response()
