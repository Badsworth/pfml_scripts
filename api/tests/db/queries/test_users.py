from massgov.pfml.db.queries.users import get_user_by_email


class TestGetUserByEmail:
    def test_success(self, user, test_db_session):
        db_user = get_user_by_email(test_db_session, user.email_address)

        assert db_user is not None
