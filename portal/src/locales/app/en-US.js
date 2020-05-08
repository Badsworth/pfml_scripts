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
    passwordErrors:
      "Your password does not meet the requirements. Please check the requirements and try again.",
    passwordRequired: "Enter your password",
    verificationCodeRequired: "Enter the 6-digit code sent to your email",
  },
};

const general = {
  // TODO: Correct phone number
  // https://lwd.atlassian.net/browse/CP-143
  callCenterPhoneNumber: "(XXX) XXX-XXXX",
  siteDescription:
    "Paid Family and Medical Leave is a state-offered benefit for anyone who works in Massachusetts and is eligible to take up to 26 weeks of paid leave for medical or family reasons.",
  siteTitle: "Paid Family and Medical Leave (PFML) | Mass.gov",
};

// TODO: Combine shared and general keys
// https://lwd.atlassian.net/browse/CP-299
const shared = {
  choiceNo: "No",
  choiceYes: "Yes",
  passwordHint:
    "Your password must be at least 8 characters long and include numbers and letters.",
};

const pages = {
  claimsDateOfBirth: {
    sectionLabel: "What's your birthdate?",
    title: "$t(pages.claimsGeneral.takingLeaveTitle)",
  },
  claimsDuration: {
    avgWeeklyHoursWorkedHint:
      "Tell us how many hours you typically worked before going on leave. We need to know this so we can calculate your benefit amount.",
    avgWeeklyHoursWorkedLabel:
      "How many hours do you work in a week, on average?",
    continuousHint: "(Continuous leave)",
    continuousLabel: "Take off work completely",
    hoursOffNeededHint:
      "This can be an approximate. You can change this after your claim is approved.",
    hoursOffNeededLabel: "How many hours do you need to take off each week?",
    intermittentHint: "(Intermittent leave)",
    intermittentLabel: "Work on a reduced schedule",
    sectionLabel:
      "Do you need to take off work completely or work on a reduced schedule?",
    title: "$t(pages.claimsGeneral.leaveDurationTitle)",
  },
  claimsGeneral: {
    leaveDurationTitle: "Leave duration",
    leaveTypeTitle: "Leave type",
    takingLeaveTitle: "Who is taking leave",
  },
  claimsLeaveDates: {
    endDateLabel: "When do you expect your leave will end?",
    startDateHint: "Your leave begins the day you stopped working.",
    startDateLabel: "When do you expect your leave to begin?",
  },
  claimsLeaveType: {
    activeDutyFamilyLeaveHint: "(Family leave)",
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces",
    medicalLeaveHint: "(Medical leave)",
    medicalLeaveLabel: "I have a serious injury or illness",
    parentalLeaveHint: "(Can cover medical and family leave)",
    parentalLeaveLabel: "I need to take parental leave",
    sectionLabel: "Why do you need to take time off?",
    title: "$t(pages.claimsGeneral.leaveTypeTitle)",
  },
  claimsName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    middleNameLabel: "Middle name",
    nameSectionHint:
      "Fill out your name as it appears on official documents like your driver’s license or W-2.",
    sectionLabel: "What's your name?",
    title: "$t(pages.claimsGeneral.takingLeaveTitle)",
  },
  claimsNotifiedEmployer: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hint:
      "Notify your employer at least 30 days before the start of your leave if possible.",
    label: "Have you notified your employer of your leave?",
    title: "Medical Leave Application",
  },
  claimsSsn: {
    sectionHint:
      "Don't have an SSN? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What's your Social Security Number?",
    title: "$t(pages.claimsGeneral.takingLeaveTitle)",
  },
  claimsStateId: {
    hasIdChoiceLabel:
      "Do you have a Massachusetts driver's license or ID card?",
    hasIdChoiceNo: "$t(shared.choiceNo)",
    hasIdChoiceYes: "$t(shared.choiceYes)",
    idLabel: "Enter your license or ID number",
    title: "$t(pages.claimsGeneral.takingLeaveTitle)",
  },
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
    activeClaimsHeading: "Active claims",
    claimCardHeading: "Claim {{number}}",
    claimChecklistContact: "Contact information",
    claimChecklistDateOfLeave:
      "When you are taking leave or planning to take leave",
    claimChecklistEmployment: "Employment information",
    claimChecklistHeader:
      "To submit your claim, you will need to provide the following:",
    claimChecklistReasonForLeave: "Why you are taking leave",
    claimChecklistWhereToSendBenefits: "Where to send your benefits",
    createClaimButtonText: "Start a new claim",
    newClaimHeading: "Start a new claim",
    resumeClaimButton: "Finish your claim",
    tagInProgress: "In Progress",
    title: "Dashboard",
  },
};

const components = {
  authNav: {
    logOutButtonText: "Log out",
  },
  authenticator: {
    accountVerified:
      "Thanks for verifying your email address. You may now log into your account.",
    accountVerifiedHeading: "Email successfully verified",
    errorHeading: "Please fix the following errors",
  },
  backButton: {
    label: "Back",
  },
  confirmSignUp: {
    codeLabel: "6-digit code",
    confirmButton: "Submit",
    resendCodeLink: "Resend the code",
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
  errorsSummary: {
    genericHeading: "An error was encountered",
    genericHeading_plural: "{{count}} errors were encountered",
  },
  exemption: {
    contactEmployer:
      "Please contact your employer to learn how to request paid leave.",
    employerHasExemption:
      "This plan meets or exceeds the benefits offered through the Commonwealth, so they do not participate in the Commonwealth's plan.",
    title: "Your employer has their own paid leave plan",
  },
  forgotPassword: {
    codeLabel: "6-digit code",
    leadCreatePasswordView:
      "If an account exists for {{emailAddress}}, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    leadSendView:
      "If an account exists for the email you provide, we will email a 6-digit verification code to it.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "Resend the code",
    signInFooterLink: "Back to log in",
    submitEmailButton: "Send code",
    submitPasswordButton: "Set new password",
    titleCreatePasswordView: "Create a new password",
    titleSendView: "Forgot your password?",
  },
  form: {
    continueButton: "Continue",
    dateInputDayLabel: "Day",
    dateInputMonthLabel: "Month",
    dateInputYearLabel: "Year",
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
    createAccountButton: "Create account",
    emailLabel: "Email address",
    haveAnAccountFooterLabel: "Have an account?",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "Password",
    signInFooterLink: "Log in",
    title: "Create an account",
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
  translation: Object.assign(
    {},
    { components, errors, general, pages, shared }
  ),
};

export default englishLocale;
