/**
 *
 * @file US English language file.
 * @see docs/internationalization.md
 *
 */

const pages = {
  eligibility: {
    form: {
      firstNameLabel: "First name",
      lastNameLabel: "Last name",
      middleNameLabel: "Middle name",
      nameSectionHint:
        "Fill out your name as it appears on official documents like your driver’s license or W-2.",
      nameSectionLabel: "What's your name?",
      ssnSectionHint:
        "Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number.",
      ssnSectionLabel: "What’s your Social Security Number?",
      title: "Tell us about yourself",
    },
    wages: {
      dataIsCorrectLabel: "Does the employment history look correct to you?",
      descriptionP1:
        "According to our records, you've worked for $t(pages.eligibility.wages.employers, { 'count': {{totalEmployers}} }) in the last 12 months.",
      descriptionP2:
        "Your earnings are an estimate of what you earned before paying taxes.",
      detailsLabel: "Show my full wage history",
      employers: "{{count}} employer",
      employers_plural: "{{count}} employers",
      q1MonthRange: "October - December",
      q2MonthRange: "January - March",
      q3MonthRange: "April - June",
      q4MonthRange: "July - September",
      title: "Verify your employment history",
      wagesHistoryTableCaption: "Estimated earnings from {{employer}}",
      wagesTableEarningsHeading: "Estimated earnings",
      wagesTableEmployerHeading: "Employer",
      wagesTableHeading: "Employment history from the past 12 months",
      wagesTablePeriodHeading: "Period",
    },
  },
  index: {
    eligibilityCheckInfoHeader: "How it works",
    eligibilityCheckInfoNameAndNumber:
      "We need your full legal name and Social Security Number or Individual Tax Identification Number to find you in our records.",
    eligibilityCheckInfoUseToDetermineEligibility:
      "We'll use this information to determine if you're eligible for paid leave.",
    eligibilityCheckInfoVerifyEmploymentEarnings:
      "You will verify a summarized employment history and earnings from the past 12 months.",
    eligibilityCheckTimeEstimation: "This should take less than 5 minutes.",
    financialRequirementStatement:
      "Before you can create a claim, we need to see if you meet the financial requirements to take paid leave.",
    pageHeader: "Checking your eligibility to take leave",
    startButtonText: "Start",
  },
};

const components = {
  authNav: {
    logOutButtonText: "Log out",
  },
  exemption: {
    contactEmployer:
      "Please contact your employer to learn how to request paid leave.",
    employerHasExemption:
      "This plan meets or exceeds the benefits offered through the Commonwealth, so they do not participate in the Commonwealth's plan.",
    homeButtonText: "Back to Dashboard",
    title: "Your employer has their own paid leave plan",
  },
  form: {
    optionalText: "(optional)",
    submitButtonText: "Submit",
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave",
  },
  spinner: {
    label: "Loading",
  },
};

const englishLocale = {
  translation: Object.assign({}, { components, pages }),
};

export default englishLocale;
