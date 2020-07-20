import {
  EmploymentStatus,
  LeaveReason,
  PaymentPreference,
  PaymentPreferenceMethod,
} from "../../../src/models/Claim";
import Review from "../../../src/pages/claims/review";
import { renderWithAppLogic } from "../../test-utils";

/**
 * Get a claim for an Employed claimant, with all required fields.
 * Fields can be overridden in each unit test.
 * @returns {object}
 */
function fullClaimAttrs() {
  return {
    duration_type: "continuous",
    first_name: "Bud",
    employment_status: EmploymentStatus.employed,
    employer_fein: "12-1234567",
    middle_name: "Monstera",
    last_name: "Baxter",
    leave_details: {
      continuous_leave_periods: [
        {
          end_date: "2021-12-30",
          start_date: "2021-09-21",
        },
      ],
      employer_notified: true,
      employer_notification_date: "2020-06-25",
      reason: LeaveReason.medical,
    },
    temp: {
      payment_preferences: [
        new PaymentPreference({ payment_method: PaymentPreferenceMethod.ach }),
      ],
    },
  };
}

describe("Review", () => {
  describe("when all data is present", () => {
    it("renders Review page with the field values", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: fullClaimAttrs(),
        userAttrs: { has_state_id: true },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: fullClaimAttrs(),
      });

      expect(wrapper.text()).not.toContain("Notified employer");
      expect(wrapper.text()).not.toContain("Employer's FEIN");
    });
  });

  describe("when data is empty", () => {
    it("does not render strings like 'null' or 'undefined'", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: {
          duration_type: "continuous",
          leave_details: {
            reason: LeaveReason.medical,
          },
        },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });
});
