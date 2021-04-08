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
  applications: {
    address: "/applications/address",
    bondingLeaveAttestation: "/applications/bonding-leave-attestation",
    caringLeaveAttestation: "/applications/caring-leave-attestation",
    checklist: "/applications/checklist",
    dashboard: "/dashboard",
    dateOfBirth: "/applications/date-of-birth",
    dateOfChild: "/applications/date-of-child",
    employerBenefits: "/applications/employer-benefits",
    employerBenefitsDetails: "/applications/employer-benefits-details",
    employmentStatus: "/applications/employment-status",
    familyMemberDateOfBirth: "/applications/family-member-date-of-birth",
    familyMemberName: "/applications/family-member-name",
    familyMemberRelationship: "/applications/family-member-relationship",
    getReady: "/applications/get-ready",
    index: "/applications",
    intermittentFrequency: "/applications/intermittent-frequency",
    leavePeriodContinuous: "/applications/leave-period-continuous",
    leavePeriodIntermittent: "/applications/leave-period-intermittent",
    leavePeriodReducedSchedule: "/applications/leave-period-reduced-schedule",
    leaveReason: "/applications/leave-reason",
    name: "/applications/name",
    notifiedEmployer: "/applications/notified-employer",
    otherIncomes: "/applications/other-incomes",
    otherIncomesDetails: "/applications/other-incomes-details",
    paymentMethod: "/applications/payment-method",
    phoneNumber: "/applications/phone-number",
    previousLeaves: "/applications/previous-leaves",
    previousLeavesDetails: "/applications/previous-leaves-details",
    reasonPregnancy: "/applications/reason-pregnancy",
    reducedLeaveSchedule: "/applications/reduced-leave-schedule",
    review: "/applications/review",
    scheduleFixed: "/applications/schedule-fixed",
    scheduleRotating: "/applications/schedule-rotating",
    scheduleRotatingNumberWeeks: "/applications/schedule-rotating-number-weeks",
    scheduleVariable: "/applications/schedule-variable",
    ssn: "/applications/ssn",
    start: "/applications/start",
    stateId: "/applications/state-id",
    success: "/applications/success",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.applications.todo,
    // which is less confusing than seeing routes.applications.checklist
    todo: "/applications/checklist",
    uploadCertification: "/applications/upload-certification",
    uploadDocsOptions: "/applications/upload-docs-options",
    uploadId: "/applications/upload-id",
    workPatternType: "/applications/work-pattern-type",
  },
  auth: {
    convert: "/convert-to-employer",
    createAccount: "/create-account",
    forgotPassword: "/forgot-password",
    login: "/login",
    resetPassword: "/reset-password",
    verifyAccount: "/verify-account",
  },
  employers: {
    addOrganization: "/employers/organizations/add-organization",
    cannotVerify: "/employers/organizations/cannot-verify",
    confirmation: "/employers/applications/confirmation",
    createAccount: "/employers/create-account",
    dashboard: "/employers/dashboard",
    finishAccountSetup: "/employers/finish-account-setup",
    newApplication: "/employers/applications/new-application",
    organizations: "/employers/organizations",
    review: "/employers/applications/review",
    status: "/employers/applications/status",
    success: "/employers/applications/success",
    verificationSuccess: "/employers/organizations/success",
    verifyContributions: "/employers/organizations/verify-contributions",
    welcome: "/employers/welcome",
  },
  external: {
    massTaxConnect: "https://mtc.dor.state.ma.us/mtc/_/",
    massgov: {
      benefitsGuide:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide",
      benefitsGuide_seriousHealthCondition:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide#what-is-a-serious-health-condition?-",
      benefitsTimeline_2020December2:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-timeline#december-2,-2020-",
      calculateHours: "https://www.mass.gov/pfml-calculate-hours",
      calculateReductions:
        "https://www.mass.gov/guides/what-to-expect-when-you-apply-for-paid-family-and-medical-leave-benefits#-calculate-any-reductions-",
      consentAgreement:
        "https://www.mass.gov/info-details/massachusetts-department-of-family-and-medical-leave-informed-consent-agreement",
      dfml: "https://www.mass.gov/orgs/department-of-family-and-medical-leave",
      dfmlRegulations:
        "https://www.mass.gov/regulations/458-CMR-200-department-of-family-and-medical-leave-1",
      emergencyBondingRegulationsEmployer:
        "https://www.mass.gov/pfml-acute-employer",
      emergencyBondingRegulationsWorker:
        "https://www.mass.gov/pfml-acute-claimant",
      employerAccount:
        "https://www.mass.gov/how-to/creating-an-employer-account-to-review-paid-family-and-medical-leave-pfml-applications",
      employerReimbursements:
        "https://www.mass.gov/forms/request-reimbursement-for-your-employees-paid-leave-benefits",
      employersGuide:
        "https://www.mass.gov/info-details/employer-paid-leave-application-review-guide",
      federalEmployerIdNumber:
        "https://www.mass.gov/info-details/finding-your-employers-federal-employer-identification-number-fein",
      feedbackClaimant: "https://www.mass.gov/paidleave-claimant-feedback",
      feedbackEmployer: "https://www.mass.gov/paidleave-employer-feedback",
      healthcareProviderForm: "https://www.mass.gov/hcp-form",
      howToApplyPaidLeave:
        "https://www.mass.gov/guides/what-is-paid-family-and-medical-leave#-how-can-i-apply-for-paid-leave-massachusetts-benefits",
      identityProof:
        "https://www.mass.gov/info-details/identity-proof-for-paid-leave",
      index:
        "https://www.mass.gov/topics/paid-family-and-medical-leave-in-massachusetts",
      informedConsent: "https://www.mass.gov/paidleave-informedconsent",
      intermittentLeaveGuide:
        "https://www.mass.gov/intermittent-leave-instructions",
      mailFaxInstructions: "https://www.mass.gov/pfmlsubmitinfo",
      medicalBonding: "https://www.mass.gov/pfml-medical-bonding",
      multipleBirths: "https://www.mass.gov/pfml-multiple-births",
      paidLeave:
        "https://www.mass.gov/topics/paid-family-and-medical-leave-in-massachusetts",
      preparingToVerifyEmployer:
        "https://www.mass.gov/info-details/preparing-to-verify-your-employer-paid-family-and-medical-leave-account",
      privacyPolicy: "https://www.mass.gov/privacypolicy",
      reductionsEmployerBenefits:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefit-reductions#earned-time-off-through-your-employer-",
      reductionsOverview:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefit-reductions",
      taxLiability: "https://www.mass.gov/pfml-tax-liability",
      verifyEmployer: "https://www.mass.gov/pfml-verify-employer",
      whatToExpect:
        "https://www.mass.gov/guides/what-to-expect-when-you-apply-for-paid-family-and-medical-leave-benefits",
      zeroBalanceEmployer: "https://www.mass.gov/pfml-zero-balance-employer",
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
export const isApplicationsRoute = (url) => {
  return Object.values(routes.applications).includes(getRouteFromUrl(url));
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
