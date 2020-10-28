import Document from "../../../src/models/Document";
import DocumentCollection from "../../models/DocumentCollection";
import { uniqueId } from "xstate/lib/utils";

// Export mocked DocumentsApi functions so we can spy on them
// e.g.
// import { getDocumentsMock } from "./src/api/DocumentsApi";
// expect(getDocumentsMock).toHaveBeenCalled();
export const attachDocumentMock = jest.fn(
  (application_id, files = [], document_type) => {
    return Promise.resolve({
      success: true,
      status: 200,
      document: new Document({
        application_id,
        document_type,
        fineos_document_id: uniqueId(),
      }),
    });
  }
);

export const getDocumentsMock = jest.fn((application_id) => {
  return Promise.resolve({
    success: true,
    status: 200,
    documents: new DocumentCollection([
      new Document({ application_id, fineos_document_id: uniqueId() }),
      new Document({ application_id, fineos_document_id: uniqueId() }),
      new Document({ application_id, fineos_document_id: uniqueId() }),
    ]),
  });
});

export const downloadDocumentMock = jest.fn(() => {
  return new Blob();
});

const documentsApi = jest.fn().mockImplementation(() => ({
  attachDocument: attachDocumentMock,
  downloadDocument: downloadDocumentMock,
  getDocuments: getDocumentsMock,
}));

export default documentsApi;
