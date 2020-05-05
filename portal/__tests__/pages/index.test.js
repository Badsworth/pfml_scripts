import Claim from "../../src/models/Claim";
import Collection from "../../src/models/Collection";
import Index from "../../src/pages/index";
import React from "react";
import { createClaim } from "../../src/api/claimsApi";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { shallow } from "enzyme";
jest.mock("../../src/api/claimsApi", () => {
  return {
    createClaim: jest.fn().mockReturnValue({ success: true, claim: {} }),
  };
});

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

  it("creates claim when user clicks create claim button", () => {
    const wrapper = shallow(<Index addClaim={jest.fn()} claims={claims} />);

    wrapper.find("Button").simulate("click");

    expect(createClaim).toHaveBeenCalled();
  });

  it("redirects to claims.name after claim is successfully created", async () => {
    let addedClaim;
    const addClaim = jest.fn().mockImplementation((claim) => {
      addedClaim = claim;
    });
    const wrapper = shallow(<Index addClaim={addClaim} claims={claims} />);

    await wrapper.find("Button").simulate("click");

    expect(addClaim).toHaveBeenCalled();
    expect(mockRouter.push).toHaveBeenCalledWith(
      `${routes.claims.name}?claim_id=${addedClaim.claim_id}`
    );
  });
});
