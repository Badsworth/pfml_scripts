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
import UploadId from "../../../src/pages/applications/upload-id";
import { createMockBenefitsApplicationDocument } from "../../../lib/mock-helpers/createMockDocument";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");
jest.mock("../../../src/services/tracker");

const expectedTempFiles = [
  expect.objectContaining({
    file: expect.objectContaining({ name: "file1" }),
  }),
  expect.objectContaining({
    file: expect.objectContaining({ name: "file2" }),
  }),
];

const cbHasLoadedClaimDocsTrue = (appLogic: AppLogic) => {
  appLogic.documents.hasLoadedClaimDocuments = jest.fn().mockReturnValue(true);
};

const clearErrors = jest.fn();
const catchError = jest.fn();

const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

let attach = jest.fn();

const setup = (
  claim = new MockBenefitsApplicationBuilder().medicalLeaveReason().create(),
  props = {},
  cb?: (appLogic: AppLogic) => void
) => {
  return renderPage(
    UploadId,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim], cb);
        appLogic.portalFlow.goToNextPage = goToNextPage;
        appLogic.documents.attach = attach;
        appLogic.clearErrors = clearErrors;
        appLogic.catchError = catchError;
      },
    },
    { query: { claim_id: "mock_application_id" }, ...props }
  );
};

