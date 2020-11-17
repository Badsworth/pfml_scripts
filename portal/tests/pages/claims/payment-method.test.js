import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import PaymentMethod from "../../../src/pages/claims/payment-method";
import { PaymentPreferenceMethod } from "../../../src/models/Claim";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("PaymentMethod", () => {
  let appLogic, claim, wrapper;

  it("renders the page", () => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod));

    expect(wrapper).toMatchSnapshot();
  });

  describe("when ACH is selected as the payment method", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: {
          payment_preferences: [
            {
              payment_method: PaymentPreferenceMethod.ach,
            },
          ],
        },
      }));
    });

    it("displays the ACH fieldset", () => {
      const achField = wrapper.find(
        "[name='payment_preferences[0].account_details.routing_number']"
      );
      const conditionalContent = achField.parents("ConditionalContent");

      expect(conditionalContent.prop("visible")).toBe(true);
    });
  });

  describe("when Paper check is selected as the payment method", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: {
          payment_preferences: [
            {
              payment_method: PaymentPreferenceMethod.check,
            },
          ],
        },
      }));
    });

    it("does not show the ACH fieldset", () => {
      const achField = wrapper.find(
        "[name='payment_preferences[0].account_details.routing_number']"
      );
      const conditionalContent = achField.parents("ConditionalContent");

      expect(conditionalContent.prop("visible")).toBe(false);
    });
  });

  describe("when user clicks continue", () => {
    it("submits payment preference fields and ID", () => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: new MockClaimBuilder().directDeposit().create(),
      }));

      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          payment_preferences: [
            {
              account_details: {
                account_number: "091000022",
                account_type: "Checking",
                routing_number: "1234567890",
              },
              payment_method: "ACH",
              payment_preference_id: "mock-payment-preference-id",
            },
          ],
        }
      );
    });
  });
});
