import Claim from "../../src/models/Claim";
import Index from "../../src/pages/index";
import React from "react";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic;

  beforeEach(() => {
    appLogic = useAppLogic();
  });

  describe("when no claims exist", () => {
    it("renders the initial blank dashboard state", () => {
      appLogic.claims = null;

      const wrapper = shallow(<Index appLogic={appLogic} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when a claim exists", () => {
    it("renders the In Progress dashboard state", () => {
      appLogic.claims = appLogic.claims.addItem(
        new Claim({ application_id: "mock_claim_id" })
      );

      const wrapper = shallow(<Index appLogic={appLogic} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  it("creates claim and redirects to claims.name", async () => {
    const wrapper = shallow(<Index appLogic={appLogic} />);

    await wrapper
      .find("form")
      .simulate("submit", { preventDefault: jest.fn() });

    expect(appLogic.createClaim).toHaveBeenCalled();
    expect(mockRouter.push).toHaveBeenCalledWith(
      expect.stringContaining(`${routes.claims.name}?claim_id=`)
    );
  });
});
