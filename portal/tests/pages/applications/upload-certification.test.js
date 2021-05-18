import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockBenefitsApplicationBuilder,
  makeFile,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import TempFileCollection from "../../../src/models/TempFileCollection";
import UploadCertification from "../../../src/pages/applications/upload-certification";
import { ValidationError } from "../../../src/errors";
import { act } from "react-dom/test-utils";
import { uniqueId } from "lodash";

jest.mock("../../../src/services/tracker");

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

const setup = (props = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(UploadCertification, {
    claimAttrs: new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create(),
    diveLevels,
    ...props,
  });
  const { submitForm } = simulateEvents(wrapper);
  return {
    appLogic,
    claim,
    submitForm,
    wrapper,
  };
};

describe("UploadCertification", () => {
  describe("before any documents have been loaded", () => {
    const { wrapper } = setup();

    it("does not render a FileCardList", () => {
      expect(wrapper.exists("FileCardList")).toBe(false);
    });

    it("renders a spinner", () => {
      expect(wrapper.find("Spinner")).toHaveLength(1);
    });

    it("does not render the ReviewRow block", () => {
      expect(wrapper.find("ReviewRow")).toEqual({});
    });

    it("renders page with medical leave content", () => {
      const { wrapper } = setup();
      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders page with bonding leave content when leave reason is Bonding leave", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = setup({ claimAttrs: claim });
      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });

    it("renders page with caregiver leave contentwhen leave reason is caregiver leave", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .caringLeaveReason()
        .create();
      const { wrapper } = setup({ claimAttrs: claim });
      // Only take snapshots of the i18n content
      expect(wrapper.find("Heading")).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when there are no previously uploaded documents", () => {
    it("does not render FileCard", () => {
      const { wrapper } = setup({ hasLoadedClaimDocuments: true });
      expect(
        wrapper.find("FileCardList").dive().find("FileCard").exists()
      ).toBe(false);
    });

    it("throws an error when saving without files", async () => {
      const { appLogic, submitForm } = setup({
        hasLoadedClaimDocuments: true,
      });
      jest.spyOn(appLogic._appErrorsLogic, "catchError");
      jest.spyOn(appLogic.portalFlow, "goToNextPage");
      await submitForm();

      expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
      expect(appLogic._appErrorsLogic.catchError).toHaveBeenCalledWith(
        new ValidationError(
          [
            {
              field: "file",
              message:
                "Client requires at least one file before sending request",
              type: "required",
            },
          ],
          "documents"
        )
      );
    });
  });

  describe("when there are previously loaded documents", () => {
    it("renders unremovable FileCard", () => {
      const { wrapper } = setup({
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: true,
      });

      const unremovableFileCards = wrapper
        .find("FileCardList")
        .dive()
        .findWhere(
          (component) =>
            component.name() === "FileCard" && component.prop("document")
        );
      expect(unremovableFileCards).toHaveLength(1);
    });

    it("navigates to checklist when saving without new files and does not make an API request", async () => {
      const { appLogic, submitForm } = setup({
        hasLoadedClaimDocuments: true,
        hasUploadedCertificationDocuments: true,
      });
      jest.spyOn(appLogic.portalFlow, "goToNextPage");
      jest.spyOn(appLogic.documents, "attach");
      await submitForm();
      expect(appLogic.documents.attach).not.toHaveBeenCalled();
      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalled();
    });
  });

  describe("when the user uploads files", () => {
    const expectedTempFiles = [
      expect.objectContaining({
        file: expect.objectContaining({ name: "file1" }),
      }),
      expect.objectContaining({
        file: expect.objectContaining({ name: "file2" }),
      }),
    ];
    const tempFiles = [
      makeFile({ name: "file1" }),
      makeFile({ name: "file2" }),
    ];

    it("passes files to FileCardList as a TempFileCollection", async () => {
      const { wrapper } = setup({
        hasLoadedClaimDocuments: true,
      });
      await act(async () => {
        await wrapper.find("FileCardList").simulate("change", tempFiles);
      });

      const tempFilesProp = wrapper.find("FileCardList").prop("tempFiles");
      expect(tempFilesProp).toBeInstanceOf(TempFileCollection);
      expect(tempFilesProp.items).toHaveLength(2);
    });

    it("renders removable file cards", async () => {
      const { wrapper } = setup({
        hasLoadedClaimDocuments: true,
      });
      await act(async () => {
        await wrapper.find("FileCardList").simulate("change", tempFiles);
      });

      const removableFileCards = wrapper
        .find("FileCardList")
        .dive()
        .findWhere(
          (component) =>
            component.name() === "FileCard" && component.prop("file")
        );
      expect(removableFileCards).toHaveLength(2);
    });

    it("makes API request when no previous documents exist", async () => {
      const { appLogic, claim, submitForm, wrapper } = setup({
        hasLoadedClaimDocuments: true,
      });

      await act(async () => {
        await wrapper.find("FileCardList").simulate("change", tempFiles);
      });
      jest.spyOn(appLogic.documents, "attach").mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );
      jest.spyOn(appLogic.portalFlow, "goToNextPage");
      await submitForm();

      expect(appLogic.documents.attach).toHaveBeenCalledWith(
        claim.application_id,
        expect.arrayContaining(expectedTempFiles),
        expect.any(String),
        false
      );

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledTimes(1);
    });

    it("displays unsucessfully uploaded files as removable file cards", async () => {
      const { appLogic, claim, submitForm, wrapper } = setup({
        hasLoadedClaimDocuments: true,
      });
      await act(async () => {
        await wrapper.find("FileCardList").simulate("change", tempFiles);
      });

      const attachSpy = jest
        .spyOn(appLogic.documents, "attach")
        .mockImplementation(
          jest.fn(() => {
            return [
              Promise.resolve({ success: true }),
              Promise.resolve({ success: false }),
            ];
          })
        );
      jest.spyOn(appLogic.portalFlow, "goToNextPage");
      await submitForm();

      const newDocuments = [
        new Document({
          document_type: DocumentType.medicalCertification,
          application_id: claim.application_id,
          created_at: "2020-10-12",
          fineos_document_id: uniqueId(),
        }),
      ];

      wrapper.setProps({ documents: newDocuments }); // force the documents to update because we don't have access to the collection in useDocumentsLogic

      const removableFileCards = wrapper
        .find("FileCardList")
        .dive()
        .findWhere(
          (component) =>
            component.name() === "FileCard" && component.prop("file")
        );
      const unremovableFileCards = wrapper
        .find("FileCardList")
        .dive()
        .findWhere(
          (component) =>
            component.name() === "FileCard" && component.prop("document")
        );
      expect(removableFileCards).toHaveLength(1);
      expect(unremovableFileCards).toHaveLength(1);
      expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();

      attachSpy.mockRestore();
    });
  });

  it("renders alert when there is an error loading documents ", () => {
    const { wrapper } = setup({
      hasLoadingDocumentsError: true,
    });
    expect(wrapper.exists("Alert")).toBe(true);
  });

  it("calls attach function with 'true' flag when there is additionalDoc flag in query", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create();
    const { appLogic, submitForm } = setup({
      claimAttrs: claim,
      hasLoadedClaimDocuments: true,
      props: {
        query: { claim_id: claim.application_id, additionalDoc: "true" },
      },
    });

    jest.spyOn(appLogic.documents, "attach");
    await submitForm();

    expect(appLogic.documents.attach).toHaveBeenCalledWith(
      claim.application_id,
      [],
      "State managed Paid Leave Confirmation",
      true
    );
  });

  // TODO(CP-2143): Add tests for `DocumentUploadError`
  it.todo("passes fileErrors into FileCard");
});
