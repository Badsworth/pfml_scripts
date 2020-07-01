import Claim, { LeaveReason } from "../../../src/models/Claim";
import { LeaveReasonPage } from "../../../src/pages/claims/leave-reason";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveReasonPage", () => {
  it("renders the page", () => {
    const claim = new Claim({
      application_id: "12345",
      leave_details: {
        reason: LeaveReason.medical,
      },
    });
    const wrapper = shallow(<LeaveReasonPage claim={claim} appLogic={{}} />);

    expect(wrapper).toMatchSnapshot();
  });
});
