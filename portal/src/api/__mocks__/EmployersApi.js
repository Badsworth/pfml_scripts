import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import { UserLeaveAdministrator } from "../../models/User";
import Withholding from "../../models/Withholding";
import { uniqueId } from "lodash";

// Export mocked EmployersApi functions so we can spy on them

export const addEmployerMock = jest.fn().mockResolvedValue(() => {
  return {
    data: new UserLeaveAdministrator({}),
    status: 200,
    success: true,
  };
});

export const getClaimMock = jest.fn().mockResolvedValue((absenceId) => {
  return {
    claim: new EmployerClaim({
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

export const getWithholdingMock = jest.fn().mockResolvedValue(() => {
  return new Withholding({
    filing_period: "2011-11-20",
  });
});

export const downloadDocumentMock = jest.fn(() => new Blob());

export const submitClaimReviewMock = jest.fn().mockResolvedValue(() => {
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
  addEmployer: addEmployerMock,
  getClaim: getClaimMock,
  getDocuments: getDocumentsMock,
  getWithholding: getWithholdingMock,
  downloadDocument: downloadDocumentMock,
  submitClaimReview: submitClaimReviewMock,
  submitWithholding: submitWithholdingMock,
}));

export default employersApi;
