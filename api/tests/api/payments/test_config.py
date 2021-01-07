import massgov.pfml.payments.config as payments_config


def test_get_config_fully_specified(monkeypatch):
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", "test1@test.com")
    monkeypatch.setenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", "test2@test.com")
    monkeypatch.setenv("DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", "test3@test.com")

    payments_email_config = payments_config.get_email_config()

    assert payments_email_config == payments_config.PaymentsEmailConfig(
        pfml_email_address="noreplypfml@mass.gov",
        bounce_forwarding_email_address="noreplypfml@mass.gov",
        ctr_gax_bievnt_email_address="test1@test.com",
        ctr_vcc_bievnt_email_address="test2@test.com",
        dfml_business_operations_email_address="test3@test.com",
    )
