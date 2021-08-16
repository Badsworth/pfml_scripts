import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import { UserLeaveAdministrator } from "../../models/User";
import Withholding from "../../models/Withholding";
import { uniqueId } from "lodash";

// Export mocked EmployersApi functions so we can spy on them

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const addEmployerMock = jest.fn().mockResolvedValue(() => {
  return {
    data: new UserLeaveAdministrator({}),
    status: 200,
    success: true,
  };
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const getClaimMock = jest.fn().mockResolvedValue((absenceId) => {
  return {
    claim: new EmployerClaim({
      fineos_absence_id: absenceId,
    }),
    status: 200,
    success: true,
  };
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const getDocumentsMock = jest.fn().mockResolvedValue((absenceId) => {
  const application_id = absenceId;
  return {
    documents: new DocumentCollection([
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
      new Document({ application_id, fineos_document_id: uniqueId() }),
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
      new Document({ application_id, fineos_document_id: uniqueId() }),
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
      new Document({ application_id, fineos_document_id: uniqueId() }),
    ]),
    status: 200,
    success: true,
  };
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const getWithholdingMock = jest.fn().mockResolvedValue(() => {
  return new Withholding({
    filing_period: "2011-11-20",
  });
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const downloadDocumentMock = jest.fn(() => new Blob());

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const submitClaimReviewMock = jest
  .fn()
  .mockResolvedValue((absenceId, patchData) => {
    return {
      claim: null,
      status: 200,
      success: true,
    };
  });

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const submitWithholdingMock = jest.fn().mockResolvedValue(() => {
  return {
    status: 200,
    success: true,
  };
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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
