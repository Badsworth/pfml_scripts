import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../../test-utils";
import EmployerBenefit from "../../../../src/models/EmployerBenefit";
import PreviousLeave from "../../../../src/models/PreviousLeave";
import Review from "../../../../src/pages/employers/applications/review";
import { act } from "react-dom/test-utils";
import { clone } from "lodash";

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
    process.env.featureFlags = {
      employerShowPreviousLeaves: true,
    };

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

  it("displays organization/employer information", () => {
    const organizationNameLabel = wrapper.find("p.text-bold").at(0);
    const employerIdentifierNumberLabel = wrapper.find("p.text-bold").at(1);
    const dataValues = wrapper.find("p.margin-top-0");
    const organizationName = dataValues.at(0);
    const ein = dataValues.at(1);

    expect(organizationNameLabel.text()).toBe("Organization");
    expect(organizationName.text()).toBe("Work Inc.");
    expect(employerIdentifierNumberLabel.text()).toBe(
      "Employer ID number (EIN)"
    );
    expect(ein.text()).toBe("12-3456789");
  });

  it("hides organization name if employer_dba is falsy", () => {
    const noEmployerDba = clone(claim);
    noEmployerDba.employer_dba = undefined;

    act(() => {
      ({ wrapper } = renderComponent("shallow", noEmployerDba));
    });

    const employerIdentifierNumberLabel = wrapper.find("p.text-bold").first();
    expect(employerIdentifierNumberLabel.text()).toBe(
      "Employer ID number (EIN)"
    );
  });

  it("submits a claim with the correct options", async () => {
    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      {
        comment: expect.any(String),
        employer_benefits: expect.any(Array),
        employer_decision: undefined, // undefined by default
        fraud: undefined, // undefined by default
        hours_worked_per_week: expect.any(Number),
        previous_leaves: expect.any(Array),
        has_amendments: false,
      }
    );
  });

  it("sets 'comment' based on the Feedback", async () => {
    act(() => {
      const setComment = wrapper.find("Feedback").prop("setComment");
      setComment("my comment");
    });

    await await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ comment: "my comment" })
    );
  });

  it("sets 'employer_decision' based on EmployerDecision", async () => {
    act(() => {
      const setEmployerDecision = wrapper
        .find("EmployerDecision")
        .prop("onChange");
      setEmployerDecision("Approve");
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ employer_decision: "Approve" })
    );
  });

  it("sets 'fraud' based on FraudReport", async () => {
    act(() => {
      const setFraud = wrapper.find("FraudReport").prop("onChange");
      setFraud("No");
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ fraud: "No" })
    );
  });

  it("sets 'hours_worked_per_week' based on SupportingWorkDetails", async () => {
    act(() => {
      const setAmendedHours = wrapper
        .find("SupportingWorkDetails")
        .prop("onChange");
      setAmendedHours(50.5);
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ hours_worked_per_week: 50.5 })
    );
  });

  it.todo("sets 'previous_leaves' based on PreviousLeaves");

  it.todo("sets 'employer_benefits' based on EmployerBenefits");

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

  it("sets 'has_amendments' to false if nothing is amended", async () => {
    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: false })
    );
  });

  it("sets 'has_amendments' to true if benefits are amended", async () => {
    act(() => {
      wrapper
        .find("EmployerBenefits")
        .props()
        .onChange(new EmployerBenefit({ employer_benefit_id: 0 }));
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if leaves are amended", async () => {
    act(() => {
      wrapper
        .find("PreviousLeaves")
        .props()
        .onChange(new PreviousLeave({ previous_leave_id: 0 }));
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if hours are amended", async () => {
    act(() => {
      wrapper.find("SupportingWorkDetails").props().onChange(60);
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });
});
