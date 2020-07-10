import Claim, {
  EmploymentStatus,
  LeaveReason,
} from "../../../src/models/Claim";
import React from "react";
import { Review } from "../../../src/pages/claims/review";
import User from "../../../src/models/User";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

/**
 * Initialize a claim for an Employed claimant, with all required fields.
 * Fields can be overridden in each unit test.
 * @returns {Claim}
 */
function initFullClaim() {
  return new Claim({
    application_id: "mock-id",
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
  });
}

describe("Review", () => {
  let appLogic;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  describe("when all data is present", () => {
    it("renders Review page with the field values", () => {
      const claim = initFullClaim();
      const query = { claim_id: claim.application_id };
      appLogic.user = new User({
        user_id: "mock-id",
        has_state_id: true,
      });

      const wrapper = shallow(
        <Review claim={claim} query={query} appLogic={appLogic} />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const claim = initFullClaim();
      const query = { claim_id: claim.application_id };
      appLogic.user = new User();

      const wrapper = shallow(
        <Review claim={claim} query={query} appLogic={appLogic} />
      );

      expect(wrapper.text()).not.toContain("Notified employer");
      expect(wrapper.text()).not.toContain("Employer's FEIN");
    });
  });

  describe("when data is empty", () => {
    it("does not render strings like 'null' or 'undefined'", () => {
      const claim = new Claim({
        application_id: "mock-id",
        duration_type: "continuous",
        leave_details: {
          reason: LeaveReason.medical,
        },
      });
      const query = { claim_id: claim.application_id };
      appLogic.user = new User({
        user_id: "mock-id",
      });

      const wrapper = shallow(
        <Review claim={claim} query={query} appLogic={appLogic} />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });
});
