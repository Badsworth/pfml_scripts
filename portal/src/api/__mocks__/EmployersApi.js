import Claim from "../../models/Claim";
import DocumentCollection from "../../models/DocumentCollection";
import { uniqueId } from "lodash";

// Export mocked EmployersApi functions so we can spy on them

export const getClaimMock = jest.fn().mockResolvedValue((absenceId) => {
  return {
    claim: new Claim({
      fineos_absence_id: absenceId,
    }),
    status: 200,
    success: true,
  };
});

export const getDocumentsMock = jest.fn().mockResolvedValue((absenceId) => {
  const application_id = absenceId;
  return {
    documents: new DocumentCollection([
      new Document({ application_id, fineos_document_id: uniqueId() }),
      new Document({ application_id, fineos_document_id: uniqueId() }),
      new Document({ application_id, fineos_document_id: uniqueId() }),
    ]),
    status: 200,
    success: true,
  };
});

export const downloadDocumentMock = jest.fn(() => new Blob());

export const submitClaimReviewMock = jest
  .fn()
  .mockResolvedValue((absenceId, patchData) => {
    return {
      claim: null,
      status: 200,
      success: true,
    };
  });

export const submitWithholdingMock = jest.fn().mockResolvedValue(() => {
  return {
    status: 200,
    success: true,
  };
});

const employersApi = jest.fn().mockImplementation(() => ({
  getClaim: getClaimMock,
  getDocuments: getDocumentsMock,
  downloadDocument: downloadDocumentMock,
  submitClaimReview: submitClaimReviewMock,
  submitWithholding: submitWithholdingMock,
}));

export default employersApi;
