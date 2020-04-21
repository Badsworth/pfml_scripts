import Claim from "../../../src/models/Claim";
import Collection from "../../../src/models/Collection";
import Duration from "../../../src/pages/claims/duration";
import React from "react";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("Duration", () => {
  let claims, wrapper;
  beforeEach(() => {
    claims = new Collection({ idProperty: "claimId" });
  });

  describe("regardless of duration type", () => {
    beforeEach(() => {
      wrapper = shallow(<Duration claims={claims} query={{}} />);
    });

    it("initially renders the page without conditional fields", () => {
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });

    it("redirects to the home page", () => {
      expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
        routes.home
      );
    });
  });

  describe("when user indicates that leave is continuous", () => {
    beforeEach(() => {
      claims.add(new Claim({ claimId: "12345", durationType: "continuous" }));
      wrapper = shallow(
        <Duration claims={claims} query={{ claimId: "12345" }} />
      );
    });

    it("doesn't render conditional fields", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    });
  });

  describe("when user indicates that leave is intermittent", () => {
    beforeEach(() => {
      claims.add(new Claim({ claimId: "12345", durationType: "intermittent" }));
      wrapper = shallow(
        <Duration claims={claims} query={{ claimId: "12345" }} />
      );
    });

    it("renders conditional field", () => {
      expect(wrapper.find("ConditionalContent").prop("visible")).toBeTruthy();
    });
  });
});
