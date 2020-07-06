import Claim, {
  EmploymentStatus,
  LeaveReason,
} from "../../../src/models/Claim";
import React from "react";
import { Review } from "../../../src/pages/claims/review";
import User from "../../../src/models/User";
import { shallow } from "enzyme";

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
      employment_status: EmploymentStatus.employed,
      reason: LeaveReason.medical,
    },
  });
}

describe("Review", () => {
  describe("when all data is present", () => {
    it("renders Review page with the field values", () => {
      const claim = initFullClaim();
      const query = { claim_id: claim.application_id };
      const user = new User({
        user_id: "mock-id",
        has_state_id: true,
      });

      const wrapper = shallow(
        <Review claim={claim} query={query} user={user} />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row", () => {
      const claim = initFullClaim();
      const query = { claim_id: claim.application_id };
      const user = new User();

      const wrapper = shallow(
        <Review claim={claim} query={query} user={user} />
      );

      expect(wrapper.text()).not.toMatch("Notified employer");
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
      const user = new User({
        user_id: "mock-id",
      });

      const wrapper = shallow(
        <Review claim={claim} query={query} user={user} />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });
});
