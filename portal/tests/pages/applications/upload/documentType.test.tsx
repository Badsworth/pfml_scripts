import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../../src/models/Document";
import { DocumentsLoadError, ValidationError } from "../../../../src/errors";
import UploadDocument, {
  DocumentUploadProps,
  getStaticPaths,
} from "../../../../src/pages/applications/upload/[documentType]";

import { act, screen, waitFor } from "@testing-library/react";
import { makeFile, renderPage } from "../../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../../src/hooks/useAppLogic";
import LeaveReason from "../../../../src/models/LeaveReason";
import { createMockBenefitsApplicationDocument } from "../../../../lib/mock-helpers/createMockDocument";
import userEvent from "@testing-library/user-event";

function setup(
  documentType: DocumentUploadProps["query"]["documentType"] = "state-id",
  addCustomSetup?: (appLogic: AppLogic) => void
) {
  let attachSpy: jest.SpyInstance | undefined; // some tests rely on the unmocked method
  const goToNextPageSpy = jest.fn();

  const utils = renderPage(
    UploadDocument,
    {
      pathname: `/applications/upload/${documentType}`,
      addCustomSetup: (appLogic: AppLogic) => {
        attachSpy = jest.spyOn(appLogic.documents, "attach");
        appLogic.documents.loadAll = jest.fn();
        appLogic.documents.hasLoadedClaimDocuments = jest
          .fn()
          .mockReturnValue(true);
        appLogic.portalFlow.goToNextPage = goToNextPageSpy;
        appLogic.portalFlow.pageRoute = `/applications/upload/${documentType}`;

        if (addCustomSetup) {
          addCustomSetup(appLogic);
        }
      },
    },
    {
      query: {
        documentType,
        claim_id: "mock-claim-id",
        absence_id: "mock-absence-case-id",
      },
    }
  );

  return { ...utils, attachSpy, goToNextPageSpy };
}

