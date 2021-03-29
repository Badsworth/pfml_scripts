from decimal import Decimal

import faker

from massgov.pfml.delegated_payments.ez_check import EzCheckFile, EzCheckHeader, EzCheckRecord

fake = faker.Faker()


def EzCheckHeaderFactory(**args) -> EzCheckHeader:
    default_args = {
        "name_line_1": fake.name(),
        "name_line_2": fake.company(),
        "address_line_1": fake.street_address(),
        "address_line_2": "Bldg. " + fake.building_number(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.postcode(),
        "country": fake.country_code(),
        "account_number": fake.random_int(min=1_000_000_000_000_000, max=9_999_999_999_999_999),
        "routing_number": fake.random_int(min=10_000_000_000, max=99_999_999_999),
    }
    return EzCheckHeader(**{**default_args, **args})


def EzCheckRecordFactory(**args) -> EzCheckRecord:
    default_args = {
        "check_number": fake.random_int(min=1_000_000_000, max=9_999_999_999),
        "check_date": fake.date_between("-3w", "today"),
        "amount": Decimal(fake.random_int(min=10, max=9_999)),
        "memo": fake.sentence()[:99],
        "payee_name": fake.name(),
        "address_line_1": fake.street_address(),
        "address_line_2": "",
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.postcode(),
        "country": fake.country_code(),
    }
    return EzCheckRecord(**{**default_args, **args})


def EzCheckFileFactory() -> EzCheckFile:
    ez_check_file = EzCheckFile(EzCheckHeaderFactory())
    for _i in range(fake.random_int(min=3, max=12)):
        ez_check_file.add_record(EzCheckRecordFactory())

    return ez_check_file
