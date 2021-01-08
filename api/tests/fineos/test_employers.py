import concurrent.futures

import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.employers as fineos_employers
from massgov.pfml.db.models.employees import EmployerLog
from massgov.pfml.db.models.factories import EmployerOnlyDORDataFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_load_all(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_all_missing_info(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    # this should never be the case, but just to test behavior
    employer_missing_name = EmployerOnlyDORDataFactory.create(employer_name=None)

    assert employer_missing_name.fineos_employer_id is None

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 2
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 1

    test_db_session.refresh(employer)
    test_db_session.refresh(employer_missing_name)

    assert employer.fineos_employer_id is not None
    assert employer_missing_name.fineos_employer_id is None


def test_load_all_skip_existing_fineos_employer_id(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create(fineos_employer_id=1)

    assert employer.fineos_employer_id == 1

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 0
    assert result.loaded_employers_count == 0
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id == 1


def test_load_all_multiple(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 10
    assert result.loaded_employers_count == 10
    assert result.errored_employers_count == 0

    for employer in employers:
        test_db_session.refresh(employer)
        assert employer.fineos_employer_id is not None


def test_load_updates_simple(test_db_session, initialize_factories_session, create_triggers):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    employer_log_entries_before = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_before) == 1

    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    employer_log_entries_after = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_after) == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_updates_multiple_log_entries_only_run_once(
    test_db_session, initialize_factories_session, create_triggers
):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    # make an update
    employer.account_key = "foo"
    test_db_session.commit()

    # and ensure it was recorded in the log table
    employer_log_entries_before = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_before) == 2

    # then test
    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    employer_log_entries_after = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_after) == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_updates_multiple(test_db_session, initialize_factories_session, create_triggers):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    employer_log_entries_before = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_before) == 10

    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 10
    assert result.loaded_employers_count == 10
    assert result.errored_employers_count == 0

    for employer in employers:
        test_db_session.refresh(employer)
        assert employer.fineos_employer_id is not None

    employer_log_entries_after = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_after) == 0


class SpecialTestException(Exception):
    """Exception only defined here for ensure mocked exception is bubbled up"""

    pass


def test_load_updates_does_not_get_stuck_in_loop_with_failing_employer(
    test_db_session, initialize_factories_session, create_triggers, monkeypatch
):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    employer_log_entries_before = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_before) == 1

    # have the call to FINEOS fail
    def mock(*args, **kwargs):
        raise SpecialTestException

    monkeypatch.setattr(fineos_client, "create_or_update_employer", mock)

    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 0
    assert result.errored_employers_count == 1

    employer_log_entries_after = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_after) == 1

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is None


def test_load_updates_picks_up_left_behind_work(
    test_db_session, initialize_factories_session, create_triggers
):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    employer_log_entries = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries) == 1

    process_id = 1

    # update the log row to indicate it had already been attempted processing by
    # this process id, simulating a failed run in the past
    test_db_session.query(EmployerLog).filter(
        EmployerLog.employer_id == employer.employer_id
    ).update({EmployerLog.process_id: process_id})

    result = fineos_employers.load_updates(test_db_session, fineos_client, process_id)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    employer_log_entries_after = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_after) == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_updates_does_not_pick_up_work_from_other_process(
    test_db_session, test_db_other_session, initialize_factories_session, create_triggers,
):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    employer_log_entries = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries) == 1

    process_id = 1

    # update the log row to indicate it had already been attempted processing by
    # this process id, simulating a failed run in the past
    test_db_session.query(EmployerLog).filter(
        EmployerLog.employer_id == employer.employer_id
    ).update({EmployerLog.process_id: process_id})
    test_db_session.commit()

    result = fineos_employers.load_updates(test_db_other_session, fineos_client, process_id=2)

    assert result.total_employers_count == 0
    assert result.loaded_employers_count == 0
    assert result.errored_employers_count == 0

    employer_log_entries_after = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries_after) == 1

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is None


