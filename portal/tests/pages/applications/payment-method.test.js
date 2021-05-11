import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../../src/models/PaymentPreference";
import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PaymentMethod from "../../../src/pages/applications/payment-method";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (payment_type) => {
  let claim = new MockBenefitsApplicationBuilder();

  if (payment_type === PaymentPreferenceMethod.check) {
    claim.check();
  }
  if (payment_type === PaymentPreferenceMethod.ach) {
    claim.directDeposit();
  }
  claim = claim.create();

  const { appLogic, wrapper } = renderWithAppLogic(PaymentMethod, {
    claimAttrs: claim,
  });

  const { changeField, changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("PaymentMethod", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });

  it("displays the ACH fieldset when ACH is previously selected as the payment method", () => {
    const { wrapper } = setup(PaymentPreferenceMethod.ach);
    const achField = wrapper.find("[name='payment_preference.routing_number']");
    const conditionalContent = achField.parents("ConditionalContent");

    expect(conditionalContent.prop("visible")).toBe(true);
  });

  it("does not show the ACH fieldset when paper check is previously selected as the payment method", () => {
    const { wrapper } = setup(PaymentPreferenceMethod.check);

    const achField = wrapper.find("[name='payment_preference.routing_number']");
    const conditionalContent = achField.parents("ConditionalContent");

    expect(conditionalContent.prop("visible")).toBe(false);
  });

  it("submits payment preference fields for direct deposit when the data is already on the claim", async () => {
    const { appLogic, claim, submitForm } = setup(PaymentPreferenceMethod.ach);

    await submitForm();

    expect(
      appLogic.benefitsApplications.submitPaymentPreference
    ).toHaveBeenCalledWith(claim.application_id, {
      payment_preference: {
        account_number: "091000022",
        bank_account_type: "Checking",
        routing_number: "1234567890",
        payment_method: PaymentPreferenceMethod.ach,
      },
    });
  });

  it("submits payment preference fields for check when the data is already on the claim", async () => {
    const { appLogic, claim, submitForm } = setup(
      PaymentPreferenceMethod.check
    );

    await submitForm();

    expect(
      appLogic.benefitsApplications.submitPaymentPreference
    ).toHaveBeenCalledWith(claim.application_id, {
      payment_preference: {
        account_number: null,
        bank_account_type: null,
        routing_number: null,
        payment_method: PaymentPreferenceMethod.check,
      },
    });
  });

  it("submits payment preference fields for direct deposit when the data is newly entered", async () => {
    const {
      appLogic,
      changeField,
      changeRadioGroup,
      claim,
      submitForm,
    } = setup();
    const account_number = "987654321";
    const bank_account_type = BankAccountType.checking;
    const payment_method = PaymentPreferenceMethod.ach;
    const routing_number = "123456789";

    changeRadioGroup("payment_preference.payment_method", payment_method);
    changeField("payment_preference.routing_number", routing_number);
    changeField("payment_preference.account_number", account_number);
    changeRadioGroup("payment_preference.bank_account_type", bank_account_type);

    await submitForm();

    expect(
      appLogic.benefitsApplications.submitPaymentPreference
    ).toHaveBeenCalledWith(claim.application_id, {
      payment_preference: {
        account_number,
        bank_account_type,
        routing_number,
        payment_method,
      },
    });
  });
});
