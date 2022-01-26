import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../models/Document";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import { uniqueId } from "xstate/lib/utils";

const documentData = {
  content_type: "",
  created_at: "2021-1-1",
  description: "",
  name: "mock doc",
  user_id: "mock-user-id",
  document_type: DocumentType.approvalNotice,
};

// Export mocked DocumentsApi functions so we can spy on them
// e.g.
// import { getDocumentsMock } from "./src/api/DocumentsApi";
// expect(getDocumentsMock).toHaveBeenCalled();
export const attachDocumentMock = jest.fn(
  (application_id, files, document_type) => {
    return Promise.resolve({
      success: true,
      status: 200,
      document: {
        ...documentData,
        application_id,
        document_type,
        fineos_document_id: uniqueId(),
      },
    });
  }
);

export const getDocumentsMock = jest.fn((application_id) => {
  return Promise.resolve({
    success: true,
    status: 200,
    documents: new ApiResourceCollection<BenefitsApplicationDocument>(
      "fineos_document_id",
      [
        {
          ...documentData,
          application_id,
          fineos_document_id: uniqueId(),
        },
        {
          ...documentData,
          application_id,
          fineos_document_id: uniqueId(),
        },
        {
          ...documentData,
          application_id,
          fineos_document_id: uniqueId(),
        },
      ]
    ),
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
