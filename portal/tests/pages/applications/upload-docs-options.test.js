import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import tracker from "../../../src/services/tracker";
import uploadDocsOptions from "../../../src/pages/applications/upload-docs-options";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/services/tracker");

const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

const setAppErrors = jest.fn();

const setup = (claim) => {
  return renderPage(
    uploadDocsOptions,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.portalFlow.goToNextPage = goToNextPage;
        appLogic.setAppErrors = setAppErrors;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("UploadDocsOptions", () => {
  it.each([
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
  ])("renders document options for leave reason", (claim) => {
    setup(claim);
    const choices = screen.getAllByRole("radio");
    expect(choices).toMatchSnapshot(
      {},
      // include leave reason in snapshot title:
      `${claim.leave_details.reason} ${claim.leave_details.reason_qualifier}`
    );
  });

  it("routes to next page when a user chooses to upload Mass ID", async () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    setup(claim);
    const claim_id = claim.application_id;

    userEvent.click(
      screen.getByRole("radio", {
        name: "Massachusetts driver’s license or ID",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id, showStateId: true, additionalDoc: "true" },
        "UPLOAD_MASS_ID"
      );
    });
  });

  it("routes to next page when a user chooses to upload non Mass ID", async () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    setup(claim);
    const claim_id = claim.application_id;

    userEvent.click(
      screen.getByRole("radio", {
        name: "Different identification documentation",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id, showStateId: false, additionalDoc: "true" },
        "UPLOAD_ID"
      );
    });
  });

  it("routes to next page when a user chooses to upload a certification document", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .completed()
      .create();

    setup(claim);
    const claim_id = claim.application_id;

    userEvent.click(
      screen.getByRole("radio", {
        name: "Certification of Your Serious Health Condition",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(goToNextPage).toHaveBeenCalledWith(
        { claim },
        { claim_id, additionalDoc: "true" },
        "UPLOAD_CERTIFICATION"
      );
    });
  });

  it("shows a validation error when a user does not choose a doc type option", async () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    setup(claim);
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "upload_docs_options",
        issueType: "required",
      });
      expect(goToNextPage).not.toHaveBeenCalled();
      expect(setAppErrors).toHaveBeenCalledTimes(1);
    });
  });
});
