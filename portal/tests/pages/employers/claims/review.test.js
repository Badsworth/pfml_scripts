import { MockClaimBuilder, testHook } from "../../../test-utils";
import { mount, shallow } from "enzyme";
import EmployeeInformation from "../../../../src/components/employers/EmployeeInformation";
import EmployerBenefits from "../../../../src/components/employers/EmployerBenefits";
import Feedback from "../../../../src/components/employers/Feedback";
import LeaveDetails from "../../../../src/components/employers/LeaveDetails";
import LeaveSchedule from "../../../../src/components/employers/LeaveSchedule";
import PreviousLeaves from "../../../../src/components/employers/PreviousLeaves";
import React from "react";
import Review from "../../../../src/pages/employers/claims/review";
import Spinner from "../../../../src/components/Spinner";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  const claim = new MockClaimBuilder().completed().create();
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("displays the spinner if claim is not loaded", () => {
    wrapper = shallow(<Review appLogic={appLogic} query={query} />).dive();

    expect(wrapper.find(Spinner).exists()).toEqual(true);
  });

  it("makes a call to load claim if claim is not loaded", () => {
    appLogic.employers.claim = null;

    act(() => {
      wrapper = mount(<Review appLogic={appLogic} query={query} />);
    });

    expect(appLogic.employers.load).toHaveBeenCalled();
  });

  it("renders pages when claim is loaded", () => {
    appLogic.employers.claim = claim;

    act(() => {
      wrapper = mount(<Review appLogic={appLogic} query={query} />);
    });

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
