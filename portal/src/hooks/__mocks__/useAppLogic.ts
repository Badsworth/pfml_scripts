import {
  BenefitsApplicationDocument,
  ClaimDocument,
} from "../../models/Document";
import User, { UserLeaveAdministrator } from "../../models/User";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import BenefitsApplication from "../../models/BenefitsApplication";
import Claim from "../../models/Claim";
import ClaimDetail from "../../models/ClaimDetail";
import EmployerClaim from "../../models/EmployerClaim";
import Flag from "../../models/Flag";
import { Payment } from "src/models/Payment";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  errors: [],
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
    resetPassword: jest.fn(),
    verifyAccount: jest.fn(),
  },
  catchError: jest.fn(),
  benefitsApplications: {
    benefitsApplications: new ApiResourceCollection<BenefitsApplication>(
      "application_id"
    ),
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
    claimDetail: new ClaimDetail(),
    claims: new ApiResourceCollection<Claim>("fineos_absence_id"),
    clearClaims: jest.fn(),
    isLoadingClaims: null,
    isLoadingClaimDetail: null,
    loadClaimDetail: jest.fn(),
    paginationMeta: {},
    loadPage: jest.fn(),
  },
  clearErrors: jest.fn(),
  clearRequiredFieldErrors: jest.fn(),
  documents: {
    attach: jest.fn((application_id, files) => {
      const uploadPromises: Array<Promise<{ success: boolean }>> = [];
      for (let i = 0; i < files.length; i++) {
        uploadPromises.push(Promise.resolve({ success: true }));
      }
      return uploadPromises;
    }),
    hasLoadedClaimDocuments: jest.fn(),
    documents: new ApiResourceCollection<BenefitsApplicationDocument>(
      "fineos_document_id"
    ),
    download: jest.fn(),
    loadAll: jest.fn(),
  },
  employers: {
    addEmployer: jest.fn(),
    downloadDocument: jest.fn(() => new Blob()),
    loadClaim: jest.fn(
      () =>
        new EmployerClaim({
          absence_periods: [],
          fineos_absence_id: "NTN-111-ABS-01",
        })
    ),
    loadDocuments: jest.fn(
      () => new ApiResourceCollection<ClaimDocument>("fineos_document_id")
    ),
    loadWithholding: jest.fn(() => ({ filing_period: "2011-11-20" })),
    submitClaimReview: jest.fn(),
    submitWithholding: jest.fn(),
  },
  payments: {
    loadPayments: jest.fn(),
    loadedPaymentsData: new Payment(),
    hasLoadedPayments: true,
    isLoadingPayments: false,
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
  setErrors: jest.fn(),
  updateUser: jest.fn(),
  user: new User({
    user_id: "mock_user_id",
    consented_to_data_sharing: true,
    email_address: "ali@miau.com",
    auth_id: "cognito_123",
    roles: [],
    user_leave_administrators: [],
  }),
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
  featureFlags: {
    flags: [
      new Flag({
        enabled: false,
        name: "maintenance",
        options: {
          page_routes: ["/*"],
        },
        start: null,
        end: null,
      }),
    ],
    getFlag: jest.fn(() => {
      return new Flag({
        enabled: false,
        name: "maintenance",
        options: {
          page_routes: ["/*"],
        },
        start: null,
        end: null,
      });
    }),
    loadFlags: jest.fn(),
  },
}));
