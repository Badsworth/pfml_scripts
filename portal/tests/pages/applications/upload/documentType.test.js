import Document, { DocumentType } from "../../../../src/models/Document";
import UploadDocument, {
  getStaticPaths,
} from "../../../../src/pages/applications/upload/[documentType]";

import { act, render, screen } from "@testing-library/react";
import AppErrorInfo from "../../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../../src/models/AppErrorInfoCollection";
import LeaveReason from "../../../../src/models/LeaveReason";
import React from "react";
import User from "../../../../src/models/User";

import { makeFile } from "../../../test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";
import userEvent from "@testing-library/user-event";
import { v4 as uuidv4 } from "uuid";

const UploadDocumentWithAppLogic = ({
  // eslint-disable-next-line react/prop-types
  addAppLogicMocks = (appLogic) => {},
  ...props
}) => {
  const appLogic = useAppLogic();
  appLogic.auth.requireLogin = jest.fn();
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.requireUserRole = jest.fn();
  appLogic.users.user = new User({ consented_to_data_sharing: true });
  appLogic.portalFlow.pathWithParams = `/applications/upload/${props.query.documentType}/?application_id=${props.query.claim_id}`;

  appLogic.documents.loadAll = jest.fn();

  addAppLogicMocks(appLogic);

  return <UploadDocument appLogic={appLogic} {...props} />;
};

