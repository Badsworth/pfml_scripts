import Claim from "../../../src/models/Claim";
import { LeaveDates } from "../../../src/pages/claims/leave-dates";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveDates", () => {
  it("renders the page", () => {
    const wrapper = shallow(
      <LeaveDates
        claim={new Claim({ application_id: "12345" })}
        appLogic={{}}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });
});
