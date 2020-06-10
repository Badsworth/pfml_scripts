import Claim from "../../../src/models/Claim";
import { LeaveReason } from "../../../src/pages/claims/leave-reason";
import LeaveReasonEnums from "../../../src/models/LeaveReason";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveReason", () => {
  it("renders the page", () => {
    const claim = new Claim({
      application_id: "12345",
      leave_details: {
        reason: LeaveReasonEnums.medical,
      },
    });
    const wrapper = shallow(<LeaveReason claim={claim} appLogic={{}} />);
    expect(wrapper).toMatchSnapshot();
  });
});
