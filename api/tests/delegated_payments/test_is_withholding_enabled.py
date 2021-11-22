import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util

def test_is_withholding_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_WITHHOLDING_PAYMENTS", "0")

    is_withholding_enabled = payments_util.is_withholding_payments_enabled()

    assert is_withholding_enabled == False
