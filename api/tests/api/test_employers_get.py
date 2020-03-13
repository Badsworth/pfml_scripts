import massgov.pfml.api
import massgov.pfml.api.users
from massgov.pfml.api import generate_fake_data as fake

app = massgov.pfml.api.create_app()


def test_valid_get():
    employer = fake.create_employer()
    employer_id = employer.get("employer_id")

    # a little janky - can't figure out how to properly mock the employers dictionary so
    # I'm actually adding the employer created above directly to it
    employers = fake.employers
    employers[employer_id] = employer

    client = app.app.test_client()
    response = client.get("/v1/employers/{}".format(employer_id))
    assert response.status_code == 200


def test_invalid_get():
    client = app.app.test_client()
    response = client.get("/v1/employers/12345")
    assert response.status_code == 404
