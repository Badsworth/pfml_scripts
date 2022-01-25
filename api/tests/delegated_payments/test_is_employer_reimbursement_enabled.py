import massgov.pfml.delegated_payments.delegated_payments_util as payments_util


def test_is_employer_reimbursement_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "0")

    is_employer_reimbursement_enabled = payments_util.is_employer_reimbursement_payments_enabled()

    assert is_employer_reimbursement_enabled is False
