import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import UploadDocsOptions, {
  UploadType,
} from "../../../src/pages/applications/upload-docs-options";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadDocsOptions", () => {
  let appLogic, changeRadioGroup, claim, wrapper;

  it("renders the page for medical leave with HCP as cert option", () => {
    ({ wrapper } = renderWithAppLogic(UploadDocsOptions, {
      claimAttrs: new MockClaimBuilder()
        .medicalLeaveReason()
        .completed()
        .create(),
    }));
    expect(wrapper.find("InputChoiceGroup").prop("choices")).toMatchSnapshot();
    expect(wrapper.html()).not.toMatch("Proof of placement");
    expect(wrapper.html()).toMatch("Health Care Provider Certification");
  });

  it("renders the appropriate cert option for newborn bonding leave", () => {
    ({ wrapper } = renderWithAppLogic(UploadDocsOptions, {
      claimAttrs: new MockClaimBuilder()
        .completed()
        .bondingBirthLeaveReason()
        .create(),
    }));
    expect(wrapper.find("InputChoiceGroup").prop("choices")).toMatchSnapshot();
    expect(wrapper.html()).toMatch("Proof of birth");
  });

  it("renders the appropriate cert option for adoption bonding leave", () => {
    ({ wrapper } = renderWithAppLogic(UploadDocsOptions, {
      claimAttrs: new MockClaimBuilder()
        .completed()
        .bondingAdoptionLeaveReason()
        .create(),
    }));
    expect(wrapper.find("InputChoiceGroup").prop("choices")).toMatchSnapshot();
    expect(wrapper.html()).toMatch("Proof of placement");
  });

  describe("when a user chooses to upload Mass ID", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(UploadDocsOptions, {
        claimAttrs: new MockClaimBuilder().completed().create(),
      }));
      ({ changeRadioGroup } = simulateEvents(wrapper));
      changeRadioGroup("upload_docs_options", UploadType.mass_id);
    });

    it("redirects to the upload_id page", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      const claim_id = claim.application_id;
      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id, showStateId: true },
        "UPLOAD_MASS_ID"
      );
    });
  });

  describe("when a user chooses to upload non Mass ID", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(UploadDocsOptions, {
        claimAttrs: new MockClaimBuilder().completed().create(),
      }));
      ({ changeRadioGroup } = simulateEvents(wrapper));
      changeRadioGroup("upload_docs_options", UploadType.non_mass_id);
    });

    it("redirects to the upload_id page", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      const claim_id = claim.application_id;
      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id, showStateId: false },
        "UPLOAD_ID"
      );
    });
  });

  describe("when a user chooses to upload cert", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(UploadDocsOptions, {
        claimAttrs: new MockClaimBuilder().completed().create(),
      }));
      ({ changeRadioGroup } = simulateEvents(wrapper));
      changeRadioGroup("upload_docs_options", UploadType.certification);
    });

    it("redirects to the upload_certification page", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      const claim_id = claim.application_id;
      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id },
        "UPLOAD_CERTIFICATION"
      );
    });
  });
});
