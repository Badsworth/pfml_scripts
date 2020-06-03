import massgov.pfml.db.status as status
from massgov.pfml.db.models.employees import Status


def get_status(db_session, status_description):
    return (
        db_session.query(Status)
        .filter(Status.status_description == status_description.value)
        .one_or_none()
    )


def test_get_or_make_status_makes(test_db_session):
    status_description_to_create = status.UserStatusDescription.unverified

    # set up
    created_status_should_not_exist = get_status(test_db_session, status_description_to_create)

    assert created_status_should_not_exist is None

    # test
    status.get_or_make_status(test_db_session, status_description_to_create)

    created_status = get_status(test_db_session, status_description_to_create)

    assert created_status


def test_get_or_make_status_gets(test_db_session):
    status_description_to_get = status.UserStatusDescription.unverified

    # set up
    created_status = Status(status_description=status_description_to_get.value)
    test_db_session.add(created_status)
    test_db_session.commit()

    # test
    status.get_or_make_status(test_db_session, status_description_to_get)

    existing_status = get_status(test_db_session, status_description_to_get)

    assert existing_status == created_status
