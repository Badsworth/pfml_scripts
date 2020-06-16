import Claim from "../../../src/models/Claim";
import LeaveReason from "../../../src/models/LeaveReason";
import React from "react";
import { Review } from "../../../src/pages/claims/review";
import User from "../../../src/models/User";
import { shallow } from "enzyme";

describe("Review", () => {
  describe("when all data is present", () => {
    it("renders Review page with the field values", () => {
      const claim = new Claim({
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
          reason: LeaveReason.medical,
        },
      });
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
