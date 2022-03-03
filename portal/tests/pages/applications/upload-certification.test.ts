import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../src/models/Document";
import { DocumentsLoadError, ValidationError } from "../../../src/errors";
import {
  MockBenefitsApplicationBuilder,
  makeFile,
  renderPage,
} from "../../test-utils";
import { act, screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import UploadCertification from "../../../src/pages/applications/upload-certification";
import { createMockBenefitsApplicationDocument } from "../../../lib/mock-helpers/createMockDocument";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

const catchError = jest.fn();

let attach = jest.fn().mockResolvedValue([]);

const setup = (
  claim = new MockBenefitsApplicationBuilder().medicalLeaveReason().create(),
  props = {},
  cb?: (appLogic: AppLogic) => void
) => {
  return renderPage(
    UploadCertification,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        if (cb) cb(appLogic);
        appLogic.portalFlow.goToNextPage = goToNextPage;
        appLogic._errorsLogic.catchError = catchError;
        appLogic.documents.attach = attach;
      },
    },
    { query: { claim_id: "mock_application_id" }, ...props }
  );
};

describe("UploadCertification", () => {
  describe("before any documents have been loaded", () => {
    it("does not render a FileCardList", () => {
      setup();
      expect(screen.queryByText(/File/)).not.toBeInTheDocument();
    });

    it("renders a spinner", () => {
      setup();
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("renders page with medical leave content", () => {
      setup();
      expect(
        screen.getByRole("heading", { name: "Upload your certification form" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Certification of Your Serious Health Condition",
        })
      ).toBeInTheDocument();
    });

    it("renders page with bonding leave content when leave reason is Bonding leave", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason()
        .create();
      setup(claim);
      expect(
        screen.getByRole("heading", { name: "Upload your documentation" })
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /You need to upload one of the following documents to confirm your child’s date of birth/
        )
      ).toBeInTheDocument();
    });

    it("renders page with caregiver leave content when leave reason is caregiver leave", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .caringLeaveReason()
        .create();
      setup(claim);
      expect(
        screen.getByRole("heading", { name: "Upload your certification form" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Certification of Your Family Member’s Serious Health Condition",
        })
      ).toBeInTheDocument();
    });
  });

  describe("when there are no previously uploaded documents", () => {
    it("does not render FileCard", () => {
      setup();
      expect(screen.queryByText(/File/)).not.toBeInTheDocument();
    });

    it("throws an error when saving without files", async () => {
      setup();
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(goToNextPage).not.toHaveBeenCalled();
        expect(catchError).toHaveBeenCalledWith(
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
  });

  describe("when there are previously loaded documents", () => {
    const cb = (appLogic: AppLogic) => {
      appLogic.documents.hasLoadedClaimDocuments = jest
        .fn()
        .mockReturnValue(true);
      appLogic.documents.documents =
        new ApiResourceCollection<BenefitsApplicationDocument>(
          "fineos_document_id",
          [
            createMockBenefitsApplicationDocument({
              document_type: DocumentType.certification.medicalCertification,
            }),
          ]
        );
    };
    it("renders unremovable FileCard", () => {
      setup(undefined, undefined, cb);
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      expect(
        screen.getByText(/You can’t remove files previously uploaded./)
      ).toBeInTheDocument();
    });

    it("navigates to checklist when saving without new files and does not make an API request", async () => {
      setup(undefined, undefined, cb);
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(goToNextPage).toHaveBeenCalled();
        expect(attach).not.toHaveBeenCalled();
      });
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

    const cb = (appLogic: AppLogic) => {
      appLogic.documents.hasLoadedClaimDocuments = jest
        .fn()
        .mockReturnValue(true);
    };

    it("renders removable file cards", async () => {
      setup(undefined, undefined, cb);
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();

      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });

      expect(screen.getAllByText(/File/)).toHaveLength(2);
      expect(
        screen.getAllByRole("button", { name: "Remove file" })
      ).toHaveLength(2);
    });

    it("makes API request when no previous documents exist", async () => {
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );
      setup(undefined, undefined, cb);
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(attach).toHaveBeenCalledWith(
          "mock_application_id",
          expect.arrayContaining(expectedTempFiles),
          DocumentType.certification.certificationForm,
          false
        );
        expect(goToNextPage).toHaveBeenCalledTimes(1);
      });
    });

    it("displays unsuccessfully uploaded files as removable file cards", async () => {
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: false }),
          ];
        })
      );
      setup(undefined, undefined, cb);
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });
      expect(screen.getAllByText(/File/)).toHaveLength(2); // now we have 2 cards displayed

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(screen.getByText(/File/)).toBeInTheDocument(); // now we have 1 card displayed
        expect(goToNextPage).not.toHaveBeenCalled();
      });
    });

    it("uses Certification Form as the doc type", async () => {
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );
      setup(undefined, undefined, cb);
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });
      expect(
        screen.getAllByRole("button", { name: "Remove file" })[0]
      ).toBeEnabled();
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      expect(
        screen.getAllByRole("button", { name: "Remove file" })[0]
      ).toBeDisabled();

      await waitFor(() => {
        expect(attach).toHaveBeenCalledWith(
          "mock_application_id",
          expect.arrayContaining(expectedTempFiles),
          DocumentType.certification.certificationForm,
          false
        );
      });
    });
  });

  it("renders alert when there is an error loading documents", () => {
    const cb = (appLogic: AppLogic) => {
      appLogic.errors = [new DocumentsLoadError("mock_application_id")];
    };
    setup(undefined, undefined, cb);
    expect(
      screen.getByText(
        /An error was encountered while checking your application for documents./
      )
    ).toBeInTheDocument();
  });

  it("calls attach function with 'true' flag when there is additionalDoc flag in query", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create();
    attach = jest.fn().mockResolvedValue([]);

    setup(claim, {
      query: { claim_id: claim.application_id, additionalDoc: "true" },
    });

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(attach).toHaveBeenCalledWith(
        claim.application_id,
        [],
        DocumentType.certification.certificationForm,
        true
      );
    });
  });
});
