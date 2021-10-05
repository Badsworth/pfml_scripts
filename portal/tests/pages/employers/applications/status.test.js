import Document, { DocumentType } from "../../../../src/models/Document";
import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AbsenceCaseStatus } from "../../../../src/models/Claim";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import Status from "../../../../src/pages/employers/applications/status";
import userEvent from "@testing-library/user-event";

function setup(models = {}) {
  const spys = {};
  const { claim, documents } = {
    claim: new MockEmployerClaimBuilder()
      .status(AbsenceCaseStatus.approved)
      .completed()
      .create(),
    documents: new DocumentCollection([
      new Document({
        content_type: "application/pdf",
        created_at: "2021-01-02",
        document_type: DocumentType.approvalNotice,
        fineos_document_id: "fineos-id-1",
        name: "Approval.pdf",
      }),
    ]),
    ...models,
  };

  const utils = renderPage(
    Status,
    {
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = claim;
        appLogic.employers.documents = documents;
        spys.loadDocumentsSpy = jest
          .spyOn(appLogic.employers, "loadDocuments")
          .mockResolvedValue();
        spys.downloadDocumentSpy = jest
          .spyOn(appLogic.employers, "downloadDocument")
          .mockResolvedValue();
      },
    },
    {
      query: { absence_id: "NTN-111-ABS-01" },
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
      documents: null,
      claim: new MockEmployerClaimBuilder().completed().create(),
    });

    expect(
      screen.getByText(/No action is required of you/i)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("does not show intermittent leave dates", () => {
    setup({
      claim: new MockEmployerClaimBuilder()
        .completed()
        .intermittent({
          start_date: "2019-01-30",
        })
        .create(),
    });

    expect(screen.queryByText(/intermittent/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/2019/)).not.toBeInTheDocument();
  });

  it("loads the documents when they're not yet loaded", async () => {
    const { loadDocumentsSpy } = setup({
      documents: null,
    });

    await waitFor(() => {
      expect(loadDocumentsSpy).toHaveBeenCalled();
    });
  });

  it("shows only legal documents", () => {
    // Generate a list of documents of every possible type
    const documents = [];
    function addDocument(document_type) {
      const num = (documents.length + 1).toString().padStart(2, "0");

      documents.push(
        new Document({
          document_type,
          content_type: "application/pdf",
          created_at: `2021-01-${num}`,
          fineos_document_id: `fineos-id-${num}`,
        })
      );
    }

    Object.values(DocumentType).forEach((documentType) => {
      if (typeof documentType === "string") return addDocument(documentType);
      if (typeof documentType === "object") {
        Object.values(documentType).forEach((documentSubType) =>
          addDocument(documentSubType)
        );
      }
    });

    setup({ documents: new DocumentCollection(documents) });

    expect(screen.getByTestId("documents")).toMatchSnapshot();
  });

  it("download documents on click", () => {
    const document = new Document({
      content_type: "application/pdf",
      created_at: "2021-01-02",
      document_type: DocumentType.approvalNotice,
      fineos_document_id: "fineos-id-1",
      name: "Approval.pdf",
    });

    const { downloadDocumentSpy } = setup({
      documents: new DocumentCollection([document]),
    });

    userEvent.click(screen.getByRole("button", { name: /approval/i }));

    expect(downloadDocumentSpy).toHaveBeenCalledWith(
      "NTN-111-ABS-01",
      document
    );
  });
});
