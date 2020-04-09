/**
 *
 * @file US English language file for i18next-based i18n.
 * @see docs/internationalization.md
 *
 */

const errors = {
  auth: {
    emailAndPasswordRequired: "Enter your email address and password",
    emailRequired: "Enter your email address",
    incorrectEmailOrPassword: "Incorrect email or password",
    invalidParametersFallback: "Please enter all required information",
    invalidPhoneFormat: "Invalid phone number",
    invalidVerificationCode: "Invalid verification code",
    passwordRequired: "Enter your password",
    verificationCodeRequired: "Enter the 6-digit code sent to your email",
  },
};

const general = {
  // TODO(CP-143) correct phone number
  callCenterPhoneNumber: "(XXX) XXX-XXXX",
};

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
      pageHeader: "Check your eligibility to take leave",
      startButtonText: "Start",
    },
  },
  index: {
    claimChecklistContact: "Contact information",
    claimChecklistDateOfLeave:
      "When you are taking leave or planning to take leave",
    claimChecklistEmployment: "Employment information",
    claimChecklistHeader:
      "To submit your claim, you will need to provide the following:",
    claimChecklistReasonForLeave: "Why you are taking leave",
    claimChecklistWhereToSendBenefits: "Where to send your benefits",
    createClaimButtonText: "Create a claim",
    pageHeader: "Get started",
  },
};

const components = {
  authNav: {
    logOutButtonText: "Log out",
  },
  authenticator: {
    errorHeading: "Please fix the following errors",
  },
  backButton: {
    label: "Back",
  },
  confirmSignUp: {
    codeLabel: "Six-digit code",
    confirmButton: "Submit",
    resendCodeLink: "Resend code",
    signInFooterLink: "Back to log in",
    title: "Verify your email address",
    verifyHint:
      "We sent a 6-digit verification code to {{emailAddress}}. Enter the code to verify your email.",
  },
  dashboardButton: {
    text: "Back to Dashboard",
  },
  eligible: {
    dataIsCorrectLabel: "Does the employment history look correct to you?",
    title: "Verify your employment history",
  },
  exemption: {
    contactEmployer:
      "Please contact your employer to learn how to request paid leave.",
    employerHasExemption:
      "This plan meets or exceeds the benefits offered through the Commonwealth, so they do not participate in the Commonwealth's plan.",
    title: "Your employer has their own paid leave plan",
  },
  form: {
    continueButton: "Continue",
    optionalText: "(optional)",
    submitButtonText: "Submit",
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave",
  },
  ineligible: {
    option1Description:
      "If you believe you have earned at least $5,100 as a Massachusetts employee in the past 12 months, call the Paid Family Leave Contact Center at $t(general.callCenterPhoneNumber). Then come back to create a claim.",
    option1Heading: "Call the Paid Family Leave Contact Center",
    option2Description:
      "If you need to begin tracking your claim right away, you can create a claim before you call the Contact Center.",
    option2Heading: "Create a claim",
    optionsHeading: "What are my options?",
    title: "Based on our records, you're not eligible",
  },
  recordNotFound: {
    contactPflcHeader: "Call the Paid Family Leave Center",
    contactPflcStatement:
      "If you believe you are eligible for this program, call the Paid Family Leave Contact Center at $t(general.callCenterPhoneNumber). Then come back to create a claim.",
    mainTitle: "We couldn't find you in our records",
    notContributingHeader: "You may not be contributing",
    notContributingStatement:
      "To be eligible for this program, you need to have payments into the paid leave fund. Your employer makes these payments for you every quarter. If there are no contributions, you won't show up in our records.",
    notFoundStatement:
      "We didn’t find your name and SSN together in our records. You’re not eligible to take paid leave without a matching record.",
    optionsHeader: "What are my options?",
    recordsIncorrectHeader:
      "Your information in our records might be incorrect",
    recordsIncorrectStatement:
      "There could have been an issue when your employer entered your information, such as misspelling your name.",
    whyHeader: "Why can't you find me?",
  },
  signUp: {
    createAccountButton: "Create Account",
    haveAnAccountFooterLabel: "Have an account?",
    passwordHelpText:
      "Your password must be at least 8 characters long and include numbers and letters.",
    signInFooterLink: "Sign in",
  },
  spinner: {
    label: "Loading",
  },
  wagesTable: {
    detailsLabel: "Show my full wage history",
    eligibleDescriptionP1:
      "According to our records, you've worked for $t(components.wagesTable.employers, { 'count': {{totalEmployers}} }) in the last 12 months.",
    eligibleDescriptionP2:
      "Your earnings are an estimate of what you earned before paying taxes.",
    employers: "{{count}} employer",
    employers_plural: "{{count}} employers",
    historyTableCaption: "Estimated earnings from {{employer}}",
    historyTablePeriodHeading: "Period",
    ineligibleDescription:
      "You must have earned at least $5,100 in the last 12 months.",
    q1MonthRange: "October - December",
    q2MonthRange: "January - March",
    q3MonthRange: "April - June",
    q4MonthRange: "July - September",
    tableEarningsHeading: "Estimated earnings",
    tableEmployerHeading: "Employer",
    tableHeading: "Employment history from the past 12 months",
  },
};

const englishLocale = {
  translation: Object.assign({}, { components, errors, general, pages }),
};

export default englishLocale;
