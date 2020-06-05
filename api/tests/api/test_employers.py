import json

from massgov.pfml.api.employers import EmployerResponse
from massgov.pfml.db.models.factories import EmployerFactory


def test_get_employer_info(client):
    employer = EmployerFactory.create()
    EmployerFactory.create()

    response = client.get(f"/v1/employers/{employer.employer_id}")
    assert response.status_code == 200
    assert response.get_json() == json.loads(EmployerResponse.from_orm(employer).json())


def test_get_404(client):
    response = client.get("/v1/employers/00000000-291b-403f-a85a-15e938c26f2f")
    assert response.status_code == 404
