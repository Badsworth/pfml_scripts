import Claim from "../../../src/models/Claim";
import { Confirm } from "../../../src/pages/claims/confirm";
import React from "react";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Confirm", () => {
  let claim, wrapper;
  const application_id = "34567";

  beforeEach(() => {
    const appLogic = useAppLogic();
    claim = new Claim({ application_id });
    wrapper = shallow(<Confirm claim={claim} appLogic={appLogic} />);
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
