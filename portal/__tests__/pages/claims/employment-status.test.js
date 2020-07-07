import Claim from "../../../src/models/Claim";
import { EmploymentStatusPage } from "../../../src/pages/claims/employment-status";
import React from "react";
import { shallow } from "enzyme";

describe("EmploymentStatusPage", () => {
  let props;

  beforeEach(() => {
    const claim = new Claim({ application_id: "12345" });

    props = {
      appLogic: {
        updateClaim: jest.fn(),
      },
      claim,
      query: {
        claim_id: claim.application_id,
      },
    };
  });

  it("renders the page", () => {
    const wrapper = shallow(<EmploymentStatusPage {...props} />);
    expect(wrapper).toMatchSnapshot();
  });
});
