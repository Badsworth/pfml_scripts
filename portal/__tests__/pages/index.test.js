import Index from "../../src/pages/index";
import React from "react";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Index appLogic={appLogic} />);
  });

  it("renders dashboard content", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when Create Application form is submitted", () => {
    it("creates claim and redirects to claims.checklist", async () => {
      await wrapper
        .find("form")
        .simulate("submit", { preventDefault: jest.fn() });

      expect(appLogic.createClaim).toHaveBeenCalled();
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining(`${routes.claims.checklist}?claim_id=`)
      );
    });
  });
});
