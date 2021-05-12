import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
} from "../../test-utils";
import Checklist from "../../../src/pages/applications/checklist";
import { DocumentType } from "../../../src/models/Document";
import LeaveReason from "../../../src/models/LeaveReason";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";

function renderStepListDescription(stepListWrapper) {
  return stepListWrapper
    .dive()
    .find(`Trans[i18nKey="pages.claimsChecklist.stepListDescription"]`)
    .dive();
}

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

describe("Checklist", () => {
  beforeEach(() => {
    mockRouter.pathname = routes.applications.checklist;
  });

  it("renders multiple StepList components with list of Steps", () => {
    const { wrapper } = renderWithAppLogic(Checklist, {
      diveLevels,
      hasLoadedClaimDocuments: true,
    });

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.exists("Spinner")).toBe(false);
  });

  it("renders description for Step", () => {
    expect.assertions(7);

    const { wrapper } = renderWithAppLogic(Checklist, {
      // Avoids a blank description for the Upload Certification step,
      // which we have more unit tests for below to capture its other
      // variations
      claimAttrs: new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason()
        .create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
    });
    const steps = wrapper.find("Step");

    steps.forEach((step) => {
      expect(step.find("Trans").dive()).toMatchSnapshot();
    });
  });

  it("renders 'In progress' version of Part 1 StepList description when claim isn't yet submitted", () => {
    const { wrapper } = renderWithAppLogic(Checklist, { diveLevels });
    const part1List = wrapper.find("StepList").at(0);

    expect(renderStepListDescription(part1List)).toMatchSnapshot();
  });

  describe("when Part 1 is submitted", () => {
    let wrapper;

    beforeEach(() => {
      const claim = new MockBenefitsApplicationBuilder().submitted().create();

      ({ wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        warningsLists: {
          [claim.application_id]: [],
        },
      }));
    });

    it("renders different description for Part 1", () => {
      const part1List = wrapper.find("StepList").at(0);

      expect(renderStepListDescription(part1List)).toMatchSnapshot();
    });

    it("renders descriptions for Part 2", () => {
      const part2List = wrapper.find("StepList").at(1);

      expect(renderStepListDescription(part2List)).toMatchSnapshot();
    });

    it("does not render descriptions for Part 3", () => {
      const part3List = wrapper.find("StepList").at(2);

      expect(
        part3List.exists(
          `Trans[i18nKey="pages.claimsChecklist.stepListDescription"]`
        )
      ).toBe(false);
    });
  });

  describe("when Part 2 is submitted", () => {
    let wrapper;

    beforeEach(() => {
      const claim = new MockBenefitsApplicationBuilder()
        .paymentPrefSubmitted()
        .create();

      ({ wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        warningsLists: {
          [claim.application_id]: [],
        },
      }));
    });

    it("Payment pref step is not editable", () => {
      const paymentPrefStep = wrapper.find("Step").at(4);

      expect(paymentPrefStep.prop("editable")).toBe(false);
    });

    it("renders submitted descriptions for Part 2", () => {
      const part2List = wrapper.find("StepList").at(1);

      expect(renderStepListDescription(part2List)).toMatchSnapshot();
    });

    it("renders descriptions for Part 3", () => {
      const part3List = wrapper.find("StepList").at(2);

      expect(renderStepListDescription(part3List)).toMatchSnapshot();
    });
  });

  it("renders success message after submitting part one", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    const { wrapper } = renderWithAppLogic(Checklist, {
      claimAttrs: claim,
      diveLevels,
      props: {
        query: { "part-one-submitted": "true", claim_id: claim.application_id },
      },
    });

    const partOneSubmittedMessage = wrapper.find({
      name: "part-one-submitted-message",
    });

    expect(partOneSubmittedMessage).toHaveLength(1);
    expect(partOneSubmittedMessage.find("Trans").dive()).toMatchSnapshot();
  });

  it("renders success message after submitting part 2", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .submitted()
      .directDeposit()
      .create();
    const { wrapper } = renderWithAppLogic(Checklist, {
      claimAttrs: claim,
      diveLevels,
      props: {
        query: {
          "payment-pref-submitted": "true",
          claim_id: claim.application_id,
        },
      },
    });

    const partTwoSubmittedMessage = wrapper.find({
      name: "part-two-submitted-message",
    });
    expect(partTwoSubmittedMessage).toHaveLength(1);
    expect(partTwoSubmittedMessage).toMatchSnapshot();
  });

  it("enables Review and Submit button when all Parts are completed", () => {
    const claim = new MockBenefitsApplicationBuilder().complete().create();

    const { wrapper } = renderWithAppLogic(Checklist, {
      claimAttrs: claim,
      diveLevels,
      hasLoadedClaimDocuments: true,
      hasUploadedIdDocuments: true,
      hasUploadedCertificationDocuments: {
        document_type: DocumentType.certification.medicalCertification,
      },
      warningsLists: {
        [claim.application_id]: [],
      },
    });

    expect(wrapper.find("ButtonLink").prop("disabled")).toBe(false);
  });

  describe("Upload leave certification step", () => {
    it("renders medical leave content if claim reason is medical", () => {
      const claim = new MockBenefitsApplicationBuilder().submitted().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(6);
      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders newborn bonding leave content if claim reason is newborn", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .submitted()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(6);

      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders adoption bonding leave content if claim reason is adoption", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .submitted()
        .bondingAdoptionLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(6);

      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when loading documents", () => {
    it("renders spinner for loading", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        diveLevels,
      });

      expect(wrapper.exists("Spinner")).toBe(true);
      expect(wrapper.find("Step")).toHaveLength(5);
    });

    it("renders Alert when there is an error for loading documents", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        diveLevels,
        hasLoadingDocumentsError: true,
      });

      expect(wrapper.find("StepList").at(2).exists("Alert")).toBe(true);
      expect(wrapper.find("Step")).toHaveLength(5);
    });
  });

  describe("Upload document steps status", () => {
    const startStatus = "not_started";
    const completeStatus = "completed";

    it("renders both doc steps as not completed", () => {
      const claim = new MockBenefitsApplicationBuilder().complete().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
        warningsLists: {
          [claim.application_id]: [],
        },
      });
      expect(wrapper.find("Step").at(5).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(6).prop("status")).toBe(startStatus);
    });

    it("renders id doc step as completed", () => {
      const claim = new MockBenefitsApplicationBuilder().complete().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
        hasUploadedIdDocuments: true,
        warningsLists: {
          [claim.application_id]: [],
        },
      });
      expect(wrapper.find("Step").at(5).prop("status")).toBe(completeStatus);
      expect(wrapper.find("Step").at(6).prop("status")).toBe(startStatus);
    });

    it("renders certification doc step as completed when the document type matches the leave reason when Caring Leave feature flag is turned on", () => {
      // When the feature flag is enabled, the component should mark this step as completed when there are documents with a DocType that match the leave reason
      // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that match the leave reason,
      // so the component should render this step as completed

      process.env.featureFlags = {
        showCaringLeaveType: true,
      };

      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .complete()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: {
          document_type: DocumentType.certification[LeaveReason.medical],
          numberOfDocs: 1,
        },
      });
      expect(wrapper.find("Step").at(5).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(6).prop("status")).toBe(completeStatus);
    });

    it("renders certification doc step as incomplete when the document type does not match the leave reason when Caring Leave feature flag is turned on", () => {
      // When the feature flag is enabled, the component should mark this step as completed when there are documents with a DocType that match the leave reason
      // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that don't match the leave reason,
      // so the component should render this step as incomplete

      process.env.featureFlags = {
        showCaringLeaveType: true,
      };

      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .complete()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: {
          document_type: DocumentType.certification[LeaveReason.care],
          numberOfDocs: 1,
        },
      });
      expect(wrapper.find("Step").at(5).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(6).prop("status")).toBe(startStatus);
    });

    // TODO (CP-2029): Remove this test once claims filed before 7/1/2021 are adjudicated and we don't use State managed Paid Leave Confirmation
    it("renders certification doc step as complete when the Document Type is State managed Paid Leave Confirmation", () => {
      // This is for the case of claims created prior to 7/1, until we can remove this doc type
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .complete()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels,
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: {
          document_type: DocumentType.certification.medicalCertification,
          numberOfDocs: 1,
        },
      });
      expect(wrapper.find("Step").at(5).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(6).prop("status")).toBe(completeStatus);
    });
  });
});
