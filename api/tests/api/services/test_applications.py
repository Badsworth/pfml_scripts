from datetime import date, timedelta

from freezegun import freeze_time

from massgov.pfml.api.services.applications import split_application_by_date, split_start_end_dates
from massgov.pfml.db.models.applications import AmountFrequency, ConcurrentLeave, EmployerBenefit
from massgov.pfml.db.models.factories import (
    ConcurrentLeaveFactory,
    ContinuousLeavePeriodFactory,
    EmployerBenefitFactory,
    IntermittentLeavePeriodFactory,
    OtherIncomeFactory,
    ReducedScheduleLeavePeriodFactory,
)


class TestSplitApplicationByDate:
    class TestSplitStartEndDates:
        def test_dates_exclusively_after_split(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date + timedelta(days=10)
                end_date = split_on_date + timedelta(days=20)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )
                assert dates_before is None
                assert dates_after is not None
                assert dates_after.start_date == start_date
                assert dates_after.end_date == end_date

        def test_dates_exclusively_before_split(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=20)
                end_date = split_on_date - timedelta(days=10)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_after is None
                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == end_date

        def test_start_date_equals_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date
                end_date = split_on_date + timedelta(days=20)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == start_date
                assert dates_after is not None
                assert dates_after.start_date == split_on_date + timedelta(days=1)
                assert dates_after.end_date == end_date

        def test_end_date_equals_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = split_on_date
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == end_date
                assert dates_after is None

        def test_end_date_before_start_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = start_date - timedelta(days=1)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is None
                assert dates_after is None

        def test_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = split_on_date + timedelta(days=10)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before.start_date == start_date
                assert dates_before.end_date == split_on_date
                assert dates_after.start_date == split_on_date + timedelta(1)
                assert dates_after.end_date == end_date

    def _verify_leave_period(self, leave_period, start_date, end_date, application_id):
        assert leave_period.application_id == application_id
        if isinstance(leave_period, ConcurrentLeave):
            assert leave_period.leave_start_date == start_date
            assert leave_period.leave_end_date == end_date
        else:
            assert leave_period.start_date == start_date
            assert leave_period.end_date == end_date

    def _verify_benefit(self, benefit, start_date, end_date, amount, application_id):
        assert benefit.application_id == application_id
        if isinstance(benefit, EmployerBenefit):
            assert benefit.benefit_start_date == start_date
            assert benefit.benefit_end_date == end_date
            assert benefit.benefit_amount_dollars == amount
        else:
            assert benefit.income_start_date == start_date
            assert benefit.income_end_date == end_date
            assert benefit.income_amount_dollars == amount

    def test_split_no_leave_periods_or_benefits(self, application, test_db_session):
        split_on_date = date.today()
        split_app_1, split_app_2 = split_application_by_date(
            test_db_session, application, split_on_date
        )
        test_db_session.refresh(split_app_1)
        test_db_session.refresh(split_app_2)

        assert split_app_1.application_id == application.application_id
        assert split_app_2.application_id != application.application_id
        assert split_app_1.application_id != split_app_2.application_id
        assert split_app_1.split_into_application_id == split_app_2.application_id
        assert split_app_2.split_from_application_id == split_app_1.application_id
        assert split_app_1.claim_id is None
        assert split_app_2.claim_id is None

    def test_leave_periods_multiple_dates(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date_1 = split_on_date - timedelta(days=20)
            end_date_1 = split_on_date - timedelta(days=10)

            start_date_2 = split_on_date - timedelta(days=10)
            end_date_2 = split_on_date + timedelta(days=10)

            start_date_3 = split_on_date + timedelta(days=10)
            end_date_3 = split_on_date + timedelta(days=20)

            application.continuous_leave_periods = [
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_1,
                    end_date=end_date_1,
                ),
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_2,
                    end_date=end_date_2,
                ),
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_3,
                    end_date=end_date_3,
                ),
            ]

            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            # Apply a consistent ordering to the leave periods before validating
            split_app_1_leave_periods = split_app_1.continuous_leave_periods
            split_app_1_leave_periods.sort(key=lambda lp: lp.start_date)
            split_app_2_leave_periods = split_app_2.continuous_leave_periods
            split_app_2_leave_periods.sort(key=lambda lp: lp.start_date)

            assert len(split_app_1.continuous_leave_periods) == 2
            assert len(split_app_2.continuous_leave_periods) == 2
            self._verify_leave_period(
                split_app_1_leave_periods[0], start_date_1, end_date_1, split_app_1.application_id
            )
            self._verify_leave_period(
                split_app_1_leave_periods[1],
                start_date_2,
                split_on_date,
                split_app_1.application_id,
            )
            self._verify_leave_period(
                split_app_2_leave_periods[0],
                split_on_date + timedelta(days=1),
                end_date_2,
                split_app_2.application_id,
            )
            self._verify_leave_period(
                split_app_2_leave_periods[1], start_date_3, end_date_3, split_app_2.application_id
            )

    def test_split_multiple_type_of_leave_periods(self, application, test_db_session):
        split_on_date = date.today()
        application.continuous_leave_periods = [
            ContinuousLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.intermittent_leave_periods = [
            IntermittentLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.reduced_schedule_leave_periods = [
            ReducedScheduleLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.concurrent_leave = ConcurrentLeaveFactory.create(
            leave_start_date=split_on_date - timedelta(days=10),
            leave_end_date=split_on_date + timedelta(days=10),
            application=application,
        )
        application.has_concurrent_leave = True

        split_app_1, split_app_2 = split_application_by_date(
            test_db_session, application, split_on_date
        )
        test_db_session.refresh(split_app_1)
        test_db_session.refresh(split_app_2)

        assert len(split_app_1.all_leave_periods) == 3
        assert len(split_app_2.all_leave_periods) == 3
        for leave_period in split_app_1.all_leave_periods:
            self._verify_leave_period(
                leave_period,
                split_on_date - timedelta(days=10),
                split_on_date,
                split_app_1.application_id,
            )

        for leave_period in split_app_2.all_leave_periods:
            self._verify_leave_period(
                leave_period,
                split_on_date + timedelta(days=1),
                split_on_date + timedelta(days=10),
                split_app_2.application_id,
            )

        self._verify_leave_period(
            split_app_1.concurrent_leave,
            split_on_date - timedelta(days=10),
            split_on_date,
            split_app_1.application_id,
        )
        self._verify_leave_period(
            split_app_2.concurrent_leave,
            split_on_date + timedelta(days=1),
            split_on_date + timedelta(days=10),
            split_app_2.application_id,
        )

    def test_multiple_benefits(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=10)
            end_date = split_on_date + timedelta(days=20)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=100,
                )
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                )
            ]

            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            assert len(split_app_1.other_incomes) == 1
            assert len(split_app_2.other_incomes) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 100, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 100, split_app_2.application_id
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )

    def test_benefit_all_at_once_frequency_scenario_uneven_split(
        self, application, test_db_session
    ):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 600, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 400, split_app_2.application_id
                )

    def test_benefit_all_at_once_frequency_scenario_even_split(self, application, test_db_session):
        with freeze_time("2022-03-05"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=4)
            end_date = split_on_date + timedelta(days=5)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 500, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 500, split_app_2.application_id
                )

    def test_benefit_multiple_types_and_frequency(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                ),
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=300,
                    benefit_amount_frequency_id=AmountFrequency.PER_MONTH.amount_frequency_id,
                ),
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                    income_amount_frequency_id=AmountFrequency.PER_DAY.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 2
            assert len(split_app_2.employer_benefits) == 2
            assert len(split_app_1.other_incomes) == 1
            assert len(split_app_2.other_incomes) == 1
            for benefit in split_app_1.employer_benefits:
                amount = (
                    600
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit, start_date, split_on_date, amount, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                amount = (
                    400
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    split_on_date + timedelta(1),
                    end_date,
                    amount,
                    split_app_2.application_id,
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )

    def test_split_app_leave_periods_and_benefits(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.continuous_leave_periods = [
                ContinuousLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.intermittent_leave_periods = [
                IntermittentLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.reduced_schedule_leave_periods = [
                ReducedScheduleLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.concurrent_leave = ConcurrentLeaveFactory.create(
                leave_start_date=split_on_date - timedelta(days=10),
                leave_end_date=split_on_date + timedelta(days=10),
                application=application,
            )
            application.has_concurrent_leave = True

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                ),
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=300,
                    benefit_amount_frequency_id=AmountFrequency.PER_MONTH.amount_frequency_id,
                ),
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                    income_amount_frequency_id=AmountFrequency.PER_DAY.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.commit()
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.all_leave_periods) == 3
            assert split_app_1.has_continuous_leave_periods is True
            assert split_app_1.has_intermittent_leave_periods is True
            assert split_app_1.has_reduced_schedule_leave_periods is True
            assert split_app_1.has_employer_benefits is True
            assert split_app_1.has_other_incomes is True
            assert len(split_app_2.all_leave_periods) == 3
            assert split_app_2.has_continuous_leave_periods is True
            assert split_app_2.has_intermittent_leave_periods is True
            assert split_app_2.has_reduced_schedule_leave_periods is True
            assert split_app_2.has_employer_benefits is True
            assert split_app_2.has_other_incomes is True
            for leave_period in split_app_1.all_leave_periods:
                self._verify_leave_period(
                    leave_period,
                    split_on_date - timedelta(days=10),
                    split_on_date,
                    split_app_1.application_id,
                )

            for leave_period in split_app_2.all_leave_periods:
                self._verify_leave_period(
                    leave_period,
                    split_on_date + timedelta(days=1),
                    split_on_date + timedelta(days=10),
                    split_app_2.application_id,
                )

            self._verify_leave_period(
                split_app_1.concurrent_leave,
                split_on_date - timedelta(days=10),
                split_on_date,
                split_app_1.application_id,
            )
            self._verify_leave_period(
                split_app_2.concurrent_leave,
                split_on_date + timedelta(days=1),
                split_on_date + timedelta(days=10),
                split_app_2.application_id,
            )
            for benefit in split_app_1.employer_benefits:
                amount = (
                    600
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    start_date,
                    split_on_date,
                    amount,
                    split_app_1.application_id,
                )
            for benefit in split_app_2.employer_benefits:
                amount = (
                    400
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    split_on_date + timedelta(1),
                    end_date,
                    amount,
                    split_app_2.application_id,
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )
