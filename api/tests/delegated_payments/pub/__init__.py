# == Assertion Helpers ==


from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import PubEft, PubError
from massgov.pfml.db.models.payments import FineosWritebackDetails


def assert_pub_error(db_session, pub_error_type, message):
    pub_errors = db_session.query(PubError).all()
    assert len(pub_errors) == 1

    pub_error = pub_errors[0]
    assert pub_error.pub_error_type_id == pub_error_type.pub_error_type_id
    assert pub_error.message == message


def assert_pub_eft_prenote_state(
    db_session, pub_eft_id, prenote_state, prenote_response_reason_code=None
):
    pub_eft = (
        db_session.query(PubEft)
        .filter(
            PubEft.pub_eft_id == pub_eft_id,
            PubEft.prenote_state_id == prenote_state.prenote_state_id,
        )
        .one_or_none()
    )
    assert pub_eft is not None

    if prenote_response_reason_code:
        assert pub_eft.prenote_response_reason_code == prenote_response_reason_code


def assert_payment_state(payment, flow, end_state, db_session):
    state_log = state_log_util.get_latest_state_log_in_flow(payment, flow, db_session)

    assert state_log
    assert state_log.end_state_id == end_state.state_id


def assert_fineos_writeback_status(payment, transaction_status, db_session):
    assert (
        db_session.query(FineosWritebackDetails)
        .filter(
            FineosWritebackDetails.payment_id == payment.payment_id,
            FineosWritebackDetails.transaction_status_id
            == transaction_status.transaction_status_id,
        )
        .one_or_none()
    )
