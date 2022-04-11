import { ClaimDocument, DocumentType } from "../../models/Document";
import User, { UserLeaveAdministrator } from "../../models/User";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import EmployerClaimReview from "../../models/EmployerClaimReview";
import { faker } from "@faker-js/faker";
import { uniqueId } from "lodash";

const documentData = {
  content_type: "",
  created_at: "2021-1-1",
  description: "",
  name: "mock doc",
  document_type: DocumentType.approvalNotice,
};

// Export mocked EmployersApi functions so we can spy on them
export const addEmployerMock = jest.fn().mockResolvedValue({
  data: new UserLeaveAdministrator({}),
});

export const getClaimMock = jest.fn().mockResolvedValue((absenceId: string) => {
  return {
    claim: new EmployerClaimReview({
      absence_periods: [],
      fineos_absence_id: absenceId,
    }),
  };
});

export const getDocumentsMock = jest.fn().mockResolvedValue({
  documents: new ApiResourceCollection<ClaimDocument>("fineos_document_id", [
    { ...documentData, fineos_document_id: uniqueId() },
    { ...documentData, fineos_document_id: uniqueId() },
    { ...documentData, fineos_document_id: uniqueId() },
  ]),
});

export const getWithholdingMock = jest.fn().mockResolvedValue({
  filing_period: "2011-11-20",
});

export const downloadDocumentMock = jest.fn(() => new Blob());

export const submitClaimReviewMock = jest.fn().mockResolvedValue({
  claim: null,
});

export const submitWithholdingMock = jest.fn().mockResolvedValue({
  user: new User({
    user_leave_administrators: [
      {
        employer_dba: faker.company.companyName(),
        employer_fein: "12-3456789",
        employer_id: uniqueId(),
        has_fineos_registration: true,
        has_verification_data: true,
        verified: true,
      },
    ],
  }),
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
