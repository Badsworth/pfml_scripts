/**
 *
 * @file US English language file.
 * @see docs/internationalization.md
 *
 */

const pages = {
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
    startButtonText: "Start"
  }
};

const components = {
  authNav: {
    logOutButtonText: "Log out"
  },
  form: {
    optionalText: "(optional)"
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave"
  }
};

const englishLocale = {
  translation: Object.assign({}, { components, pages })
};

export default englishLocale;
