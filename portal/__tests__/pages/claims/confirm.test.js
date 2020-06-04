import Claim from "../../../src/models/Claim";
import ClaimsApi from "../../../src/api/ClaimsApi";
import { Confirm } from "../../../src/pages/claims/confirm";
import React from "react";
import User from "../../../src/models/User";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

jest.mock("../../../src/api/ClaimsApi");

describe("Confirm", () => {
  let claim, wrapper;
  const application_id = "34567";

  beforeEach(() => {
    const submitClaim = jest.fn();
    ClaimsApi.mockImplementation(() => ({
      submitClaim,
    }));
    const user = new User();
    const claimsApi = new ClaimsApi({ user });
    claim = new Claim({ application_id });
    wrapper = shallow(<Confirm claim={claim} claimsApi={claimsApi} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to success page", async () => {
    await wrapper
      .find("form")
      .simulate("submit", { preventDefault: jest.fn() });

    expect(mockRouter.push).toHaveBeenCalledWith(routes.claims.success);
  });
});