describe("UploadId", () => {
  describe("before any documents have been loaded", () => {
    beforeEach(() => {
      setup();
    });

    it("does not render a FileCardList", () => {
      expect(screen.queryByText(/File/)).not.toBeInTheDocument();
    });

    it("renders a spinner", () => {
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });
  });

  describe("after documents have been loaded", () => {
    it("when the user doesn't have a Mass ID, renders the page with 'Other' ID content", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .create();
      claim.has_state_id = false;
      const { container } = setup(claim, undefined, cbHasLoadedClaimDocsTrue);
      expect(container).toMatchSnapshot();
    });

    describe("when the user has a Mass ID", () => {
      const cb = (appLogic: AppLogic) => {
        appLogic.documents.hasLoadedClaimDocuments = jest
          .fn()
          .mockReturnValue(true);
        appLogic.documents.documents =
          new ApiResourceCollection<BenefitsApplicationDocument>(
            "fineos_document_id",
            [
              createMockBenefitsApplicationDocument({
                document_type: DocumentType.identityVerification,
              }),
            ]
          );
      };
      beforeEach(() => {
        const claim = new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .create();
        claim.has_state_id = true;
        setup(claim, undefined, cb);
      });

      it("renders a FileCardList", () => {
        expect(screen.queryByText(/File/)).toBeInTheDocument();
      });

      it("doesn't render a spinner", () => {
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      });

      it("renders the page with Mass ID content", () => {
        expect(
          screen.getByText(
            /Upload the front and back of your Massachusetts driver’s license or ID card/
          )
        ).toBeInTheDocument();
        expect(
          screen.getByRole("heading", { name: "File 1" })
        ).toBeInTheDocument();
        expect(screen.getByText("Choose files")).toBeInTheDocument();
      });
    });

    it("when the user uploads files, renders filecards for the files", async () => {
      setup(undefined, undefined, cbHasLoadedClaimDocsTrue);
      const tempFiles = [makeFile(), makeFile(), makeFile()];
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });
      await waitFor(() => {
        expect(screen.getAllByText(/File/)).toHaveLength(3);
      });
    });

    it("clears errors", async () => {
      setup(undefined, undefined, cbHasLoadedClaimDocsTrue);
      const tempFiles = [makeFile(), makeFile(), makeFile()];
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });

      expect(clearErrors).toHaveBeenCalledTimes(1);
    });

    it("catches invalid files", async () => {
      setup(undefined, undefined, cbHasLoadedClaimDocsTrue);
      const invalidFiles = [makeFile({ name: "file1", type: "image/heic" })];
      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          invalidFiles
        );
      });

      await waitFor(() => {
        expect(catchError).toHaveBeenCalledWith(
          new ValidationError([
            {
              field: "file",
              message:
                "We could not upload: file1. Choose a PDF or an image file (.jpg, .jpeg, .png).",
              type: "required",
              namespace: "documents",
            },
          ])
        );
      });
    });

    it("makes documents.attach request when no documents exist", async () => {
      const claim = new MockBenefitsApplicationBuilder().create();
      setup(claim, undefined, cbHasLoadedClaimDocsTrue);

      const tempFiles = [
        makeFile({ name: "file1" }),
        makeFile({ name: "file2" }),
      ];

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
          claim.application_id,
          expect.arrayContaining(expectedTempFiles),
          expect.any(String),
          false
        );
      });
    });

    it("navigates the user to the next page if there are no errors", async () => {
      const tempFiles = [makeFile(), makeFile(), makeFile()];
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );
      setup(undefined, undefined, cbHasLoadedClaimDocsTrue);

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
        expect(goToNextPage).toHaveBeenCalled();
      });
    });

    it("does not navigate the user to the next page if there are errors", async () => {
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [Promise.resolve({ success: false })];
        })
      );
      const tempFiles = [makeFile()];
      setup(undefined, undefined, cbHasLoadedClaimDocsTrue);

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
        expect(goToNextPage).not.toHaveBeenCalled();
      });
    });

    it("displays successfully uploaded files as unremovable file cards", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .create();

      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );

      const tempFiles = [
        makeFile({ name: "File1" }),
        makeFile({ name: "File2" }),
        makeFile({ name: "File3" }),
      ];

      setup(claim, undefined, cbHasLoadedClaimDocsTrue);

      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });
      await waitFor(() => {
        expect(screen.getAllByText(/File /)).toHaveLength(3);
        expect(
          screen.queryByText(/You can’t remove files previously uploaded./)
        ).not.toBeInTheDocument();
      });

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(screen.queryByText(/File [0-9]/)).not.toBeInTheDocument();
      });
    });

    it("displays unsucessfully uploaded files as removable file cards", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .create();
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
            Promise.resolve({ success: false }),
          ];
        })
      );

      setup(claim, undefined, cbHasLoadedClaimDocsTrue);

      const tempFiles = [
        makeFile({ name: "File1" }),
        makeFile({ name: "File2" }),
        makeFile({ name: "File3" }),
      ];

      await act(async () => {
        await userEvent.upload(
          screen.getByLabelText(/Choose files/),
          tempFiles
        );
      });

      await waitFor(() => {
        expect(
          screen.getAllByRole("heading", { name: /File [0-9]/ })
        ).toHaveLength(3);
        expect(
          screen.queryByText(/You can’t remove files previously uploaded./)
        ).not.toBeInTheDocument();
      });

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: /File/ })
        ).toBeInTheDocument();
      });
    });

    it("redirects to the Applications page when the claim has been completed", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .create();
      attach = jest.fn().mockImplementation(
        jest.fn(() => {
          return [
            Promise.resolve({ success: true }),
            Promise.resolve({ success: true }),
          ];
        })
      );

      setup(claim, undefined, cbHasLoadedClaimDocsTrue);
      // Add files to the page state
      const tempFiles = [makeFile(), makeFile()];
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
        expect(goToNextPage).toHaveBeenCalledWith(
          { claim },
          {
            claim_id: claim.application_id,
            uploadedAbsenceId: claim.fineos_absence_id,
          }
        );
      });
    });

    describe("when there are previously loaded documents", () => {
      it("renders the FileCardList with documents", () => {
        const cb = (appLogic: AppLogic) => {
          appLogic.documents.hasLoadedClaimDocuments = jest
            .fn()
            .mockReturnValue(true);
          appLogic.documents.documents =
            new ApiResourceCollection<BenefitsApplicationDocument>(
              "fineos_document_id",
              [
                createMockBenefitsApplicationDocument({
                  document_type: DocumentType.identityVerification,
                }),
              ]
            );
        };
        setup(undefined, undefined, cb);
        expect(screen.getByText(/File/)).toBeInTheDocument();
      });

      it("makes API request when there are new files", async () => {
        const claim = new MockBenefitsApplicationBuilder().create();
        const cb = (appLogic: AppLogic) => {
          appLogic.documents.hasLoadedClaimDocuments = jest
            .fn()
            .mockReturnValue(true);
          appLogic.documents.documents =
            new ApiResourceCollection<BenefitsApplicationDocument>(
              "fineos_document_id",
              [
                createMockBenefitsApplicationDocument({
                  document_type: DocumentType.identityVerification,
                }),
              ]
            );
        };
        setup(claim, undefined, cb);
        const tempFiles = [
          makeFile({ name: "file1" }),
          makeFile({ name: "file2" }),
        ];

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
            claim.application_id,
            expect.arrayContaining(expectedTempFiles),
            expect.any(String),
            false
          );
        });
      });

      it("skips an API request if there are no new files added", async () => {
        const cb = (appLogic: AppLogic) => {
          appLogic.documents.hasLoadedClaimDocuments = jest
            .fn()
            .mockReturnValue(true);
          appLogic.documents.documents =
            new ApiResourceCollection<BenefitsApplicationDocument>(
              "fineos_document_id",
              [
                createMockBenefitsApplicationDocument({
                  document_type: DocumentType.identityVerification,
                }),
              ]
            );
        };

        setup(undefined, undefined, cb);

        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        await waitFor(() => {
          expect(attach).not.toHaveBeenCalled();
          expect(goToNextPage).toHaveBeenCalledTimes(1);
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

    it("When uploading additional docs", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .create();
      attach = jest.fn();

      setup(undefined, {
        query: { claim_id: claim.application_id, additionalDoc: "true" },
      });

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(attach).toHaveBeenCalledWith(
          claim.application_id,
          [],
          DocumentType.identityVerification,
          true
        );
      });
    });
  });
});