describe(UploadDocument, () => {
  it.each(["state-id", "other-id"])(
    `renders the appropriate identification upload content for applications/upload/%s`,
    (documentType) => {
      const { container } = render(
        <UploadDocumentWithAppLogic
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType,
          }}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    }
  );

  it.each([
    "proof-of-birth",
    "proof-of-placement",
    "medical-certification",
    "family-member-medical-certification",
    "pregnancy-medical-certification",
  ])(
    "renders the appropriate certification upload content for applications/upload/%s",
    (documentType) => {
      const { container } = render(
        <UploadDocumentWithAppLogic
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType,
          }}
        />
      );

      expect(container.firstChild).toMatchSnapshot();
    }
  );

  describe("before any documents have been loaded", () => {
    beforeEach(() => {
      render(
        <UploadDocumentWithAppLogic
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType: "state-id",
          }}
        />
      );
    });

    it("renders spinner", () => {
      const spinner = screen.getByRole("progressbar");

      expect(spinner).toBeInTheDocument();
      expect(spinner.getAttribute("aria-valuetext")).toEqual(
        "Loading documents"
      );
    });

    it("does not show file card rows", () => {
      const fileCards = screen.queryAllByTestId("file-card");
      expect(fileCards).toHaveLength(0);
    });
  });

  describe("when there are no previously uploaded documents", () => {
    let appLogic;
    beforeEach(() => {
      render(
        <UploadDocumentWithAppLogic
          addAppLogicMocks={(_appLogic) => {
            appLogic = _appLogic;
            appLogic.documents.hasLoadedClaimDocuments = jest
              .fn()
              .mockImplementation(() => true);
            appLogic.portalFlow.goToNextPage = jest.fn();
          }}
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType: "state-id",
          }}
        />
      );
    });

    it("does not show file card rows", () => {
      const fileCards = screen.queryAllByTestId("file-card");
      expect(fileCards).toHaveLength(0);
    });

    it("shows error when saving without files", async () => {
      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));
      expect(appLogic.appErrors.items[0].message).toEqual(
        "Upload at least one file to continue."
      );
      expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
    });
  });

  describe("when there are previously loaded documents", () => {
    let appLogic;
    beforeEach(() => {
      render(
        <UploadDocumentWithAppLogic
          addAppLogicMocks={(_appLogic) => {
            appLogic = _appLogic;
            appLogic.documents.hasLoadedClaimDocuments = jest
              .fn()
              .mockImplementation(() => true);
            appLogic.documents.attach = jest.fn();
            appLogic.documents.documents = appLogic.documents.documents.addItem(
              new Document({
                application_id: "mock-claim-id",
                fineos_document_id: uuidv4(),
                document_type: DocumentType.identityVerification,
                created_at: "2021-09-01",
              })
            );
            appLogic.portalFlow.goToNextPage = jest.fn();
          }}
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType: "state-id",
          }}
        />
      );
    });

    it("renders unremovable FileCard", async () => {
      const fileCards = await screen.findAllByRole("heading", {
        level: 3,
        name: /File \d+/,
      });
      const unremovableFileCards = await screen.findAllByText(
        /You can’t remove files previously uploaded./
      );

      expect(fileCards).toHaveLength(1);
      expect(unremovableFileCards).toHaveLength(1);
    });

    it("navigates to checklist when saving without new files and does not make an API request", async () => {
      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      expect(appLogic.documents.attach).not.toHaveBeenCalled();
      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalled();
    });
  });

  describe("when user uploads files", () => {
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

    let appLogic;
    beforeEach(async () => {
      render(
        <UploadDocumentWithAppLogic
          addAppLogicMocks={(_appLogic) => {
            appLogic = _appLogic;
            appLogic.documents.hasLoadedClaimDocuments = jest
              .fn()
              .mockImplementation(() => true);

            appLogic.documents.attach = jest.fn().mockImplementation(() => {
              return [
                Promise.resolve({ success: true }),
                Promise.resolve({ success: true }),
              ];
            });

            appLogic.portalFlow.goToNextPage = jest.fn();
          }}
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType: "state-id",
          }}
        />
      );

      const chooseFilesButton = screen.getByLabelText(/Choose files/);
      await act(async () => {
        await userEvent.upload(chooseFilesButton, tempFiles);
      });
    });

    it("renders removable files", async () => {
      const files = await screen.findAllByText(/File \d+/);
      expect(files).toHaveLength(2);
    });

    it("makes API request when user clicks save and continue", async () => {
      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      expect(appLogic.documents.attach).toHaveBeenCalledWith(
        "mock-claim-id",
        expect.arrayContaining(expectedTempFiles),
        expect.any(String),
        true
      );

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledTimes(1);
    });

    it("displays unsuccessfully uploaded files as removable file cards", async () => {
      appLogic.documents.attach = jest.fn().mockImplementation(() => {
        return [
          Promise.resolve({ success: true }),
          Promise.resolve({ success: false }),
        ];
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => await userEvent.click(submitButton));

      const fileCards = await screen.findAllByText(/File \d+/);
      const unremovableFileCards = await screen.queryAllByText(
        /You can’t remove files previously uploaded./
      );
      expect(fileCards).toHaveLength(1);
      expect(unremovableFileCards).toHaveLength(0);
      expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
    });
  });

  it("renders alert when there is an error loading documents ", async () => {
    const { findByRole } = render(
      <UploadDocumentWithAppLogic
        addAppLogicMocks={(appLogic) => {
          appLogic.appErrors = new AppErrorInfoCollection([
            new AppErrorInfo({
              meta: { application_id: "mock-claim-id" },
              name: "DocumentsLoadError",
            }),
          ]);
        }}
        query={{
          claim_id: "mock-claim-id",
          absence_case_id: "mock-absence-case-id",
          documentType: "state-id",
        }}
      />
    );

    const alert = await findByRole("alert");
    expect(alert).toMatchInlineSnapshot(`
      <div
        class="usa-alert__body"
        role="alert"
      >
        <div
          class="usa-alert__text"
        >
          An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at (833) 344‑7365.
        </div>
      </div>
    `);
  });

  it("calls attach function with 'true' flag when there is additionalDoc flag in query", async () => {
    let appLogic;
    render(
      <UploadDocumentWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.documents.hasLoadedClaimDocuments = jest
            .fn()
            .mockImplementation(() => true);

          appLogic.documents.attach = jest.fn();

          appLogic.portalFlow.goToNextPage = jest.fn();
        }}
        query={{
          claim_id: "mock-claim-id",
          absence_case_id: "mock-absence-case-id",
          documentType: "state-id",
          additionalDoc: "true",
        }}
      />
    );

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => await userEvent.click(submitButton));

    expect(appLogic.documents.attach).toHaveBeenCalledWith(
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
  ];

  it.each(docTypes)(
    `uploads the "%s" document type for /applications/upload/%s`,
    async (documentType, documentTypeParam) => {
      let appLogic;
      render(
        <UploadDocumentWithAppLogic
          addAppLogicMocks={(_appLogic) => {
            appLogic = _appLogic;
            appLogic.documents.hasLoadedClaimDocuments = jest
              .fn()
              .mockImplementation(() => true);

            appLogic.documents.attach = jest.fn().mockImplementation(
              jest.fn(() => {
                return [
                  Promise.resolve({ success: true }),
                  Promise.resolve({ success: true }),
                ];
              })
            );
            appLogic.portalFlow.goToNextPage = jest.fn();
          }}
          query={{
            claim_id: "mock-claim-id",
            absence_case_id: "mock-absence-case-id",
            documentType: documentTypeParam,
            additionalDoc: "true",
          }}
        />
      );

      const chooseFilesButton = screen.getByLabelText(/Choose files/);
      await act(async () => {
        await userEvent.upload(chooseFilesButton, [
          makeFile({ name: "file1" }),
          makeFile({ name: "file2" }),
        ]);
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });
      await act(async () => {
        await userEvent.click(submitButton);
      });

      expect(appLogic.documents.attach).toHaveBeenCalledWith(
        "mock-claim-id",
        expect.any(Array),
        documentType,
        true
      );

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        { isAdditionalDoc: true },
        { claim_id: "mock-claim-id", absence_case_id: "mock-absence-case-id" }
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
