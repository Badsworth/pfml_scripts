import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Claim from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import User from "../../models/User";
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
    verifyEmployerAccount: jest.fn(),
  },
  catchError: jest.fn(),
  claims: {
    claims: new ClaimCollection(),
    complete: jest.fn(),
    create: jest.fn(() => new Claim({ application_id: uniqueId() })),
    get: jest.fn(),
    hasLoadedClaimAndWarnings: jest.fn().mockReturnValue(true),
    hasLoadedAll: false,
    load: jest.fn(),
    loadAll: jest.fn(),
    submit: jest.fn(),
    submitPaymentPreference: jest.fn(),
    update: jest.fn(),
    warningsLists: {},
  },
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
    downloadDocument: jest.fn(() => new Blob()),
    loadClaim: jest.fn(
      () => new EmployerClaim({ fineos_absence_id: "NTN-111-ABS-01" })
    ),
    loadDocuments: jest.fn(() => new DocumentCollection()),
    submit: jest.fn(),
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
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
    }),
  },
}));
