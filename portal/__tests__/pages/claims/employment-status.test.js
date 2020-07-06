import Claim, { EmploymentStatus } from "../../../src/models/Claim";
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

  describe("when employment_status is employed", () => {
    it("routes to Notified Employer page", () => {
      props.claim.leave_details.employment_status = EmploymentStatus.employed;

      const wrapper = shallow(<EmploymentStatusPage {...props} />);

      expect(wrapper.prop("nextPage")).toMatchInlineSnapshot(
        `"/claims/notified-employer?claim_id=12345"`
      );
    });
  });

  describe("when employment_status is not employed", () => {
    it("routes to checklist", () => {
      props.claim.leave_details.employment_status =
        EmploymentStatus.selfEmployed;

      const wrapper = shallow(<EmploymentStatusPage {...props} />);

      expect(wrapper.prop("nextPage")).toMatchInlineSnapshot(
        `"/claims/checklist?claim_id=12345"`
      );
    });
  });
});
