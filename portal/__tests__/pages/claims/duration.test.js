import Claim from "../../../src/models/Claim";
import { Duration } from "../../../src/pages/claims/duration";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("Duration", () => {
  let claim, wrapper;
  const application_id = "12345";

  beforeEach(() => {
    claim = new Claim({ application_id });
  });

  describe("regardless of duration type", () => {
    beforeEach(() => {
      wrapper = shallow(<Duration claim={claim} />);
    });

    it("initially renders the page without conditional fields", () => {
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });

    it("redirects to the Notified Employer page", () => {
      expect(wrapper.find("QuestionPage").prop("nextPage")).toContain(
        routes.claims.notifiedEmployer
      );
    });
  });

  describe("when user indicates that leave is continuous", () => {
    beforeEach(() => {
      claim = new Claim({ application_id, duration_type: "continuous" });

      wrapper = shallow(<Duration claim={claim} />);
    });

    it("doesn't render conditional fields", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });
  });

  describe("when user indicates that leave is intermittent", () => {
    beforeEach(() => {
      claim = new Claim({ application_id, duration_type: "intermittent" });

      wrapper = shallow(<Duration claim={claim} />);
    });

    it("renders conditional field", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeTruthy();
    });
  });
});