describe(UploadDocument, () => {
  it.each(["state-id", "other-id"] as const)(
    `renders the appropriate identification upload content for applications/upload/%s`,
    (documentType) => {
      const { container } = setup(documentType);
      expect(container.firstChild).toMatchSnapshot();
    }
  );

  it.each([
    "proof-of-birth",
    "proof-of-placement",
    "medical-certification",
    "family-member-medical-certification",
    "pregnancy-medical-certification",
  ] as const)(
    "renders the appropriate certification upload content for applications/upload/%s",
    (documentType) => {
      const { container } = setup(documentType);

      expect(container.firstChild).toMatchSnapshot();
    }
  );

  describe("before any documents have been loaded", () => {
    beforeEach(() => {
      setup("state-id", (appLogic) => {
        appLogic.documents.hasLoadedClaimDocuments = jest
          .fn()
          .mockReturnValue(false);
      });
    });

    it("renders spinner", () => {
      const spinner = screen.getByRole("progressbar");

      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveAttribute("aria-label", "Loading documents");
    });

    it("does not show file card rows", () => {
      const fileCards = screen.queryByTestId("file-card");
      expect(fileCards).not.toBeInTheDocument();
    });
  });

  describe("when there are no previously uploaded documents", () => {
    it("does not show file card rows", () => {
      setup();

      const fileCards = screen.queryByTestId("file-card");
      expect(fileCards).not.toBeInTheDocument();
    });

    it("shows error when saving without files", async () => {
      let appLogic: AppLogic | undefined;
      const { goToNextPageSpy } = setup("state-id", (_appLogic) => {
        appLogic = _appLogic;
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      await waitFor(() => {
        expect(appLogic?.errors[0]).toBeInstanceOf(ValidationError);

        if (appLogic?.errors[0] instanceof ValidationError) {
          expect(appLogic?.errors[0].issues).toEqual([
            expect.objectContaining({
              field: "file",
              type: "required",
            }),
          ]);
        }
      });
      expect(goToNextPageSpy).not.toHaveBeenCalled();
    });
  });

  describe("when there are previously loaded documents", () => {
    const mockAppLogic = (appLogic: AppLogic) => {
      appLogic.documents.documents =
        new ApiResourceCollection<BenefitsApplicationDocument>(
          "fineos_document_id",
          [
            createMockBenefitsApplicationDocument({
              application_id: "mock-claim-id",
              document_type: DocumentType.identityVerification,
            }),
          ]
        );
    };

    it("renders unremovable FileCard", async () => {
      setup("state-id", mockAppLogic);

      const fileCards = await screen.findByRole("heading", {
        level: 3,
        name: /File \d+/,
      });
      const unremovableFileCards = await screen.findByText(
        /You can’t remove files previously uploaded./
      );

      expect(fileCards).toBeInTheDocument();
      expect(unremovableFileCards).toBeInTheDocument();
    });

    it("navigates to checklist when saving without new files and does not make an API request", async () => {
      const { attachSpy, goToNextPageSpy } = setup("state-id", mockAppLogic);

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      expect(attachSpy).not.toHaveBeenCalled();
      expect(goToNextPageSpy).toHaveBeenCalledWith(
        { isAdditionalDoc: true },
        { claim_id: "mock-claim-id", absence_id: "mock-absence-case-id" }
      );
    });
  });

  describe("when user uploads files", () => {
    const tempFiles = [
      makeFile({ name: "file1" }),
      makeFile({ name: "file2" }),
    ];

    const selectFiles = async () => {
      const chooseFilesButton = screen.getByLabelText(/Choose files/);
      await act(async () => {
        await userEvent.upload(chooseFilesButton, tempFiles);
      });
    };

    it("renders removable files", async () => {
      setup();
      await selectFiles();

      const files = await screen.findAllByText(/File \d+/);
      expect(files).toHaveLength(2);
    });

    it("makes API request when user clicks save and continue", async () => {
      const attachSpy = jest
        .fn()
        .mockReturnValue([
          Promise.resolve({ success: true }),
          Promise.resolve({ success: true }),
        ]);

      const { goToNextPageSpy } = setup("state-id", (appLogic) => {
        appLogic.documents.attach = attachSpy;
      });

      await selectFiles();

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      await waitFor(() => {
        expect(attachSpy).toHaveBeenCalledWith(
          "mock-claim-id",
          expect.arrayContaining([
            expect.objectContaining({
              file: expect.objectContaining({ name: "file1" }),
            }),
            expect.objectContaining({
              file: expect.objectContaining({ name: "file2" }),
            }),
          ]),
          expect.any(String),
          true
        );
      });

      expect(goToNextPageSpy).toHaveBeenCalledTimes(1);
    });

    it("displays unsuccessfully uploaded files as removable file cards", async () => {
      const attachSpy = jest
        .fn()
        .mockReturnValue([
          Promise.resolve({ success: true }),
          Promise.resolve({ success: false }),
        ]);

      const { goToNextPageSpy } = setup("state-id", (appLogic) => {
        appLogic.documents.attach = attachSpy;
      });

      await selectFiles();

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      const fileCards = await screen.findByText(/File \d+/);
      const unremovableFileCards = screen.queryByText(
        /You can’t remove files previously uploaded./
      );
      expect(fileCards).toBeInTheDocument();
      expect(unremovableFileCards).not.toBeInTheDocument();
      expect(goToNextPageSpy).not.toHaveBeenCalled();
    });
  });

  it("renders alert when there is an error loading documents ", async () => {
    setup("state-id", (appLogic) => {
      appLogic.errors = [new DocumentsLoadError("mock-claim-id")];
    });

    const alert = await screen.findByRole("alert");
    expect(alert).toMatchInlineSnapshot(`
      <div
        class="usa-alert usa-alert--error usa-alert--no-icon margin-bottom-3"
        role="alert"
        tabindex="-1"
      >
        <div
          class="usa-alert__body"
        >
          <div
            class="usa-alert__text"
          >
            An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at 
            <a
              href="tel:(833) 344-7365"
            >
              (833) 344‑7365
            </a>
            .
          </div>
        </div>
      </div>
    `);
  });

  it("calls attach function with 'true' flag when there is additionalDoc flag in query", async () => {
    const { attachSpy } = setup("state-id");

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(attachSpy).toHaveBeenCalledWith(
      "mock-claim-id",
      [],
      expect.any(String),
      true
    );
  });

  const docTypes = [
    [DocumentType.identityVerification, "state-id"],
    [DocumentType.identityVerification, "other-id"],
    [DocumentType.certification[LeaveReason.bonding], "proof-of-birth"],
    [DocumentType.certification[LeaveReason.bonding], "proof-of-placement"],
    [DocumentType.certification[LeaveReason.medical], "medical-certification"],
    [
      DocumentType.certification[LeaveReason.care],
      "family-member-medical-certification",
    ],
    [
      DocumentType.certification[LeaveReason.pregnancy],
      "pregnancy-medical-certification",
    ],
  ] as const;

  it.each(docTypes)(
    `uploads the "%s" document type for /applications/upload/%s`,
    async (documentType, documentTypeParam) => {
      const attachSpy = jest
        .fn()
        .mockReturnValue([Promise.resolve({ success: true })]);
      const { goToNextPageSpy } = setup(documentTypeParam, (appLogic) => {
        appLogic.documents.attach = attachSpy;
      });

      const chooseFilesButton = screen.getByLabelText(/Choose files/);
      await act(async () => {
        await userEvent.upload(chooseFilesButton, [
          makeFile({ name: "file1" }),
        ]);
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => {
        await userEvent.click(submitButton);
      });

      expect(attachSpy).toHaveBeenCalledWith(
        "mock-claim-id",
        expect.any(Array),
        documentType,
        true
      );

      expect(goToNextPageSpy).toHaveBeenCalledWith(
        { isAdditionalDoc: true },
        {
          claim_id: "mock-claim-id",
          absence_id: "mock-absence-case-id",
          uploaded_document_type: documentTypeParam,
        }
      );
    }
  );
});

describe(getStaticPaths, () => {
  it("returns a path for each document type", async () => {
    const { paths } = await getStaticPaths();
    expect(paths).toEqual([
      { params: { documentType: "proof-of-placement" } },
      { params: { documentType: "proof-of-birth" } },
      { params: { documentType: "family-member-medical-certification" } },
      { params: { documentType: "medical-certification" } },
      { params: { documentType: "other-id" } },
      { params: { documentType: "pregnancy-medical-certification" } },
      { params: { documentType: "state-id" } },
    ]);
  });
});
