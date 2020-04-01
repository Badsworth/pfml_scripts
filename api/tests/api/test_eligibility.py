import massgov.pfml.api.generate_fake_data as fake

employee_id = "009fa369-291b-403f-a85a-15e938c26a7b"


def test_ineligible(client):
    fake.wages[employee_id] = [
        {
            "employee_fam_contribution": 325,
            "employee_id": employee_id,
            "employee_medical_contribution": 500,
            "employer_fam_contribution": 600,
            "employer_id": "009fa369-291b-403f-a85a-15e938c2c3f4",
            "employer_medical_contribution": 1000,
            "employer_qtr_wages": 3500,
            "employer_ytd_wages": 3500,
            "independent_contractor": True,
            "opt_in": True,
            "period_id": "2019-03-31",
        }
    ]

    response = client.get("/v1/eligibility/{}?leave_type=fam".format(employee_id))
    assert response.status_code == 200
    assert response.json["eligible"] is False


def test_eligible(client):
    fake.wages[employee_id] = [
        {
            "employee_fam_contribution": 2600,
            "employee_id": employee_id,
            "employee_medical_contribution": 975,
            "employer_fam_contribution": 4600,
            "employer_id": "009fa369-291b-403f-a85a-15e938c2c3f4",
            "employer_medical_contribution": 2000,
            "employer_qtr_wages": 5000,
            "employer_ytd_wages": 25000,
            "independent_contractor": True,
            "opt_in": True,
            "period_id": "2019-12-31",
        },
        {
            "employee_fam_contribution": 2500,
            "employee_id": employee_id,
            "employee_medical_contribution": 975,
            "employer_fam_contribution": 4600,
            "employer_id": "009fa369-291b-403f-a85a-15e938c2c3f4",
            "employer_medical_contribution": 2000,
            "employer_qtr_wages": 5000,
            "employer_ytd_wages": 25000,
            "independent_contractor": True,
            "opt_in": True,
            "period_id": "2019-09-30",
        },
    ]

    response = client.get("/v1/eligibility/{}?leave_type=fam".format(employee_id))
    assert response.status_code == 200
    assert response.json["eligible"] is True


def test_invalid_query(client):
    fake.wages[employee_id] = [
        {
            "employee_fam_contribution": 975,
            "employee_id": employee_id,
            "employee_medical_contribution": 975,
            "employer_fam_contribution": 2000,
            "employer_id": "009fa369-291b-403f-a85a-15e938c2c3f4",
            "employer_medical_contribution": 2000,
            "employer_qtr_wages": 5000,
            "employer_ytd_wages": 25000,
            "independent_contractor": True,
            "opt_in": True,
            "period_id": "2019-03-31",
        }
    ]

    response = client.get("/v1/eligibility/{}?leave_type=nope".format(employee_id))
    assert response.status_code == 400
