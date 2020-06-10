import Claim from "../../../src/models/Claim";
import { LeaveDates } from "../../../src/pages/claims/leave-dates";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveDates", () => {
  it("renders the page", () => {
    const claim = new Claim({
      application_id: "12345",
      leave_details: {
        continuous_leave_periods: [
          {
            end_date: "2022-09-21",
            start_date: "2022-09-01",
          },
        ],
      },
    });

    const wrapper = shallow(<LeaveDates claim={claim} />);
    expect(wrapper).toMatchSnapshot();
  });
});
