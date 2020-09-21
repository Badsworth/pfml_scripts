import PaymentMethod from "../../../src/pages/claims/payment-method";
import { PaymentPreferenceMethod } from "../../../src/models/Claim";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

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

    it("hides the debit card destination info box", () => {
      const conditionalContent = wrapper
        .find("Alert")
        .parents("ConditionalContent");
      expect(conditionalContent.prop("visible")).toBe(false);
    });
  });

  describe("when Debit is selected as the payment method", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod, {
        claimAttrs: {
          payment_preferences: [
            {
              payment_method: PaymentPreferenceMethod.debit,
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

    it("shows the debit card destination info box", () => {
      const conditionalContent = wrapper
        .find("Alert")
        .parents("ConditionalContent");
      expect(conditionalContent.prop("visible")).toBe(true);
    });
  });

  describe("when user clicks continue", () => {
    it("calls claims.update", () => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(PaymentMethod));

      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        expect.any(Object)
      );
    });
  });
});
