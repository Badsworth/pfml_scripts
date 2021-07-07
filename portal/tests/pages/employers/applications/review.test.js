import Document, { DocumentType } from "../../../../src/models/Document";
import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../../test-utils";
import ConcurrentLeave from "../../../../src/models/ConcurrentLeave";
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
  const baseClaimBuilder = new MockEmployerClaimBuilder()
    .completed()
    .reviewable();
  const claimWithV1Eform = baseClaimBuilder.eformsV1().create();
  const claimWithV2Eform = baseClaimBuilder.eformsV2().create();
  const query = { absence_id: "NTN-111-ABS-01" };

  let appLogic, wrapper;

  const renderComponent = (
    render = "shallow",
    employerClaimAttrs = claimWithV2Eform,
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
    ({ wrapper, appLogic } = renderComponent("mount"));
  });

  it("renders the page for v1 eforms", () => {
    ({ wrapper } = renderComponent("shallow", claimWithV1Eform));
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
      expect(wrapper.find(component).exists()).toBe(true);
    });
    expect(wrapper.find("ConcurrentLeave").exists()).toBe(false);
    expect(wrapper.find("PreviousLeaves").exists()).toBe(false);
  });

  it("renders the page for v2 eforms", () => {
    ({ wrapper } = renderComponent("shallow", claimWithV2Eform));
    const components = [
      "ConcurrentLeave",
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
      expect(wrapper.find(component).exists()).toBe(true);
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
    const noEmployerDba = clone(claimWithV1Eform);
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
        employer_decision: "Approve", // "Approve" by default
        fraud: undefined, // undefined by default
        hours_worked_per_week: expect.any(Number),
        previous_leaves: expect.any(Array),
        concurrent_leave: null,
        has_amendments: false,
        leave_reason: "Serious Health Condition - Employee",
        uses_second_eform_version: true,
      }
    );
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

  it("sets 'employer_decision' if the employer denies", async () => {
    act(() => {
      const updateFields = wrapper
        .find("EmployerDecision")
        .prop("updateFields");
      updateFields({ employer_decision: "Deny" });
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ employer_decision: "Deny" })
    );
  });

  it("sets 'employer_decision' if the employer approves", async () => {
    act(() => {
      const updateFields = wrapper
        .find("EmployerDecision")
        .prop("updateFields");
      updateFields({ employer_decision: "Approve" });
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
      const updateFields = wrapper
        .find("SupportingWorkDetails")
        .prop("updateFields");
      updateFields({ hours_worked_per_week: 50.5 });
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ hours_worked_per_week: 50.5 })
    );
  });

  it.todo("sets 'previous_leaves' based on PreviousLeaves");

  it.todo("sets 'employer_benefits' based on EmployerBenefits");

  it("sends concurrent leave if uses_second_eform_version is true", async () => {
    const claimWithConcurrentLeave = baseClaimBuilder
      .eformsV2()
      .concurrentLeave()
      .create();

    ({ appLogic, wrapper } = renderComponent(
      "mount",
      claimWithConcurrentLeave
    ));

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({
        concurrent_leave: new ConcurrentLeave({
          is_for_current_employer: true,
          leave_start_date: "2021-01-01",
          leave_end_date: "2021-03-01",
        }),
      })
    );
  });

  it("sends amended concurrent leave if uses_second_eform_version is true", async () => {
    const claim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable()
      .eformsV2()
      .concurrentLeave()
      .create();

    ({ appLogic, wrapper } = renderComponent("mount", claim));

    act(() => {
      wrapper
        .find("ConcurrentLeave")
        .props()
        .onChange(
          new ConcurrentLeave({
            is_for_current_employer: false,
            leave_start_date: "2021-10-10",
            leave_end_date: "2021-10-17",
          })
        );
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({
        concurrent_leave: new ConcurrentLeave({
          is_for_current_employer: false,
          leave_start_date: "2021-10-10",
          leave_end_date: "2021-10-17",
        }),
      })
    );
  });

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

  it("sets 'has_amendments' to true if benefits are added", async () => {
    ({ appLogic, wrapper } = renderComponent("shallow", claimWithV2Eform));

    act(() => {
      wrapper.find("EmployerBenefits").props().onAdd();
    });

    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if previous leaves are amended", async () => {
    ({ appLogic, wrapper } = renderComponent("shallow", claimWithV2Eform));

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

  it("sets 'has_amendments' to true if previous leaves are added", async () => {
    ({ appLogic, wrapper } = renderComponent("shallow", claimWithV2Eform));

    act(() => {
      wrapper.find("PreviousLeaves").props().onAdd();
    });
    await simulateEvents(wrapper).submitForm();

    expect(appLogic.employers.submitClaimReview).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      expect.objectContaining({ has_amendments: true })
    );
  });

  it("sets 'has_amendments' to true if hours are amended", async () => {
    act(() => {
      wrapper
        .find("SupportingWorkDetails")
        .props()
        .updateFields({ hours_worked_per_week: 60 });
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
        const caringLeaveClaim = clone(claimWithV2Eform);
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

      it("shows medical cert and caring cert", () => {
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
      const caringLeaveClaim = new MockEmployerClaimBuilder()
        .eformsV2()
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
          employer_decision: "Approve", // "Approve" by default
          fraud: undefined, // undefined by default
          hours_worked_per_week: expect.any(Number),
          previous_leaves: expect.any(Array),
          concurrent_leave: null,
          has_amendments: false,
          uses_second_eform_version: true,
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

    it("submits has_amendments as false when LA indicates the relationship is inaccurate", async () => {
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
          has_amendments: false,
          uses_second_eform_version: true,
          believe_relationship_accurate: "No",
        })
      );
    });
  });
});
