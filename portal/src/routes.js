/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Routes to various pages in the application are defined here rather than being
 * hard-coded into various files.
 */
const routes = {
  api: {
    claims: "/applications",
    users: "/users",
  },
  applications: "/applications",
  auth: {
    createAccount: "/create-account",
    forgotPassword: "/forgot-password",
    login: "/login",
    resetPassword: "/reset-password",
    verifyAccount: "/verify-account",
  },
  claims: {
    address: "/claims/address",
    averageWorkHours: "/claims/average-work-hours",
    checklist: "/claims/checklist",
    dashboard: "/",
    dateOfBirth: "/claims/date-of-birth",
    dateOfChild: "/claims/date-of-child",
    duration: "/claims/duration",
    employerBenefitDetails: "/claims/employer-benefit-details",
    employerBenefits: "/claims/employer-benefits",
    employmentStatus: "/claims/employment-status",
    leaveDates: "/claims/leave-dates",
    leavePeriodContinuous: "/claims/leave-period-continuous",
    leaveReason: "/claims/leave-reason",
    name: "/claims/name",
    notifiedEmployer: "/claims/notified-employer",
    otherIncomes: "/claims/other-incomes",
    otherIncomesDetails: "/claims/other-incomes-details",
    paymentMethod: "/claims/payment-method",
    previousLeaves: "/claims/previous-leaves",
    previousLeavesDetails: "/claims/previous-leaves-details",
    reasonPregnancy: "/claims/reason-pregnancy",
    review: "/claims/review",
    ssn: "/claims/ssn",
    start: "/claims/start",
    stateId: "/claims/state-id",
    success: "/claims/success",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.claims.todo,
    // which is less confusing than seeing routes.claims.checklist
    todo: "/claims/checklist",
    uploadCertification: "/claims/upload-certification",
    uploadId: "/claims/upload-id",
  },
  employers: {
    dashboard: "/employers",
    login: "/employers/login",
    review: "/employers/claims/review",
    success: "/employers/claims/success",
  },
  external: {
    massgov: {
      dfml: "https://mass.gov/dfml",
      healthcareProviderForm: "https://www.mass.gov/hcp-form",
      informedConsent: "https://www.mass.gov/paidleave-informedconsent",
      pfmlBenefitsGuide:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide",
      privacyPolicy: "https://www.mass.gov/privacypolicy",
    },
  },
  home: "/",
  user: {
    consentToDataSharing: "/user/consent-to-data-sharing",
  },
};

export default routes;
