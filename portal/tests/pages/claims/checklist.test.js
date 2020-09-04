import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import Checklist from "../../../src/pages/claims/checklist";

describe("Checklist", () => {
  describe("when claim has not been started", () => {
    it("renders initial checklist state", () => {
      const { wrapper } = renderWithAppLogic(Checklist);

      expect(wrapper).toMatchSnapshot();
    });
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
    it("renders correctly if claim reason is medical", () => {
      const claim = new MockClaimBuilder().submitted().create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
      });
      const uploadCertificationStep = wrapper.find("Step").at(5);
      expect(uploadCertificationStep).toMatchSnapshot();
    });

    it("renders correctly if claim reason is newborn", () => {
      const claim = new MockClaimBuilder()
        .submitted()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
      });
      const uploadCertificationStep = wrapper.find("Step").at(5);
      expect(uploadCertificationStep).toMatchSnapshot();
    });

    it("renders correctly if claim reason is adoption", () => {
      const claim = new MockClaimBuilder()
        .submitted()
        .bondingAdoptionLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Checklist, {
        claimAttrs: claim,
      });
      const uploadCertificationStep = wrapper.find("Step").at(5);
      expect(uploadCertificationStep).toMatchSnapshot();
    });
  });
});
