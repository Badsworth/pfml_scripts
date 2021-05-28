import Document, { DocumentType } from "../../../../src/models/Document";
import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../../test-utils";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import EmployerBenefit from "../../../../src/models/EmployerBenefit";
import LeaveReason from "../../../../src/models/LeaveReason";
import PreviousLeave from "../../../../src/models/PreviousLeave";
import Review from "../../../../src/pages/employers/applications/review";
import { act } from "react-dom/test-utils";
import { clone } from "lodash";

jest.mock("../../../../src/hooks/useAppLogic");

const DOCUMENTS = new DocumentCollection([
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-1",
    name: "Approval notice doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification[LeaveReason.care],
    fineos_document_id: "fineos-id-10",
    name: "Caring cert doc",
  }),
]);

describe("Review", () => {
  const claim = new MockEmployerClaimBuilder()
    .completed()
    .reviewable()
    .create();
  const query = { absence_id: "NTN-111-ABS-01" };

  let appLogic, wrapper;

  const renderComponent = (
    render = "shallow",
    employerClaimAttrs = claim,
    props = {}
  ) => {
    return renderWithAppLogic(Review, {
      employerClaimAttrs,
      props: {
        query,
        ...props,
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

  it("submits a claim with leave_reason when showCaringLeaveType is on ", async () => {
    process.env.featureFlags = {
      showCaringLeaveType: true,
    };
    ({ wrapper, appLogic } = renderComponent("mount"));
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
        leave_reason: "Serious Health Condition - Employee",
      }
    );
    process.env.featureFlags = {};
  });

  it("sets 'comment' based on the Feedback", async () => {
    act(() => {
      const setComment = wrapper.find("Feedback").prop("setComment");
      setComment("my comment");
    });

    await simulateEvents(wrapper).submitForm();

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
      expect.objectContaining({
        has_amendments: true,
        hours_worked_per_week: 60,
      })
    );
  });

  it("only calls preventDefault when pressing enter in text input", async () => {
    await act(async () => {
      const openAmendedHours = wrapper
        .find("SupportingWorkDetails")
        .find("AmendButton")
        .prop("onClick");
      await openAmendedHours();
    });
    const textInput = wrapper
      .find("SupportingWorkDetails")
      .find("ConditionalContent")
      .update()
      .find('input[name="hours_worked_per_week"]');
    const mockPreventDefaultForEnter = jest.fn();
    textInput.simulate("keydown", {
      keyCode: 13,
      preventDefault: mockPreventDefaultForEnter,
    });
    const mockPreventDefaultForOtherKeys = jest.fn();
    textInput.simulate("keydown", {
      keyCode: 65, // letter A
      preventDefault: mockPreventDefaultForOtherKeys,
    });
    expect(mockPreventDefaultForEnter).toHaveBeenCalled();
    expect(mockPreventDefaultForOtherKeys).not.toHaveBeenCalled();
  });

  it("doesn't call preventDefault() when pressing enter on submit button", async () => {
    const mockPreventDefault = jest.fn();
    await act(async () => {
      await wrapper.find('button[type="submit"]').simulate("keydown", {
        keyCode: 13,
        preventDefault: mockPreventDefault,
      });
    });
    expect(mockPreventDefault).not.toHaveBeenCalled();
  });

  describe("Documents", () => {
    it("loads the documents while documents are undefined", () => {
      ({ appLogic } = renderComponent("mount"));
      expect(appLogic.employers.loadDocuments).toHaveBeenCalledWith(
        "NTN-111-ABS-01"
      );
    });

    describe("when the claim is a caring leave", () => {
      function render() {
        const caringLeaveClaim = clone(claim);
        caringLeaveClaim.leave_details.reason = "Care for a Family Member";
        appLogic.employers.documents = DOCUMENTS;
        ({ appLogic, wrapper } = renderComponent("mount", caringLeaveClaim, {
          appLogic,
        }));
      }

      it("does not load the documents while documents is loaded ", () => {
        render();
        expect(appLogic.employers.loadDocuments).not.toHaveBeenCalled();
      });

      it("shows only medical cert when feature flag is false", () => {
        render();
        const documents = wrapper.find("LeaveDetails").props().documents;
        expect(documents.length).toBe(1);
        expect(documents.map((document) => document.name)).toEqual([
          "Medical cert doc",
        ]);
      });

      it("shows medical cert and caring cert when feature flag is true", () => {
        process.env.featureFlags = {
          showCaringLeaveType: true,
        };
        render();
        const documents = wrapper.find("LeaveDetails").props().documents;
        expect(documents.length).toBe(2);
        expect(documents.map((document) => document.name)).toEqual([
          "Medical cert doc",
          "Caring cert doc",
        ]);
      });
    });
  });

  describe("Caring Leave", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        showCaringLeaveType: true,
      };
      const caringLeaveClaim = new MockEmployerClaimBuilder()
        .completed()
        .caringLeaveReason()
        .reviewable()
        .create();

      ({ appLogic, wrapper } = renderComponent("mount", caringLeaveClaim));
    });

    it("submits a caring leave claim with the correct options", async () => {
      await simulateEvents(wrapper).submitForm();

      expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        {
          believe_relationship_accurate: undefined, // undefined by default
          comment: expect.any(String),
          employer_benefits: expect.any(Array),
          employer_decision: undefined, // undefined by default
          fraud: undefined, // undefined by default
          hours_worked_per_week: expect.any(Number),
          previous_leaves: expect.any(Array),
          has_amendments: false,
          relationship_inaccurate_reason: expect.any(String),
          leave_reason: "Care for a Family Member",
        }
      );
    });

    it("disables submit button when LA indicates the relationship is inaccurate and no relationship comment", () => {
      act(() => {
        wrapper
          .find("LeaveDetails")
          .props()
          .onChangeBelieveRelationshipAccurate("No");
      });

      expect(
        wrapper.update().find('button[type="submit"]').prop("disabled")
      ).toBe(true);
    });

    it("submits has_amendments as true when LA indicates the relationship is inaccurate", async () => {
      await act(async () => {
        await wrapper
          .find("input[name='believeRelationshipAccurate']")
          .last()
          .simulate("change", { target: { value: "No" } });
        await simulateEvents(wrapper).submitForm();
      });

      expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          has_amendments: true,
          believe_relationship_accurate: "No",
        })
      );
    });
  });
});
