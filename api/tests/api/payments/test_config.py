import massgov.pfml.payments.config as config


def test_get_config_fully_specified(monkeypatch):
    monkeypatch.setenv("PAYMENTS_GAX_BIEVNT_EMAIL", "test1@test.com")
    monkeypatch.setenv("PAYMENTS_DFML_BUSINESS_OPERATIONS_EMAIL", "test2@test.com")
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov")

    payment_config = config.get_email_config()

    assert payment_config == config.PaymentsEmailConfig(
        payments_gax_bievnt_email="test1@test.com",
        payments_dfml_business_operations_email="test2@test.com",
        pfml_email_address="noreplypfml@mass.gov",
        bounce_forwarding_email_address="noreplypfml@mass.gov",
    )
