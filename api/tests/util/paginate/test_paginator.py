import pytest

from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Claim, UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ClaimFactory,
    EmployerFactory,
    UserFactory,
)
from massgov.pfml.util.paginate.paginator import Paginator


@pytest.mark.integration
class TestPaginator:
    def test_pagination_entity(self, user, test_db_session):
        created_count = 0
        while created_count < 30:
            employer = EmployerFactory.create()
            test_db_session.add(employer)

            claim = ClaimFactory.create(employer_id=employer.employer_id)
            test_db_session.add(claim)

            application = ApplicationFactory.create(user=user, claim=claim)
            test_db_session.add(application)

            link = UserLeaveAdministrator(
                user_id=user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id=f"fake-fineos-web-id-{created_count}",
            )
            test_db_session.add(link)
            created_count += 1

        test_db_session.commit()

        for entity in [Claim, Application, UserLeaveAdministrator]:
            query_set = test_db_session.query(entity)
            pages = Paginator(query_set=query_set, page_size=10, page_offset=1)

            expected_page_attributes = [
                {
                    "offset": 1,
                    "page_size": 10,
                    "page_records": 10,
                    "total_records": 30,
                    "total_pages": 3,
                },
                {
                    "offset": 2,
                    "page_size": 10,
                    "page_records": 10,
                    "total_records": 30,
                    "total_pages": 3,
                },
                {
                    "offset": 3,
                    "page_size": 10,
                    "page_records": 10,
                    "total_records": 30,
                    "total_pages": 3,
                },
            ]

            i = 0
            for page in pages:
                expected = expected_page_attributes[i]
                assert page.offset == expected["offset"]
                assert page.size == expected["page_size"]
                assert len(page.values) == expected["page_records"]
                assert page.total_records == expected["total_records"]
                assert page.total_pages == expected["total_pages"]
                i += 1

            expected = {
                "page_records": 0,
                "page_size": 10,
                "total_records": 30,
                "total_pages": 3,
            }
            page = pages.page_at(page_offset=0)
            assert page.offset == 0
            assert page.size == expected["page_size"]
            assert len(page.values) == expected["page_records"]
            assert page.total_records == expected["total_records"]
            assert page.total_pages == expected["total_pages"]

            page = pages.page_at(page_offset=4)
            assert page.offset == 4
            assert page.size == expected["page_size"]
            assert len(page.values) == expected["page_records"]
            assert page.total_records == expected["total_records"]
            assert page.total_pages == expected["total_pages"]

    def test_pagination_total_count(self, user, test_db_session):
        other_user = UserFactory.create()
        users = [user, other_user]

        created_count = 0
        while created_count < 10:
            employer = EmployerFactory.create()
            test_db_session.add(employer)

            for each_user in users:
                claim = ClaimFactory.create(employer_id=employer.employer_id)
                test_db_session.add(claim)

                application = ApplicationFactory.create(user=each_user, claim=claim)
                test_db_session.add(application)

                link = UserLeaveAdministrator(
                    user_id=each_user.user_id,
                    employer_id=employer.employer_id,
                    fineos_web_id=f"fake-fineos-web-id-{created_count}",
                )
                test_db_session.add(link)
            created_count += 1

        test_db_session.commit()

        filter_conditions = [
            {"clause": Application.user == user, "total_count": 10},
            {"clause": Application.user == other_user, "total_count": 10,},
            {"clause": None, "total_count": 20},
        ]

        for filter_condition in filter_conditions:
            query_set = test_db_session.query(Application)
            clause = filter_condition["clause"]
            if clause is not None:
                query_set = query_set.filter(clause)

            paginator = Paginator(query_set=query_set, page_size=5, page_offset=1)
            assert paginator.total_records == filter_condition["total_count"]
