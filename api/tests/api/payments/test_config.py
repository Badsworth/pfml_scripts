import massgov.pfml.payments.config as payments_config


def test_get_config_fully_specified(monkeypatch):
    monkeypatch.setenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", "test@test.gov")
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv(
        "BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN",
        "arn:aws:ses:us-east-1:498823821309:identity/noreplypfml@mass.gov",
    )
    monkeypatch.setenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", "test1@test.com")
    monkeypatch.setenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", "test2@test.com")
    monkeypatch.setenv("DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", "test3@test.com")

    payments_email_config = payments_config.get_email_config()

    assert payments_email_config == payments_config.PaymentsEmailConfig(
        dfml_project_manager_email_address="test@test.gov",
        pfml_email_address="noreplypfml@mass.gov",
        bounce_forwarding_email_address="noreplypfml@mass.gov",
        bounce_forwarding_email_address_arn="arn:aws:ses:us-east-1:498823821309:identity/noreplypfml@mass.gov",
        ctr_gax_bievnt_email_address="test1@test.com",
        ctr_vcc_bievnt_email_address="test2@test.com",
        dfml_business_operations_email_address="test3@test.com",
    )


def test_get_date_config(monkeypatch):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2021-01-01")
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2021-01-15")

    payments_date_config = payments_config.get_date_config()

    assert payments_date_config == payments_config.PaymentsDateConfig(
        fineos_vendor_max_history_date="2021-01-01", fineos_payment_max_history_date="2021-01-15",
    )
