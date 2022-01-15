import {
  ClaimDocument,
  DocumentType,
  DocumentTypeEnum,
} from "../../../../src/models/Document";
import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AbsenceCaseStatus } from "../../../../src/models/Claim";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import Status from "../../../../src/pages/employers/applications/status";
import userEvent from "@testing-library/user-event";

function setup(models = {}) {
  const spys: {
    loadDocumentsSpy?: jest.SpyInstance;
    downloadDocumentSpy?: jest.SpyInstance;
  } = {};
  const absence_id = "NTN-111-ABS-01";
  const { claim, claimDocumentsMap } = {
    claim: new MockEmployerClaimBuilder()
      .status(AbsenceCaseStatus.approved)
      .completed()
      .absenceId(absence_id)
      .create(),
    claimDocumentsMap: new Map([
      [
        absence_id,
        new DocumentCollection([
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
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = claim;
        appLogic.employers.claimDocumentsMap = claimDocumentsMap;
        spys.loadDocumentsSpy = jest
          .spyOn(appLogic.employers, "loadDocuments")
          .mockResolvedValue();
        spys.downloadDocumentSpy = jest
          .spyOn(appLogic.employers, "downloadDocument")
          .mockResolvedValue(new Blob());
      },
    },
    {
      query: { absence_id },
    }
  );

  return { ...spys, ...utils };
}

describe("Status", () => {
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
      claim: new MockEmployerClaimBuilder()
        .completed()
        .intermittent({
          start_date: "2019-01-30",
        })
        .create(),
    });

    expect(screen.queryByText(/intermittent/i)).toBeInTheDocument();
    expect(screen.queryAllByText(/2019/).length).toBe(2);
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
      ["NTN-111-ABS-01", new DocumentCollection(documents)],
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
        [absence_id, new DocumentCollection([document])],
      ]),
    });

    userEvent.click(screen.getByRole("button", { name: /approval/i }));

    expect(downloadDocumentSpy).toHaveBeenCalledWith(document, absence_id);
  });
});
