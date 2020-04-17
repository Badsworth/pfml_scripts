from werkzeug.exceptions import NotFound

import massgov.pfml.api.generate_fake_data as fake

employers_dict = fake.employers


def employers_get(employer_id):
    employer = employers_dict.get(employer_id)

    if not employer:
        raise NotFound()

    return employer
