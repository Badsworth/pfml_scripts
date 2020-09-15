import EmployeeInformation from "../../../../src/components/employers/EmployeeInformation";
import EmployerBenefits from "../../../../src/components/employers/EmployerBenefits";
import Feedback from "../../../../src/components/employers/Feedback";
import LeaveDetails from "../../../../src/components/employers/LeaveDetails";
import LeaveSchedule from "../../../../src/components/employers/LeaveSchedule";
import PreviousLeaves from "../../../../src/components/employers/PreviousLeaves";
import React from "react";
import Review from "../../../../src/pages/employers/claims/review";
import Title from "../../../../src/components/Title";
import { shallow } from "enzyme";
import { testHook } from "../../../test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Review appLogic={appLogic} />).dive();
  });

  it("displays the claimant's full name", () => {
    expect(wrapper.find(Title).childAt(0).text()).toEqual(
      "Review application for Jane Doe"
    );
  });

  it("renders the following components", () => {
    const components = [
      EmployeeInformation,
      EmployerBenefits,
      Feedback,
      LeaveDetails,
      LeaveSchedule,
      PreviousLeaves,
    ];
    components.forEach((component) => {
      expect(wrapper.find(component).exists()).toEqual(true);
    });
  });
});
