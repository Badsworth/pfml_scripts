import { simulateEvents, testHook } from "../../test-utils";
import React from "react";
import { Start } from "../../../src/pages/applications/start";
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

  it("renders descriptions with mass gov link", () => {
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  describe("when user clicks agree and submit", () => {
    it("calls submitApplication", async () => {
      const { submitForm } = simulateEvents(wrapper);
      await submitForm();
      expect(appLogic.benefitsApplications.create).toHaveBeenCalled();
    });
  });
});
