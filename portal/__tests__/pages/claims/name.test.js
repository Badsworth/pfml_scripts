import Claim from "../../../src/models/Claim";
import ClaimsApi from "../../../src/api/ClaimsApi";
import { Name } from "../../../src/pages/claims/name";
import React from "react";
import User from "../../../src/models/User";
import { shallow } from "enzyme";

jest.mock("../../../src/api/ClaimsApi");

describe("Name", () => {
  let claim, claimsApi, updateClaim, user, wrapper;
  const claim_id = "12345";

  beforeEach(() => {
    user = new User();
    claim = new Claim();
    claimsApi = new ClaimsApi({ user });
    claimsApi.updateClaim = jest
      .fn()
      .mockImplementation((application_id, patchData) => {
        const success = true;
        const status = 200;
        const apiErrors = [];
        const claim = new Claim(patchData);
        return {
          success,
          status,
          apiErrors,
          claim,
        };
      });
    updateClaim = jest.fn();
    wrapper = shallow(
      <Name
        claim={claim}
        claimsApi={claimsApi}
        updateClaim={updateClaim}
        query={{ claim_id }}
      />
    );
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page prefilled with user information", () => {
    claim = new Claim({
      application_id: claim_id,
      first_name: "Aquib",
      middle_name: "cricketer",
      last_name: "Khan",
    });
    wrapper = shallow(
      <Name
        user={user}
        claim={claim}
        claimsApi={claimsApi}
        updateClaim={updateClaim}
        query={{ claim_id }}
      />
    );
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();

      await wrapper.find("QuestionPage").simulate("save");

      expect(claimsApi.updateClaim).toHaveBeenCalledTimes(1);
      expect(updateClaim).toHaveBeenCalledWith(expect.any(Claim));
    });
  });
});
