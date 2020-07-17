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
    checklist: "/claims/checklist",
    confirm: "/claims/confirm",
    dashboard: "/",
    dateOfBirth: "/claims/date-of-birth",
    duration: "/claims/duration",
    employerBenefitDetails: "/claims/employer-benefit-details",
    employerBenefits: "/claims/employer-benefits",
    employmentStatus: "/claims/employment-status",
    leaveDates: "/claims/leave-dates",
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
    stateId: "/claims/state-id",
    success: "/claims/success",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.claims.todo,
    // which is less confusing than seeing routes.claims.checklist
    todo: "/claims/checklist",
    uploadHealthcareForm: "/claims/upload-healthcare-form",
    uploadOtherId: "/claims/upload-other-id",
    uploadStateId: "/claims/upload-state-id",
  },
  external: {
    massInformedConsent: "https://www.mass.gov/paidleave-informedconsent",
    massPrivacyPolicy: "https://www.mass.gov/privacypolicy",
  },
  home: "/",
  user: {
    consentToDataSharing: "/user/consent-to-data-sharing",
  },
};

export default routes;
