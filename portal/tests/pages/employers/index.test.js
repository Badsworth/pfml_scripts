import Index from "../../../src/pages/employers";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Employer index", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Index appLogic={appLogic} />);
  });

  it("renders pre-launch content when claimantShowMedicalLeaveType is false", () => {
    process.env.featureFlags = {
      claimantShowMedicalLeaveType: false,
    };

    expect(wrapper).toMatchSnapshot();
  });

  it("renders post-launch content when claimantShowMedicalLeaveType is true", () => {
    process.env.featureFlags = {
      claimantShowMedicalLeaveType: true,
    };

    expect(wrapper).toMatchSnapshot();
  });
});
