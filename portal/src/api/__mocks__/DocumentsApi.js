import Document from "../../../src/models/Document";
import DocumentCollection from "../../models/DocumentCollection";

// Export mocked DocumentsApi functions so we can spy on them
// e.g.
// import { getDocumentsMock } from "./src/api/DocumentsApi";
// expect(getDocumentsMock).toHaveBeenCalled();
export const attachDocumentsMock = jest.fn(
  (application_id, files = [], document_type) =>
    Promise.resolve({
      success: true,
      status: 200,
      document: new Document({
        application_id,
        document_type,
        fineos_document_id: 5,
      }),
    })
);

export const getDocumentsMock = jest.fn((application_id) => {
  return Promise.resolve({
    success: true,
    status: 200,
    documents: new DocumentCollection([
      new Document({ application_id, fineos_document_id: 1 }),
      new Document({ application_id, fineos_document_id: 2 }),
      new Document({ application_id, fineos_document_id: 3 }),
    ]),
  });
});

const documentsApi = jest.fn().mockImplementation(() => ({
  attachDocuments: attachDocumentsMock,
  getDocuments: getDocumentsMock,
}));

export default documentsApi;
