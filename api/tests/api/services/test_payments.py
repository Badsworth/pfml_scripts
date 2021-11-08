from massgov.pfml.api.services.payments import get_payments_from_db
from massgov.pfml.db.models.factories import ImportLogFactory, PaymentFactory
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


def test_get_payments_from_db_dedups_pei_i_value(test_db_session, initialize_factories_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_extract_import_log_id=import_log_1.import_log_id,
        fineos_pei_i_value="9999",
    )
    claim = payment_factory.get_or_create_claim()
    payment = payment_factory.get_or_create_payment()

    import_log_2 = ImportLogFactory.create()
    payment2 = PaymentFactory.create(
        claim=claim,
        fineos_extract_import_log=import_log_2,
        fineos_pei_i_value="9999",
        payment_transaction_type=payment.payment_transaction_type,
    )

    assert import_log_2.import_log_id > import_log_1.import_log_id

    payments = get_payments_from_db(test_db_session, claim.claim_id)

    assert len(payments) == 1
    assert payments[0].payment_id == payment2.payment_id
    assert payments[0].fineos_extract_import_log == import_log_2
    assert payments[0].fineos_pei_i_value == "9999"
