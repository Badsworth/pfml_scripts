import Claim from "../../src/models/Claim";
import Collection from "../../src/models/Collection";
import Index from "../../src/pages/index";
import React from "react";
import { shallow } from "enzyme";

describe("Index", () => {
  let claims;

  beforeEach(() => {
    claims = new Collection({ idProperty: "claim_id" });
  });

  describe("when no claims exist", () => {
    it("renders the initial blank dashboard state", () => {
      const wrapper = shallow(<Index claims={claims} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when a claim exists", () => {
    it("renders the In Progress dashboard state", () => {
      claims.add(new Claim({ claim_id: "mock-claim-id" }));

      const wrapper = shallow(<Index claims={claims} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});
