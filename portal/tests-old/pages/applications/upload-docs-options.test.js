import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import UploadDocsOptions, {
  UploadType,
} from "../../../src/pages/applications/upload-docs-options";
import tracker from "../../../src/services/tracker";

jest.mock("../../../src/services/tracker");
jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(UploadDocsOptions, {
    claimAttrs,
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("UploadDocsOptions", () => {
  it("renders document options for leave reason", () => {
    expect.assertions();

    const claims = [
      new MockBenefitsApplicationBuilder()
        .completed()
        .medicalLeaveReason()
        .create(),
      new MockBenefitsApplicationBuilder()
        .completed()
        .caringLeaveReason()
        .create(),
      new MockBenefitsApplicationBuilder()
        .completed()
        .bondingBirthLeaveReason()
        .create(),
      new MockBenefitsApplicationBuilder()
        .completed()
        .bondingAdoptionLeaveReason()
        .create(),
    ];

    claims.forEach((claim) => {
      const { wrapper } = setup(claim);
      const choices = wrapper.find("InputChoiceGroup").prop("choices");

      expect(choices).toMatchSnapshot(
        {},
        // include leave reason in snapshot title:
        `${claim.leave_details.reason} ${claim.leave_details.reason_qualifier}`
      );
    });
  });

  it("routes to next page when a user chooses to upload Mass ID", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup(
      new MockBenefitsApplicationBuilder().completed().create()
    );

    changeRadioGroup("upload_docs_options", UploadType.mass_id);
    await submitForm();
    const claim_id = claim.application_id;

    expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
      { claim },
      { claim_id, showStateId: true, additionalDoc: "true" },
      "UPLOAD_MASS_ID"
    );
  });

  it("routes to next page when a user chooses to upload non Mass ID", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup(
      new MockBenefitsApplicationBuilder().completed().create()
    );

    changeRadioGroup("upload_docs_options", UploadType.non_mass_id);
    await submitForm();
    const claim_id = claim.application_id;

    expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
      { claim },
      { claim_id, showStateId: false, additionalDoc: "true" },
      "UPLOAD_ID"
    );
  });

  it("routes to next page when a user chooses to upload a certification document", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup(
      new MockBenefitsApplicationBuilder().completed().create()
    );

    changeRadioGroup("upload_docs_options", UploadType.certification);
    await submitForm();
    const claim_id = claim.application_id;

    expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
      { claim },
      { claim_id, additionalDoc: "true" },
      "UPLOAD_CERTIFICATION"
    );
  });

  it("shows a validation error when a user does not choose a doc type option", async () => {
    const { appLogic, submitForm } = setup(
      new MockBenefitsApplicationBuilder().completed().create()
    );

    await submitForm();

    expect(appLogic.setAppErrors).toHaveBeenCalledTimes(1);
    expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
      issueField: "upload_docs_options",
      issueType: "required",
    });
    expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
  });
});
