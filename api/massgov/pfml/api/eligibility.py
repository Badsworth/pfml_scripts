import flask

import massgov.pfml.api.generate_fake_data as fake

wages_dict = fake.wages


def eligibility_get(employee_id, leave_type):
    # this mock only determines financial eligibility not exemption, exemptions are defaulted to False currently
    eligbility_determination = {"family_exemption": False, "medical_exemption": False}

    # FINEOS will account for a number of leave types but for the mock, we're assuming that the leave type is either family or medical
    # the portal will require users to indicate the leave type they are applying for
    valid_leave_types = ["fam", "med"]

    if leave_type.lower() not in valid_leave_types:
        bad_request_code = flask.Response(status=400)
        return bad_request_code

    # grab wages and contribution for employee id. All wages are within the last 4 quarters.
    wages = wages_dict.get(employee_id)

    if not wages:
        not_found_status_code = flask.Response(status=404)
        return not_found_status_code

    sum_of_recent_wages = {}
    qtr_wages_key = "employer_qtr_wages"

    # iterate through the wages and keep a running total of earnings per quarter,
    # storing the totals in a dictionary where the key is the period id and the value is the total
    for contribution in wages:
        period_id = contribution["period_id"]

        # mock wages are hardcoded to contain data for the 4 quarters of 2019 only. For mock purposes, this will be considered the 4 most recent quarters.
        # In the real world, logic to pull wage data from the actual most recent quarters would need to be employed.
        if period_id in sum_of_recent_wages:
            sum_of_recent_wages[period_id] += contribution[qtr_wages_key]
        else:
            sum_of_recent_wages[period_id] = contribution[qtr_wages_key]

    # at least 2 qtrs are required and we can sort the values to more easily determine the 2 highest quarters
    if len(sum_of_recent_wages) >= 2:
        sorted_wages = sorted(sum_of_recent_wages.values())
        # the qtrs with the 2 highest employee contributions of the last 4 qtrs
        highest_quarter = sorted_wages[-1]
        second_highest_quarter = sorted_wages[-2]

        meets_financial_eligibility = highest_quarter + second_highest_quarter >= 5100

        eligbility_determination["eligible"] = meets_financial_eligibility
    else:
        eligbility_determination["eligible"] = False

    return eligbility_determination
