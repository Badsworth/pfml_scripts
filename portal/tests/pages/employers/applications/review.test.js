import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../../test-utils";
import EmployerBenefit from "../../../../src/models/EmployerBenefit";
import Review from "../../../../src/pages/employers/applications/review";
import { act } from "react-dom/test-utils";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Review", () => {
  const claim = new MockEmployerClaimBuilder()
    .completed()
    .reviewable()
    .create();
  const query = { absence_id: "NTN-111-ABS-01" };

  let appLogic, wrapper;

  const renderComponent = (render = "shallow", employerClaimAttrs = claim) => {
    return renderWithAppLogic(Review, {
      employerClaimAttrs,
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

  it.todo("sets 'employer_benefits' based on EmployerBenefits");
  it.todo("sets 'hours_worked_per_week' based on SupportingWorkDetails");
  it.todo("sets 'previous_leaves' based on PreviousLeaves");

  it("does not redirect if is_reviewable is true", () => {
    expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
  });

  it("redirects to the status page if is_reviewable is false", () => {
    const falseIsReviewableClaim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable(false)
      .create();

    ({ appLogic } = renderComponent("shallow", falseIsReviewableClaim));

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      "/employers/applications/status",
      {
        absence_id: "NTN-111-ABS-01",
      }
    );
  });

  it("does not redirect to the status page if is_reviewable is null", () => {
    const nullIsReviewableClaim = new MockEmployerClaimBuilder()
      .completed()
      .create();

    ({ appLogic } = renderComponent("shallow", nullIsReviewableClaim));

    expect(nullIsReviewableClaim.is_reviewable).toBe(null);
    expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
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
        .onChange(new EmployerBenefit({ employer_benefit_id: 1 }));
    });

    simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submit).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  // TODO (EMPLOYER-656): Show previous leaves
  // it("sets 'has_amendments' to true if leaves are amended", () => {
  //   act(() => {
  //     wrapper
  //       .find("PreviousLeaves")
  //       .props()
  //       .onChange(new PreviousLeave({ previous_leave_id: 1 }));
  //   });

  //   simulateEvents(wrapper).submitForm();

  //   expect(appLogic.employers.submit).toHaveBeenCalledWith(
  //     "NTN-111-ABS-01",
  //     expect.objectContaining({ has_amendments: true })
  //   );
  // });

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
});
