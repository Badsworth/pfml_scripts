import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../../test-utils";
import EmployerBenefit from "../../../../src/models/EmployerBenefit";
import PreviousLeave from "../../../../src/models/PreviousLeave";
import Review from "../../../../src/pages/employers/applications/review";
import { act } from "react-dom/test-utils";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  const query = { absence_id: "NTN-111-ABS-01" };

  let appLogic, wrapper;

  const renderComponent = (render = "shallow") => {
    return renderWithAppLogic(Review, {
      employerClaimAttrs: claim,
      props: {
        query,
      },
      render,
    });
  };

  beforeEach(() => {
    ({ wrapper, appLogic } = renderComponent("mount"));
  });

  it("renders the page", () => {
    const components = [
      "EmployeeInformation",
      "EmployerBenefits",
      "EmployerDecision",
      "Feedback",
      "FraudReport",
      "LeaveDetails",
      "LeaveSchedule",
      "PreviousLeaves",
      "SupportingWorkDetails",
    ];

    components.forEach((component) => {
      expect(wrapper.find(component).exists()).toEqual(true);
    });
  });

  it("submits a claim with the correct options", () => {
    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith("NTN-111-ABS-01", {
      comment: expect.any(String),
      employer_benefits: expect.any(Array),
      employer_decision: undefined, // undefined by default
      fraud: undefined, // undefined by default
      hours_worked_per_week: expect.any(Number),
      previous_leaves: expect.any(Array),
      has_amendments: false,
    });
  });

  it("sets 'comment' based on the Feedback", () => {
    act(() => {
      const setComment = wrapper.find("Feedback").prop("setComment");
      setComment("my comment");
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ comment: "my comment" })
    );
  });

  it("sets 'employer_decision' based on EmployerDecision", () => {
    act(() => {
      const setEmployerDecision = wrapper
        .find("EmployerDecision")
        .prop("onChange");
      setEmployerDecision("Approve");
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ employer_decision: "Approve" })
    );
  });

  it("sets 'fraud' based on FraudReport", () => {
    act(() => {
      const setFraud = wrapper.find("FraudReport").prop("onChange");
      setFraud("No");
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ fraud: "No" })
    );
  });

  it("sets 'has_amendments' to false if nothing is amended", () => {
    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: false })
    );
  });

  it("sets 'has_amendments' to true if benefits are amended", () => {
    act(() => {
      wrapper
        .find("EmployerBenefits")
        .props()
        .onChange(new EmployerBenefit({ id: 1 }));
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if leaves are amended", () => {
    act(() => {
      wrapper
        .find("PreviousLeaves")
        .props()
        .onChange(new PreviousLeave({ id: 1 }));
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if hours are amended", () => {
    act(() => {
      wrapper.find("SupportingWorkDetails").props().onChange(60);
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  // TODO (EMPLOYER-596) implement test for employer_benefits
  // TODO (EMPLOYER-596) implement test for hours_worked_per_week
  // TODO (EMPLOYER-596) implement test for previous_leaves
});
