import { simulateEvents, testHook } from "../test-utils";
import Index from "../../src/pages/index";
import React from "react";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    // Dive once since Index is wrapped by withUser
    wrapper = shallow(<Index appLogic={appLogic} />).dive();
  });

  it("renders dashboard content", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when Create Application form is submitted", () => {
    it("creates a new claim", async () => {
      jest.spyOn(appLogic.claims, "create").mockResolvedValueOnce();
      const { submitForm } = simulateEvents(wrapper);

      submitForm();

      expect(appLogic.claims.create).toHaveBeenCalled();
    });
  });
});
