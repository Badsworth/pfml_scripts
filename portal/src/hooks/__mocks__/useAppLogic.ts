import User, { UserLeaveAdministrator } from "../../models/User";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import BenefitsApplication from "../../models/BenefitsApplication";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import ClaimCollection from "../../models/ClaimCollection";
import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import Flag from "../../models/Flag";
import PaginationMeta from "../../models/PaginationMeta";
import { uniqueId } from "lodash";

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export default jest.fn(() => ({
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  appErrors: new AppErrorInfoCollection(),
  auth: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    createAccount: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    createEmployerAccount: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    forgotPassword: jest.fn(),
    isLoggedIn: true,
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    login: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    logout: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    requireLogin: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    resendForgotPasswordCode: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    resendVerifyAccountCode: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    resetPassword: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    verifyAccount: jest.fn(),
  },
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  catchError: jest.fn(),
  benefitsApplications: {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    benefitsApplications: new BenefitsApplicationCollection(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    complete: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    create: jest.fn(
      () => new BenefitsApplication({ application_id: uniqueId() })
    ),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    get: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    hasLoadedBenefitsApplicationAndWarnings: jest.fn().mockReturnValue(true),
    hasLoadedAll: false,
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    load: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadAll: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    submit: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    submitPaymentPreference: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    update: jest.fn(),
    warningsLists: {},
  },
  claims: {
    activeFilters: {},
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    claims: new ClaimCollection(),
    isLoadingClaims: null,
    paginationMeta: new PaginationMeta(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadPage: jest.fn(),
  },
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  clearErrors: jest.fn(),
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  clearRequiredFieldErrors: jest.fn(),
  documents: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    attach: jest.fn((application_id, files, documentType) => {
      const uploadPromises = [];
      for (let i = 0; i < files.length; i++) {
        uploadPromises.push(Promise.resolve({ success: true }));
      }
      return uploadPromises;
    }),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    hasLoadedClaimDocuments: jest.fn(),
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    documents: new DocumentCollection(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadAll: jest.fn(),
  },
  employers: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    addEmployer: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    downloadDocument: jest.fn(() => new Blob()),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadClaim: jest.fn(
      () => new EmployerClaim({ fineos_absence_id: "NTN-111-ABS-01" })
    ),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadDocuments: jest.fn(() => new DocumentCollection()),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadWithholding: jest.fn(() => ({ filing_period: "2011-11-20" })),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    submitClaimReview: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    submitWithholding: jest.fn(),
  },
  portalFlow: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    getNextPageRoute: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    goTo: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    goToNextPage: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    goToPageFor: jest.fn(),
    pathname: "/mock-portalFlow-pathname",
  },
  otherLeaves: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    removeEmployerBenefit: jest.fn(() => true),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    removeOtherIncome: jest.fn(() => true),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    removePreviousLeave: jest.fn(() => true),
  },
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  setAppErrors: jest.fn(),
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  updateUser: jest.fn(),
  user: new User({ user_id: "mock_user_id", consented_to_data_sharing: true }),
  users: {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadUser: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    requireUserConsentToDataAgreement: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    requireUserRole: jest.fn(),
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
    loadFlags: jest.fn(),
  },
}));
