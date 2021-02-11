import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PaymentMethod from "../../../src/pages/applications/payment-method";
import { PaymentPreferenceMethod } from "../../../src/models/PaymentPreference";

jest.mock("../../../src/hooks/useAppLogic");

describe("PaymentMethod", () => {
  let appLogic, claim, wrapper;

  it("renders the page", () => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod));

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").first().dive()).toMatchSnapshot();
  });

  describe("when ACH is selected as the payment method", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: {
          payment_preference: {
            payment_method: PaymentPreferenceMethod.ach,
          },
        },
      }));
    });

    it("displays the ACH fieldset", () => {
      const achField = wrapper.find(
        "[name='payment_preference.routing_number']"
      );
      const conditionalContent = achField.parents("ConditionalContent");

      expect(conditionalContent.prop("visible")).toBe(true);
    });
  });

  describe("when Paper check is selected as the payment method", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: {
          payment_preference: {
            payment_method: PaymentPreferenceMethod.check,
          },
        },
      }));
    });

    it("does not show the ACH fieldset", () => {
      const achField = wrapper.find(
        "[name='payment_preference.routing_number']"
      );
      const conditionalContent = achField.parents("ConditionalContent");

      expect(conditionalContent.prop("visible")).toBe(false);
    });
  });

  describe("when user clicks continue", () => {
    it("submits payment preference fields for direct deposit", async () => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: new MockClaimBuilder().directDeposit().create(),
      }));

      const { submitForm } = simulateEvents(wrapper);
      await submitForm();

      expect(appLogic.claims.submitPaymentPreference).toHaveBeenCalledWith(
        claim.application_id,
        {
          payment_preference: {
            account_number: "091000022",
            bank_account_type: "Checking",
            routing_number: "1234567890",
            payment_method: "Elec Funds Transfer",
          },
        }
      );
    });

    it("submits payment preference fields for check", async () => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: new MockClaimBuilder().check().create(),
      }));

      const { submitForm } = simulateEvents(wrapper);
      await submitForm();

      expect(appLogic.claims.submitPaymentPreference).toHaveBeenCalledWith(
        claim.application_id,
        {
          payment_preference: {
            account_number: null,
            bank_account_type: null,
            routing_number: null,
            payment_method: "Check",
          },
        }
      );
    });
  });
});
