import {
  ClaimDocument,
  DocumentType,
  DocumentTypeEnum,
} from "../../../../src/models/Document";
import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AbsenceCaseStatus } from "../../../../src/models/Claim";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import Status from "../../../../src/pages/employers/applications/status";
import { faker } from "@faker-js/faker";
import routes from "../../../../src/routes";
import userEvent from "@testing-library/user-event";

function setup(models = {}) {
  let loadDocumentsSpy!: jest.SpyInstance;
  let downloadDocumentSpy!: jest.SpyInstance;
  let goToPageForSpy!: jest.SpyInstance;

  const absence_id = "NTN-111-ABS-01";
  const newClaim = new MockEmployerClaimBuilder()
    .status(AbsenceCaseStatus.approved)
    .completed()
    .absenceId(absence_id)
    .create();
  const { claim, claimDocumentsMap } = {
    claim: newClaim,
    claimDocumentsMap: new Map([
      [
        absence_id,
        new ApiResourceCollection<ClaimDocument>("fineos_document_id", [
          {
            content_type: "application/pdf",
            created_at: "2021-01-02",
            description: "",
            document_type: DocumentType.approvalNotice,
            fineos_document_id: "fineos-id-1",
            name: "Approval.pdf",
          },
        ]),
      ],
    ]),
    ...models,
  };

  const utils = renderPage(
    Status,
    {
      pathname: routes.employers.status,
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = claim;
        appLogic.employers.claimDocumentsMap = claimDocumentsMap;
        loadDocumentsSpy = jest
          .spyOn(appLogic.employers, "loadDocuments")
          .mockResolvedValue();
        downloadDocumentSpy = jest
          .spyOn(appLogic.employers, "downloadDocument")
          .mockResolvedValue(new Blob());
        goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");
      },
    },
    {
      query: { absence_id },
    }
  );

  return { loadDocumentsSpy, downloadDocumentSpy, goToPageForSpy, ...utils };
}

describe("Status", () => {
  it("redirects reviewable claims", () => {
    const claim = new MockEmployerClaimBuilder().reviewable().create();
    const { goToPageForSpy } = setup({
      claim,
    });

    expect(goToPageForSpy).toHaveBeenCalledWith(
      "REDIRECT_REVIEWABLE_CLAIM",
      {},
      { absence_id: claim.fineos_absence_id },
      { redirect: true }
    );
  });

  it("renders the page for a completed claim", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("renders the page for a claim without documents or a status", () => {
    const { container } = setup({
      claimDocumentsMap: new Map(),
      claim: new MockEmployerClaimBuilder().completed().create(),
    });

    expect(
      screen.getByText(/No action is required of you/i)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("shows intermittent leave dates", () => {
    setup({
      claim: new MockEmployerClaimBuilder().completed(true).create(),
    });

    expect(screen.queryByText(/intermittent/i)).toBeInTheDocument();
    expect(screen.queryAllByText(/2022/).length).toBe(2);
  });

  it("loads the documents when they're not yet loaded", async () => {
    const { loadDocumentsSpy } = setup({
      claimDocumentsMap: new Map(),
    });

    await waitFor(() => {
      expect(loadDocumentsSpy).toHaveBeenCalled();
    });
  });

  it("shows only legal documents", () => {
    // Generate a list of documents of every possible type
    const documents: ClaimDocument[] = [];
    function addDocument(document_type: DocumentTypeEnum) {
      const num = (documents.length + 1).toString().padStart(2, "0");

      documents.push({
        document_type,
        content_type: "application/pdf",
        created_at: `2021-01-${num}`,
        fineos_document_id: `fineos-id-${num}`,
        description: "",
        name: "",
      });
    }

    Object.values(DocumentType).forEach((documentType) => {
      if (typeof documentType === "string") return addDocument(documentType);
      if (typeof documentType === "object") {
        Object.values(documentType).forEach((documentSubType) =>
          addDocument(documentSubType)
        );
      }
    });
    const newMap = new Map([
      [
        "NTN-111-ABS-01",
        new ApiResourceCollection<ClaimDocument>(
          "fineos_document_id",
          documents
        ),
      ],
    ]);

    setup({ claimDocumentsMap: newMap });
    expect(screen.getByTestId("documents")).toMatchSnapshot();
  });

  it("download documents on click", () => {
    const document = {
      content_type: "application/pdf",
      created_at: "2021-01-02",
      description: "",
      document_type: DocumentType.approvalNotice,
      fineos_document_id: "fineos-id-1",
      name: "Approval.pdf",
    };
    const absence_id = "NTN-111-ABS-01";

    const { downloadDocumentSpy } = setup({
      claimDocumentsMap: new Map([
        [
          absence_id,
          new ApiResourceCollection<ClaimDocument>("fineos_document_id", [
            document,
          ]),
        ],
      ]),
    });

    userEvent.click(screen.getByRole("button", { name: /approval/i }));

    expect(downloadDocumentSpy).toHaveBeenCalledWith(document, absence_id);
  });

  it("renders employee information section when new format is enabled", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    setup();
    expect(
      screen.getByRole("heading", { name: "Employee information" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Amend" })
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("Application ID: NTN-111-ABS-01")
    ).toBeInTheDocument();
  });

  it("renders updated Leave Details section when new format is enabled", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    const documents = [
      {
        content_type: "application/pdf",
        created_at: "2021-01-01",
        description: "",
        document_type: DocumentType.certification.medicalCertification,
        fineos_document_id: faker.datatype.uuid(),
        name: "",
      },
      {
        content_type: "image/jpeg",
        created_at: "2021-02-15",
        description: "",
        document_type: DocumentType.certification.medicalCertification,
        fineos_document_id: faker.datatype.uuid(),
        name: "",
      },
    ];
    const newMap = new Map([
      [
        "NTN-111-ABS-01",
        new ApiResourceCollection<ClaimDocument>(
          "fineos_document_id",
          documents
        ),
      ],
    ]);
    setup({ claimDocumentsMap: newMap });
    expect(screen.getByText("Documentation")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Medical leave" })
    ).toBeInTheDocument();
    expect(screen.getByTestId("absence periods")).toBeInTheDocument();
  });
});
