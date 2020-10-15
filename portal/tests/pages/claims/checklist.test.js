import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import Checklist from "../../../src/pages/claims/checklist";

function renderStepListDescription(stepListWrapper) {
  return stepListWrapper
    .dive()
    .find(`Trans[i18nKey="pages.claimsChecklist.stepListDescription"]`)
    .dive();
}

describe("Checklist", () => {
  it("renders multiple StepList components with list of Steps", () => {
    const { wrapper } = renderWithAppLogic(Checklist, {
      diveLevels: 5,
      hasLoadedClaimDocuments: true,
    });

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.exists("Spinner")).toBe(false);
  });

  it("renders description for Step", () => {
    expect.assertions(8);

    const { wrapper } = renderWithAppLogic(Checklist, {
      // Avoids a blank description for the Upload Certification step,
      // which we have more unit tests for below to capture its other
      // variations
      claimAttrs: new MockClaimBuilder().bondingBirthLeaveReason().create(),
      diveLevels: 5,
      hasLoadedClaimDocuments: true,
    });
    const steps = wrapper.find("Step");

    steps.forEach((step) => {
      expect(step.find("Trans").dive()).toMatchSnapshot();
    });
  });

  it("renders 'In progress' version of Part 1 StepList description when claim isn't yet submitted", () => {
    const { wrapper } = renderWithAppLogic(Checklist, { diveLevels: 5 });
    const part1List = wrapper.find("StepList").at(0);

    expect(renderStepListDescription(part1List)).toMatchSnapshot();
  });

  describe("when Part 1 is submitted", () => {
    let wrapper;

    beforeEach(() => {
      const claim = new MockClaimBuilder().submitted().create();
      ({ wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels: 5,
      }));
    });

    it("renders different description for Part 1", () => {
      const part1List = wrapper.find("StepList").at(0);

      expect(renderStepListDescription(part1List)).toMatchSnapshot();
    });

    it("renders descriptions for Part 2 and 3", () => {
      const part2List = wrapper.find("StepList").at(1);
      const part3List = wrapper.find("StepList").at(2);

      expect(renderStepListDescription(part2List)).toMatchSnapshot();
      expect(renderStepListDescription(part3List)).toMatchSnapshot();
    });
  });

  it("enables Review and Submit button when all Parts are completed", () => {
    const claim = new MockClaimBuilder().complete().create();

    const { wrapper } = renderWithAppLogic(Checklist, {
      claimAttrs: claim,
      diveLevels: 5,
      hasLoadedClaimDocuments: true,
      hasUploadedIdDocuments: true,
      hasUploadedCertificationDocuments: true,
    });

    expect(wrapper.find("ButtonLink").prop("disabled")).toBe(false);
  });

  describe("Upload leave certification step", () => {
    it("renders medical leave content if claim reason is medical", () => {
      const claim = new MockClaimBuilder().submitted().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(7);
      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders newborn bonding leave content if claim reason is newborn", () => {
      const claim = new MockClaimBuilder()
        .submitted()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(7);

      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders adoption bonding leave content if claim reason is adoption", () => {
      const claim = new MockClaimBuilder()
        .submitted()
        .bondingAdoptionLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
      });
      const uploadCertificationStep = wrapper.find("Step").at(7);

      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when loading documents", () => {
    it("renders spinner for loading", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        diveLevels: 5,
      });

      expect(wrapper.exists("Spinner")).toBe(true);
      expect(wrapper.find("Step")).toHaveLength(6);
    });

    it("renders Alert when there is an error for loading documents", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        diveLevels: 5,
        hasLoadingDocumentsError: true,
      });

      expect(wrapper.find("StepList").at(2).exists("Alert")).toBe(true);
      expect(wrapper.find("Step")).toHaveLength(6);
    });
  });

  describe("Upload document steps status", () => {
    const startStatus = "not_started";
    const completeStatus = "completed";
    it("renders both doc steps as not completed", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: new MockClaimBuilder().complete().create(),
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
      });
      expect(wrapper.find("Step").at(6).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(7).prop("status")).toBe(startStatus);
    });

    it("renders id doc step as completed", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: new MockClaimBuilder().complete().create(),
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
        hasUploadedIdDocuments: true,
      });
      expect(wrapper.find("Step").at(6).prop("status")).toBe(completeStatus);
      expect(wrapper.find("Step").at(7).prop("status")).toBe(startStatus);
    });

    it("renders certification doc step as completed", () => {
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: new MockClaimBuilder().complete().create(),
        diveLevels: 5,
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: true,
      });
      expect(wrapper.find("Step").at(6).prop("status")).toBe(startStatus);
      expect(wrapper.find("Step").at(7).prop("status")).toBe(completeStatus);
    });
  });
});
