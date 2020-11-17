/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Routes to various pages in the application are defined here rather than being
 * hard-coded into various files.
 */
const routes = {
  api: {
    claims: "/applications",
    employers: "/employers",
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
    bondingLeaveAttestation: "/claims/bonding-leave-attestation",
    checklist: "/claims/checklist",
    dashboard: "/dashboard",
    dateOfBirth: "/claims/date-of-birth",
    dateOfChild: "/claims/date-of-child",
    employerBenefitDetails: "/claims/employer-benefit-details",
    employerBenefits: "/claims/employer-benefits",
    employmentStatus: "/claims/employment-status",
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
    reducedLeaveSchedule: "/claims/reduced-leave-schedule",
    review: "/claims/review",
    scheduleFixed: "/claims/schedule-fixed",
    scheduleRotating: "/claims/schedule-rotating",
    scheduleRotatingNumberWeeks: "/claims/schedule-rotating-number-weeks",
    scheduleVariable: "/claims/schedule-variable",
    ssn: "/claims/ssn",
    start: "/claims/start",
    stateId: "/claims/state-id",
    success: "/claims/success",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.claims.todo,
    // which is less confusing than seeing routes.claims.checklist
    todo: "/claims/checklist",
    uploadCertification: "/claims/upload-certification",
    uploadDocsOptions: "/claims/upload-docs-options",
    uploadId: "/claims/upload-id",
    workPatternType: "/claims/work-pattern-type",
  },
  employers: {
    confirmation: "/employers/claims/confirmation",
    createAccount: "/employers/create-account",
    dashboard: "/employers",
    finishAccountSetup: "/employers/finish-account-setup",
    newApplication: "/employers/claims/new-application",
    review: "/employers/claims/review",
    status: "/employers/claims/status",
    success: "/employers/claims/success",
  },
  external: {
    massgov: {
      benefitsGuide:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide",
      benefitsGuide_seriousHealthCondition:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide#what-is-a-serious-health-condition?-",
      benefitsTimeline_2020December2:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-timeline#december-2,-2020-",
      consentAgreement:
        "https://www.mass.gov/info-details/massachusetts-department-of-family-and-medical-leave-informed-consent-agreement",
      dfml: "https://mass.gov/dfml",
      employersGuide:
        "https://www.mass.gov/guides/employers-guide-to-paid-family-and-medical-leave",
      federalEmployerIdNumber:
        "https://www.mass.gov/info-details/finding-your-employers-federal-employer-identification-number-fein",
      healthcareProviderForm: "https://www.mass.gov/hcp-form",
      identityProof:
        "https://www.mass.gov/info-details/identity-proof-for-paid-leave",
      informedConsent: "https://www.mass.gov/paidleave-informedconsent",
      mailFaxInstructions: "https://www.mass.gov/pfmlsubmitinfo",
      paidLeave:
        "https://www.mass.gov/topics/paid-family-and-medical-leave-in-massachusetts",
      privacyPolicy: "https://www.mass.gov/privacypolicy",
      userFeedback: "https://www.mass.gov/paidleave-employer-feedback",
    },
    puertoRicanBirthCertificate: "https://prfaa.pr.gov/faqs",
    workVisa:
      "https://travel.state.gov/content/travel/en/us-visas/employment/temporary-worker-visas.html",
  },
  index: "/",
  user: {
    consentToDataSharing: "/user/consent-to-data-sharing",
  },
};

/**
 * @param {string} url - path, with or without query param
 * @returns {boolean}
 */
export const isEmployersRoute = (url) => {
  return Object.values(routes.employers).includes(getRouteFromUrl(url));
};

/**
 * @param {string} url - path, with or without query param
 * @returns {boolean}
 */
export const isClaimsRoute = (url) => {
  return Object.values(routes.claims).includes(getRouteFromUrl(url));
};

/**
 * @param {string} url - path, with or without query param
 * @returns {string}
 */
const getRouteFromUrl = (url) => {
  let route = url;
  const queryStringIndex = route.indexOf("?");

  if (queryStringIndex !== -1) {
    route = route.substring(0, queryStringIndex);
  }

  if (route.endsWith("/")) {
    route = route.substring(0, route.length - 1);
  }

  return route;
};

export default routes;
