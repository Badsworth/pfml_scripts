import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import Checklist from "../../../src/pages/claims/checklist";

describe("Checklist", () => {
  it("renders multiple StepList components with list of Steps", () => {
    const { wrapper } = renderWithAppLogic(Checklist);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders description for Step", () => {
    expect.assertions(8);

    const { wrapper } = renderWithAppLogic(Checklist, {
      // Avoids a blank description for the Upload Certification step,
      // which we have more unit tests for below to capture its other
      // variations
      claimAttrs: new MockClaimBuilder().bondingBirthLeaveReason().create(),
    });
    const steps = wrapper.find("Step");

    steps.forEach((step) => {
      expect(step.find("Trans").dive()).toMatchSnapshot();
    });
  });

  it("renders 'In progress' version of Part 1 StepList description when claim isn't yet submitted", () => {
    const { wrapper } = renderWithAppLogic(Checklist);
    const part1List = wrapper.find("StepList").at(0);

    expect(part1List.prop("description")).toMatchSnapshot();
  });

  describe("when Part 1 is submitted", () => {
    let wrapper;

    beforeEach(() => {
      const claim = new MockClaimBuilder().submitted().create();
      ({ wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
      }));
    });

    it("renders different description for Part 1", () => {
      const part1List = wrapper.find("StepList").first();

      expect(part1List.prop("description")).toMatchSnapshot();
    });

    it("renders descriptions for Part 2 and 3", () => {
      const part2List = wrapper.find("StepList").at(1);
      const part3List = wrapper.find("StepList").at(2);

      expect(part2List.prop("description")).toMatchSnapshot();
      expect(part3List.prop("description")).toMatchSnapshot();
    });
  });

  it("enables Review and Submit button when all Parts are completed", () => {
    const claim = new MockClaimBuilder().complete().create();

    const { wrapper } = renderWithAppLogic(Checklist, {
      claimAttrs: claim,
    });

    expect(wrapper.find("ButtonLink").prop("disabled")).toBe(false);
  });

  describe("Upload leave certification step", () => {
    it("renders medical leave content if claim reason is medical", () => {
      const claim = new MockClaimBuilder().submitted().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
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
      });
      const uploadCertificationStep = wrapper.find("Step").at(7);

      expect(uploadCertificationStep.find("Trans").dive()).toMatchSnapshot();
    });
  });
});
