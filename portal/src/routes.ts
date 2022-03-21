/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Routes to various pages in the application are defined here rather than being
 * hard-coded into various files.
 */
const routes = {
  api: {
    applicationImports: "/application-imports",
    applications: "/applications",
    benefitYears: "/benefit-years",
    claims: "/claims",
    employers: "/employers",
    holidays: "/holidays",
    payments: "/payments",
    roles: "/roles",
    users: "/users",
  },
  applications: {
    address: "/applications/address",
    bondingLeaveAttestation: "/applications/bonding-leave-attestation",
    caringLeaveAttestation: "/applications/caring-leave-attestation",
    checklist: "/applications/checklist",
    concurrentLeaves: "/applications/concurrent-leaves",
    concurrentLeavesDetails: "/applications/concurrent-leaves-details",
    concurrentLeavesIntro: "/applications/concurrent-leaves-intro",
    dateOfBirth: "/applications/date-of-birth",
    dateOfChild: "/applications/date-of-child",
    department: "/applications/department",
    employerBenefits: "/applications/employer-benefits",
    employerBenefitsDetails: "/applications/employer-benefits-details",
    employerBenefitsIntro: "/applications/employer-benefits-intro",
    employmentStatus: "/applications/employment-status",
    familyMemberDateOfBirth: "/applications/family-member-date-of-birth",
    familyMemberName: "/applications/family-member-name",
    familyMemberRelationship: "/applications/family-member-relationship",
    gender: "/applications/gender",
    getReady: "/applications/get-ready",
    importClaim: "/applications/import-claim",
    index: "/applications",
    intermittentFrequency: "/applications/intermittent-frequency",
    leavePeriodContinuous: "/applications/leave-period-continuous",
    leavePeriodIntermittent: "/applications/leave-period-intermittent",
    leavePeriodReducedSchedule: "/applications/leave-period-reduced-schedule",
    leaveReason: "/applications/leave-reason",
    missingEeErMatch: "/applications/no-employee-employer-match",
    name: "/applications/name",
    notifiedEmployer: "/applications/notified-employer",
    otherIncomes: "/applications/other-incomes",
    otherIncomesDetails: "/applications/other-incomes-details",
    paymentMethod: "/applications/payment-method",
    phoneNumber: "/applications/phone-number",
    previousLeavesIntro: "/applications/previous-leaves-intro",
    previousLeavesOtherReason: "/applications/previous-leaves-other-reason",
    previousLeavesOtherReasonDetails:
      "/applications/previous-leaves-other-reason-details",
    previousLeavesSameReason: "/applications/previous-leaves-same-reason",
    previousLeavesSameReasonDetails:
      "/applications/previous-leaves-same-reason-details",
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
    status: {
      claim: "/applications/status",
      payments: "/applications/status/payments",
    },
    // Note that this route is used by the back-end when generating notification emails for
    // the claimant (see notifications.py). Changes here will need to be coordinated with the back-end.
    success: "/applications/success",
    taxWithholding: "/applications/tax-withholding",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.applications.todo,
    // which is less confusing than seeing routes.applications.checklist
    todo: "/applications/checklist",
    upload: {
      bondingProofOfBirth: "/applications/upload/proof-of-birth",
      bondingProofOfPlacement: "/applications/upload/proof-of-placement",
      caringCertification:
        "/applications/upload/family-member-medical-certification",
      index: "/applications/upload",
      medicalCertification: "/applications/upload/medical-certification",
      otherId: "/applications/upload/other-id",
      pregnancyCertification:
        "/applications/upload/pregnancy-medical-certification",
      stateId: "/applications/upload/state-id",
    },
    uploadCertification: "/applications/upload-certification",
    uploadDocsOptions: "/applications/upload-docs-options",
    uploadId: "/applications/upload-id",
    workPatternType: "/applications/work-pattern-type",
  },
  auth: {
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
    inLocoParentis:
      "https://www.dol.gov/agencies/whd/fact-sheets/28C-fmla-eldercare",
    massTaxConnect: "https://mtc.dor.state.ma.us/mtc/_/",
    massgov: {
      applyingSelfOrUnemployed:
        "https://www.mass.gov/how-to/how-to-apply-for-paid-family-or-medical-leave-if-you-are-self-employed-or-unemployed",
      applyingToMilitaryLeave:
        "https://www.mass.gov/how-to/how-to-apply-for-military-related-paid-family-leave",
      approvalTimeline: "https://mass.gov/pfml/application-timeline",
      benefitsCalculator:
        "https://calculator.digital.mass.gov/pfml/yourbenefits/",
      benefitsGuide_aboutBondingLeave:
        "https://www.mass.gov/family-leave-bonding",
      benefitsGuide_benefitYears:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-overview-and-benefits#getting-paid-and-taxes-on-benefits-",
      benefitsGuide_benefitsAmountDetails:
        "https://www.mass.gov/how-much-will-i-get-paid",
      benefitsGuide_seriousHealthCondition:
        "https://www.mass.gov/pfml-serious-health-condition",
      calculateHours: "https://www.mass.gov/pfml-calculate-hours",
      caregiverCertificationForm: "https://www.mass.gov/family-caring-form",
      caregiverRelationship:
        "https://www.mass.gov/family-caring-leave-relationships",
      caseCreationErrorGuide:
        "https://www.mass.gov/forms/apply-for-paid-leave-if-you-received-an-error",
      consentAgreement:
        "https://www.mass.gov/info-details/massachusetts-department-of-family-and-medical-leave-informed-consent-agreement",
      dfml: "https://www.mass.gov/orgs/department-of-family-and-medical-leave",
      dfmlRegulations:
        "https://www.mass.gov/regulations/458-CMR-200-family-and-medical-leave",
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
      healthcareProviderForm: "https://www.mass.gov/medical-leave-form",
      identityProof:
        "https://www.mass.gov/info-details/identity-proof-for-paid-leave",
      informedConsent: "https://www.mass.gov/paidleave-informedconsent",
      intermittentLeaveGuide:
        "https://www.mass.gov/intermittent-leave-instructions",
      mailFaxInstructions: "https://www.mass.gov/pfmlsubmitinfo",
      manageApprovedApplication:
        "https://www.mass.gov/info-details/managing-your-approved-paid-family-or-medical-leave-claim",
      medicalBonding: "https://www.mass.gov/pfml-medical-bonding",
      multipleBirths: "https://www.mass.gov/pfml-multiple-births",
      onlineAppealsForm:
        "https://www.mass.gov/forms/request-an-appeal-for-paid-family-and-medical-leave",
      paidLeave:
        "https://www.mass.gov/topics/paid-family-and-medical-leave-in-massachusetts",
      pfml: "https://www.mass.gov/pfml",
      privacyPolicy: "https://www.mass.gov/privacypolicy",
      proofOfBirthOrPlacement:
        "https://www.mass.gov/info-details/required-documents-for-your-paid-family-and-medical-leave-pfml-application#for-family-leave-applications-",
      reductionsOverview:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefit-reductions",
      requestAnAppealForPFML:
        "https://www.mass.gov/how-to/appealing-a-denied-paid-family-or-medical-leave-claim",
      schedulingLeaveGuide:
        "https://www.mass.gov/info-details/intermittent-and-reduced-leave-schedules",
      sevenDayWaitingPeriodInfo: "https://www.mass.gov/getting-paid",
      taxGuide:
        "https://www.mass.gov/service-details/find-a-tax-professional-to-help-with-your-taxes",
      taxLiability: "https://www.mass.gov/pfml-tax-liability",
      usingAccruedPaidLeave:
        "https://www.mass.gov/info-details/how-other-leave-and-benefits-can-affect-your-paid-family-and-medical-leave#paid-time-off-through-your-employer-",
      usingOtherLeave:
        "https://www.mass.gov/info-details/how-other-leave-and-benefits-can-affect-your-paid-family-and-medical-leave",
      verifyEmployer: "https://www.mass.gov/pfml-verify-employer",
      whenCanIUsePFML:
        "https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-fact-sheet#when-can-i-use-pfml?-",
      whichPaidLeave: "https://www.mass.gov/which-paid-leave",
      zeroBalanceEmployer: "https://www.mass.gov/pfml-zero-balance-employer",
    },
    puertoRicanBirthCertificate: "https://prfaa.pr.gov/faqs",
    workVisa:
      "https://travel.state.gov/content/travel/en/us-visas/employment/temporary-worker-visas.html",
  },
  index: "/",
  twoFactor: {
    smsConfirm: "/two-factor/sms/confirm",
    smsIndex: "/two-factor/sms",
    smsSetup: "/two-factor/sms/setup",
    smsVerify: "/two-factor/sms/verify",
  },
  user: {
    consentToDataSharing: "/user/consent-to-data-sharing",
    convertToEmployee: "/user/convert-to-employee",
    convertToEmployer: "/user/convert-to-employer",
    settings: "/user/settings",
  },
};

/**
 * @param url - path, with or without query param
 */
export const isEmployersRoute = (url: string) => {
  return Object.values(routes.employers).includes(getRouteFromUrl(url));
};

/**
 * @param url - path, with or without query param
 */
export const isApplicationsRoute = (url: string) => {
  return Object.values(routes.applications).includes(getRouteFromUrl(url));
};

/**
 * @param url - path, with or without query param
 */
const getRouteFromUrl = (url: string) => {
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
