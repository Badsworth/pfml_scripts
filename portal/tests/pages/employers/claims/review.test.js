import EmployeeInformation from "../../../../src/components/employers/EmployeeInformation";
import EmployerBenefits from "../../../../src/components/employers/EmployerBenefits";
import Feedback from "../../../../src/components/employers/Feedback";
import LeaveDetails from "../../../../src/components/employers/LeaveDetails";
import LeaveSchedule from "../../../../src/components/employers/LeaveSchedule";
import PastLeave from "../../../../src/components/employers/PastLeave";
import React from "react";
import Review from "../../../../src/pages/employers/claims/review";
import { shallow } from "enzyme";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  const appLogic = useAppLogic();
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<Review appLogic={appLogic} />);
  });

  it("renders page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders formatted employer due date", () => {
    expect(wrapper.find("p").at(1).text()).toContain("9/28/2020");
  });

  it("renders the following components", () => {
    const components = [
      EmployeeInformation,
      EmployerBenefits,
      Feedback,
      LeaveDetails,
      LeaveSchedule,
      PastLeave,
    ];
    components.forEach((component) => {
      expect(wrapper.find(component).exists()).toEqual(true);
    });
  });
});
