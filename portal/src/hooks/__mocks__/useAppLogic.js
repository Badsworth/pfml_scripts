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
    forgotPassword: jest.fn(),
    isLoggedIn: true,
    login: jest.fn(),
    logout: jest.fn(),
    requireLogin: jest.fn(),
    resendVerifyAccountCode: jest.fn(),
    verifyAccount: jest.fn(),
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
    load: jest.fn(
      () => new EmployerClaim({ fineos_absence_id: "NTN-111-ABS-01" })
    ),
    submit: jest.fn(),
  },
  portalFlow: {
    goToNextPage: jest.fn(),
    goToPageFor: jest.fn(),
    pathname: "/mock-portalFlow-pathname",
  },
  setAppErrors: jest.fn(),
  updateUser: jest.fn(),
  user: new User({ user_id: "mock_user_id", consented_to_data_sharing: true }),
  users: {
    loadUser: jest.fn(),
    requireUserConsentToDataAgreement: jest.fn(),
    updateUser: jest.fn(),
    user: new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
    }),
  },
}));
