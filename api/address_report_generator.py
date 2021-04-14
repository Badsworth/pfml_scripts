import csv

import massgov.pfml.delegated_payments.address_validation as ad_val
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Address
from massgov.pfml.experian.physical_address.client import Client, ExperianConfig
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_suggestion_text_format,
)

experian_client = Client(config=ExperianConfig(auth_token="..."))

infile_location = "check-addresses.csv"
outfile_location = "results.csv"


def confidence_after_near_match(confidence, address, suggestions):
    if confidence != "Multiple matches":
        return confidence
    for suggestion in suggestions:
        input_address = ad_val._normalize_address_string(
            address_to_experian_suggestion_text_format(address)
        )
        if suggestion.text is not None and input_address == ad_val._normalize_address_string(
            suggestion.text
        ):
            return "Verified match"
    return confidence


with file_util.open_stream(infile_location) as fin, file_util.open_stream(
    outfile_location, "w"
) as fout:
    writer = csv.DictWriter(
        fout,
        [
            "fineos_absence_id",
            "input_address",
            "result",
            "output_address_1",
            "output_address_2",
            "output_address_3",
            "output_address_4",
            "output_address_5",
            "output_address_6",
            "output_address_7",
            "output_address_8",
        ],
    )
    writer.writeheader()
    for row in csv.DictReader(fin):
        fineos_absence_id = row.pop("fineos_absence_id")
        address = Address(**row)
        response = ad_val._experian_response_for_address(experian_client, address)
        confidence = confidence_after_near_match(
            response.result.confidence, address, response.result.suggestions
        )
        row_out = {
            "fineos_absence_id": fineos_absence_id,
            "input_address": address_to_experian_suggestion_text_format(address),
            "result": confidence,
        }
        for i, suggestion in enumerate(response.result.suggestions):
            label = "output_address_" + str(1 + i)
            row_out[label] = suggestion.text
        writer.writerow(row_out)
