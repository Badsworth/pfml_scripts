import User, { UserLeaveAdministrator } from "../../models/User";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import BenefitsApplication from "../../models/BenefitsApplication";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import ClaimCollection from "../../models/ClaimCollection";
import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import PaginationMeta from "../../models/PaginationMeta";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  appErrors: new AppErrorInfoCollection(),
  auth: {
    createAccount: jest.fn(),
    createEmployerAccount: jest.fn(),
    forgotPassword: jest.fn(),
    isLoggedIn: true,
    login: jest.fn(),
    logout: jest.fn(),
    requireLogin: jest.fn(),
    resendForgotPasswordCode: jest.fn(),
    resendVerifyAccountCode: jest.fn(),
    resetEmployerPasswordAndCreateEmployerApiAccount: jest.fn(),
    resetPassword: jest.fn(),
    verifyAccount: jest.fn(),
  },
  catchError: jest.fn(),
  benefitsApplications: {
    benefitsApplications: new BenefitsApplicationCollection(),
    complete: jest.fn(),
    create: jest.fn(
      () => new BenefitsApplication({ application_id: uniqueId() })
    ),
    get: jest.fn(),
    hasLoadedBenefitsApplicationAndWarnings: jest.fn().mockReturnValue(true),
    hasLoadedAll: false,
    load: jest.fn(),
    loadAll: jest.fn(),
    submit: jest.fn(),
    submitPaymentPreference: jest.fn(),
    update: jest.fn(),
    warningsLists: {},
  },
  claims: {
    claims: new ClaimCollection(),
    paginationMeta: new PaginationMeta(),
    loadPage: jest.fn(),
  },
  clearErrors: jest.fn(),
  documents: {
    attach: jest.fn((application_id, files, documentType) => {
      const uploadPromises = [];
      for (let i = 0; i < files.length; i++) {
        uploadPromises.push(Promise.resolve({ success: true }));
      }
      return uploadPromises;
    }),
    hasLoadedClaimDocuments: jest.fn(),
    documents: new DocumentCollection(),
    loadAll: jest.fn(),
  },
  employers: {
    addEmployer: jest.fn(),
    downloadDocument: jest.fn(() => new Blob()),
    loadClaim: jest.fn(
      () => new EmployerClaim({ fineos_absence_id: "NTN-111-ABS-01" })
    ),
    loadDocuments: jest.fn(() => new DocumentCollection()),
    loadWithholding: jest.fn(() => ({ filing_period: "2011-11-20" })),
    submitClaimReview: jest.fn(),
    submitWithholding: jest.fn(),
  },
  portalFlow: {
    getNextPageRoute: jest.fn(),
    goTo: jest.fn(),
    goToNextPage: jest.fn(),
    goToPageFor: jest.fn(),
    pathname: "/mock-portalFlow-pathname",
  },
  otherLeaves: {
    removeEmployerBenefit: jest.fn(() => true),
    removeOtherIncome: jest.fn(() => true),
    removePreviousLeave: jest.fn(() => true),
  },
  setAppErrors: jest.fn(),
  updateUser: jest.fn(),
  user: new User({ user_id: "mock_user_id", consented_to_data_sharing: true }),
  users: {
    loadUser: jest.fn(),
    requireUserConsentToDataAgreement: jest.fn(),
    requireUserRole: jest.fn(),
    updateUser: jest.fn(),
    user: new User({
      auth_id: "mock_auth_id",
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      user_leave_administrators: [
        // not verified, but can be
        new UserLeaveAdministrator({
          employer_dba: "Book Bindings 'R Us",
          employer_fein: "**-***1823",
          employer_id: "dda903f-f093f-ff900",
          has_fineos_registration: true,
          has_verification_data: true,
          verified: false,
        }),
        // already verified
        new UserLeaveAdministrator({
          employer_dba: "Knitting Castle",
          employer_fein: "**-***3443",
          employer_id: "dda930f-93jfk-iej08",
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        // not verified and cannot be verified
        new UserLeaveAdministrator({
          employer_dba: "Tomato Touchdown",
          employer_fein: "**-***7192",
          employer_id: "io19fj9-00jjf-uiw3r",
          has_fineos_registration: true,
          has_verification_data: false,
          verified: false,
        }),
      ],
    }),
  },
}));
