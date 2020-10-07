import { simulateEvents, testHook } from "../../test-utils";
import React from "react";
import { Start } from "../../../src/pages/claims/start";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Start", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Start appLogic={appLogic} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks agree and submit", () => {
    it("calls submitApplication", () => {
      const { submitForm } = simulateEvents(wrapper);
      submitForm();
      expect(appLogic.claims.create).toHaveBeenCalled();
    });
  });
});