def test_get_new_or_updated_employers(
    test_db_session, initialize_factories_session, create_triggers, mocker
):
    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    skip_locked_query_spy = mocker.spy(fineos_employers.db, "skip_locked_query")

    # with 10 fresh Employers, grab them 5 at a time
    employers_to_process = fineos_employers.get_new_or_updated_employers(
        test_db_session, batch_size=5, process_id=1
    )

    # for each of them, their log entry should be updated to this process
    for i, employer in enumerate(employers_to_process, 1):
        assert employer in employers

        employer_log_entries = (
            test_db_session.query(EmployerLog.process_id)
            .filter(EmployerLog.employer_id == employer.employer_id)
            .all()
        )

        assert len(employer_log_entries) == 1
        assert employer_log_entries[0].process_id == 1

        # check the batching behavior, if we are in the range of the first batch
        # of 5, the other 5 should not be marked by this process
        if i < 5:
            assert (
                test_db_session.query(EmployerLog.process_id)
                .filter(EmployerLog.process_id.is_(None))
                .count()
            ) == 5

    # should only have been called once per batch
    assert skip_locked_query_spy.call_count == 2

    # if we try to grab updates again, but only fresh ones
    employers_to_process = fineos_employers.get_new_or_updated_employers(
        test_db_session, batch_size=5, process_id=1, pickup_existing_at_start=False
    )

    # ...we should grab none
    assert len(list(employers_to_process)) == 0

    # if we try to grab updates again, but allow old ones
    employers_to_process = fineos_employers.get_new_or_updated_employers(
        test_db_session, batch_size=5, process_id=1, pickup_existing_at_start=True
    )

    # ...we should grab them all
    assert len(list(employers_to_process)) == 10

    # and all the log entries are still there, since we didn't delete them
    employer_log_entries_after = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_after) == 10


def make_test_db():
    import massgov.pfml.db as db

    return db.init()


def call_load_updates_worker(process_id, batch_size=5):
    return fineos_employers.load_updates(
        make_test_db(), massgov.pfml.fineos.MockFINEOSClient(), process_id, batch_size=batch_size
    )


def call_load_updates_worker_failure(process_id, batch_size=5):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    # have the call to FINEOS fail
    def mock(*args, **kwargs):
        raise SpecialTestException

    fineos_client.create_or_update_employer = mock

    return fineos_employers.load_updates(
        make_test_db(), fineos_client, process_id, batch_size=batch_size
    )


def spawn_multiple_load_updates(worker_funcs):
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(worker_funcs)) as executor:
        worker_futures = []
        for i, worker_func in enumerate(worker_funcs):
            worker_futures.append(executor.submit(worker_func, i))

        workers_done, workers_not_done = concurrent.futures.wait(
            worker_futures, timeout=(len(worker_funcs) * 10)
        )

        assert len(workers_not_done) == 0

        reports = [r.result() for r in workers_done]

        total_employers_count = sum([r.total_employers_count for r in reports])
        loaded_employers_count = sum([r.loaded_employers_count for r in reports])
        errored_employers_count = sum([r.errored_employers_count for r in reports])

        return (reports, total_employers_count, loaded_employers_count, errored_employers_count)


def test_load_updates_partial_failure_multiple_processes(
    test_db_session, initialize_factories_session, create_triggers
):
    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    employer_log_entries_before = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_before) == 10

    test_db_session.commit()

    (
        reports,
        total_employers_count,
        loaded_employers_count,
        errored_employers_count,
    ) = spawn_multiple_load_updates([call_load_updates_worker_failure, call_load_updates_worker])

    # ensure that both workers actually processed some employers, otherwise
    # the test is pointless
    for r in reports:
        assert r.total_employers_count > 0

    assert total_employers_count == 10
    assert loaded_employers_count == 5
    assert errored_employers_count == 5

    failed_employer_ids = set(
        map(lambda el: el.employer_id, test_db_session.query(EmployerLog.employer_id).all())
    )
    assert len(failed_employer_ids) == 5

    for employer in employers:
        test_db_session.refresh(employer)

        if employer.employer_id in failed_employer_ids:
            assert employer.fineos_employer_id is None
        else:
            assert employer.fineos_employer_id is not None


def test_load_updates_multiple_processes(
    test_db_session, initialize_factories_session, create_triggers
):
    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    employer_log_entries_before = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_before) == 10

    test_db_session.commit()

    (
        reports,
        total_employers_count,
        loaded_employers_count,
        errored_employers_count,
    ) = spawn_multiple_load_updates([call_load_updates_worker, call_load_updates_worker])

    # ensure that both workers actually processed some employers, otherwise
    # the test is pointless
    for r in reports:
        assert r.total_employers_count > 0

    assert total_employers_count == 10
    assert loaded_employers_count == 10
    assert errored_employers_count == 0

    employer_log_entries_after = test_db_session.query(EmployerLog).all()
    assert len(employer_log_entries_after) == 0

    for employer in employers:
        test_db_session.refresh(employer)
        assert employer.fineos_employer_id is not None
