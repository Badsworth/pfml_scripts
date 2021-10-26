from _typeshed import Self
import massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing as related_payment

import pytest
# def __init__(self):
#     self.abc = related_payment.RelatedPaymentsProcessingStep()

@pytest.fixture
def load_data():
    pass

def test_get_withholding_payments_records():

    related_pay = related_payment()

    test_withholding_payments =3
    fineos_payment=related_pay._get_withholding_payments_records(Self)
    assert(len(fineos_payment, test_withholding_payments))


def test_get_payments_for_federal_withholding():
    assert(True)
    # test_withholding_payments =[1,2,3]
    # fineos_payment=self.abc._get_payments_for_federal_withholding()
    # assert(fineos_payment, test_withholding_payments)

