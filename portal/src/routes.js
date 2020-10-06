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
    checklist: "/claims/checklist",
    dashboard: "/",
    dateOfBirth: "/claims/date-of-birth",
    dateOfChild: "/claims/date-of-child",
    employerBenefitDetails: "/claims/employer-benefit-details",
    employerBenefits: "/claims/employer-benefits",
    employmentStatus: "/claims/employment-status",
    hoursWorkedPerWeek: "/claims/hours-worked-per-week",
    intermittentFrequency: "/claims/intermittent-frequency",
    leavePeriodContinuous: "/claims/leave-period-continuous",
    leavePeriodIntermittent: "/claims/leave-period-intermittent",
    leavePeriodReducedSchedule: "/claims/leave-period-reduced-schedule",
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
      identityProof:
        "https://www.mass.gov/info-details/identity-proof-for-paid-leave",
      informedConsent: "https://www.mass.gov/paidleave-informedconsent",
      pfmlBenefitsGuide:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide",
      privacyPolicy: "https://www.mass.gov/privacypolicy",
      userFeedback: "https://www.mass.gov", // TODO (EMPLOYER-417): Update link to external survey
    },
    puertoRicanBirthCertificate: "https://prfaa.pr.gov/faqs",
    workVisa:
      "https://travel.state.gov/content/travel/en/us-visas/employment/temporary-worker-visas.html",
  },
  home: "/",
  user: {
    consentToDataSharing: "/user/consent-to-data-sharing",
  },
};

export default routes;
