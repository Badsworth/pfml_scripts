import massgov.pfml.delegated_payments.delegated_config as payments_config


def test_get_date_config(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-01-01")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-01-15")

    payments_date_config = payments_config.get_date_config()

    assert payments_date_config == payments_config.PaymentsDateConfig(
        fineos_claimant_extract_max_history_date="2021-01-01",
        fineos_payment_extract_max_history_date="2021-01-15",
    )
