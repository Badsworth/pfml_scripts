/**
 *
 * @file US English language file for i18next-based i18n.
 * @see docs/internationalization.md
 *
 */

const errors = {
  auth: {
    codeDeliveryFailure:
      "We encountered an error while sending the verification code. Try again.",
    codeExpired:
      "Sorry, your verification code has expired or has already been used.",
    codeFormat:
      "Enter the 6-digit code sent to your email and ensure it does not include any punctuation.",
    codeMismatchException:
      "Invalid verification code. Make sure the code matches the code emailed to you.",
    codeRequired: "Enter the 6-digit code sent to your email",
    emailRequired: "Enter your email address",
    expiredVerificationCode:
      "Invalid verification code. Please request a new code.",
    incorrectEmailOrPassword: "Incorrect email or password",
    invalidParametersFallback: "Please enter all required information",
    invalidParametersIncludingMaybePassword:
      "Please check the requirements and try again. Ensure all required information is entered and the password meets the requirements.",
    invalidPhoneFormat: "Invalid phone number",
    passwordErrors:
      "Your password does not meet the requirements. Please check the requirements and try again.",
    passwordRequired: "Enter your password",
    userNotConfirmed:
      "Please first confirm your account by following the instructions in the verification email sent to your inbox.",
    userNotFound: "Incorrect email",
    usernameExists: "An account with the given email already exists",
  },
  caughtError:
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  caughtError_ForbiddenError:
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
  caughtError_NetworkError: "$t(shared.networkError)",
  caughtError_UserNotFoundError:
    "Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  claims: {
    child_birth_date: {
      pattern: "Please enter a valid date of birth.",
    },
    child_placement_date: {
      pattern: "Please enter a valid placement date.",
    },
    date_of_birth: {
      pattern: "Please enter a valid date of birth.",
    },
    employee_ssn: {
      pattern: "Please enter a 9-digit Social Security Number.",
    },
    employer_fein: {
      pattern: "Please enter a 9-digit FEIN.",
    },
    leave_details: {
      employer_notification_date: {
        pattern: "Please enter a valid notification date.",
      },
    },
    mass_id: {
      pattern: "Please enter your ID in the correct format.",
    },
  },
  invalidFileType:
    "Only PDF and image files may be uploaded. See the tips below for suggestions on how to convert them to an image file. These files that you selected will not be uploaded: {{disallowedFileNames}}",
  network:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  // These fallbacks shouldn't normally render, but they may if a validation rule or
  // field is introduced and we don't add a custom field-level error message for it.
  validationFallback: {
    invalid: "Field ({{field}}) has invalid value.",
    // Field's value didn't match an expected regex pattern:
    pattern: "Field ({{field}}) didn't match expected format.",
  },
};

const shared = {
  backToLoginLink: "Back to log in",
  // TODO: Correct phone number
  // https://lwd.atlassian.net/browse/CP-143
  callCenterPhoneNumber: "(XXX) XXX-XXXX",
  choiceNo: "No",
  choiceYes: "Yes",
  claimDurationTypeContinuous: "Continuous leave",
  claimDurationTypeIntermittent: "Intermittent leave",
  claimDurationTypeReducedSchedule: "Reduced leave schedule",
  claimsLeaveDetailsTitle: "Leave details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsOtherLeaveTitle: "Other income and benefits",
  claimsVerifyIdTitle: "Verify your identity",
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid Leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Short-term disability insurance",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Bonding leave",
  leaveReasonMedical: "Medical leave",
  leaveReasonServiceMemberFamily: "Military family",
  multipleEmployerAppAlert:
    "You need to complete a separate application for each employer you are taking leave from.",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  otherIncomeEntryPrefix: "Income",
  otherIncomeType_jonesAct: "Jones Act benefits",
  otherIncomeType_otherEmployer: "Earnings from another employer",
  otherIncomeType_railroadRetirement: "Railroad Retirement benefits",
  otherIncomeType_retirementDisability:
    "Disability benefits under a governmental retirement plan",
  otherIncomeType_selfEmployment: "Earnings from self-employment",
  otherIncomeType_ssdi: "Social Security Disability Insurance",
  otherIncomeType_unemployment: "Unemployment Insurance",
  otherIncomeType_workersCompensation: "Workers Compensation",
  passwordHint:
    "Your password must be at least 8 characters long and include numbers and letters.",
  passwordLabel: "Password",
  paymentMethodAch: "Direct deposit",
  paymentMethodDebit: "Debit card",
  pregnancyOrRecentBirthLabel:
    "Are you pregnant or have you recently given birth?",
  previousLeaveEntryPrefix: "Previous leave",
  resendVerificationCodeLink: "Resend the code",
  usernameLabel: "Email address",
  verificationCodeLabel: "6-digit code",
};

const pages = {
  app: {
    siteDescription:
      "Paid Family and Medical Leave is a state-offered benefit for anyone who works in Massachusetts and is eligible to take up to 26 weeks of paid leave for medical or family reasons.",
    siteTitle: "Paid Family and Medical Leave (PFML) | Mass.gov",
  },
  applications: {
    inProgressHeading: "In-progress applications",
    noClaims: "You don't have any applications yet.",
    submittedHeading: "Submitted applications",
    title: "Your applications",
  },
  authCreateAccount: {
    createAccountButton: "Create account",
    haveAnAccountFooterLabel: "Have an account? ",
    logInFooterLink: "Log in",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create an account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authForgotPassword: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead:
      "If an account exists for the email you provide, we will email a 6-digit verification code to it.",
    logInLink: "$t(shared.backToLoginLink)",
    submitButton: "Send code",
    title: "Forgot your password?",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authLogin: {
    accountVerified:
      "Thanks for verifying your email address. You may now log into your account.",
    accountVerifiedHeading: "Email successfully verified",
    createAccountLink:
      "Or <create-account-link>create an account</create-account-link>",
    forgotPasswordLink: "Forgot your password?",
    loginButton: "Log in",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Log in to get started",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authResetPassword: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead:
      "If an account exists for the email you provide, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    lead_email:
      "If an account exists for {{emailAddress}}, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    logInLink: "$t(shared.backToLoginLink)",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    submitButton: "Set new password",
    title: "Create a new password",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authVerifyAccount: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    confirmButton: "Submit",
    lead:
      "We sent a 6-digit verification code to your email address. Enter the code to verify your email.",
    lead_email:
      "We sent a 6-digit verification code to {{emailAddress}}. Enter the code to verify your email.",
    logInFooterLink: "$t(shared.backToLoginLink)",
    resendCodeLink: "Send a new code",
    title: "Verify your email address",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  claimsAverageWorkHours: {
    hint:
      "We’ll confirm this information and use it to calculate your benefit amount. If your schedule varies, tell us the average number of hours you worked over the past 52 weeks.",
    sectionLabel:
      "On average, how many hours do you work for your employer each week?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsBondingDateOfChild: {
    hint:
      "If your child is not born or placed yet, enter the expected date. You can update this date later.",
    lead:
      "You can take up to 12 weeks of family leave within the first year of your child's birth or placement.",
    sectionLabel: "What is the date of birth or placement date of your child?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsChecklist: {
    backButtonLabel: "Back to Dashboard",
    completed: "Completed",
    edit: "Edit",
    resume: "Resume",
    screenReaderNumberPrefix: "Step",
    start: "Start",
    stepHTMLDescription_employerInformation:
      "You will need to know:<ul class='usa-list'><li>Your employer's FEIN.</li><li>The date you told your employer you were taking leave.</li></ul>",
    stepHTMLDescription_leaveDetails:
      "You will need:<ul class='usa-list'><li>A completed Healthcare Provider Form if you are taking medical leave because you can’t work due to an injury, illness, or pregnancy.</li></ul>",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul class='usa-list'><li>If you will use any employer-sponsored benefits during your leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any paid or unpaid leave you’ve taken since January 1, 2021 for a qualifying condition.</li></ul>",
    stepHTMLDescription_payment:
      "You will need to know:<ul class='usa-list'><li>Your bank account information, if you want to be paid through Direct Deposit.</li></ul>",
    stepHTMLDescription_verifyId:
      "You will need:<ul class='usa-list'><li>Proof of your identity, like a driver’s license. See the full list of accepted identity documents.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListTitle: "Create a new application",
    stepTitle_employerInformation: "Enter employment information",
    stepTitle_leaveDetails: "Enter leave details",
    stepTitle_otherLeave: "Report other leave and benefits",
    stepTitle_payment: "Add payment information",
    stepTitle_verifyId: "Verify your identity",
    submitButton: "Review and submit application",
  },
  claimsConfirm: {
    explanation1:
      "We use this application to determine the leave time and benefit amount you will receive.",
    explanation2:
      "We need true answers to every question so that we can manage this program the way the law requires. Please confirm that you have answered as truthfully as you can.",
    submitApplicationButton: "Agree and Submit My Application",
    title: "Confirm and submit",
    truthAttestation:
      "I believe all the answers I have given are true. I understand that I need to give true answers to all questions in order to receive and keep my paid leave benefits and job protections. I understand false answers may forfeit my rights to paid leave.",
  },
  claimsDateOfBirth: {
    sectionLabel: "What's your birthdate?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsDuration: {
    continuousTypeHint: "$t(shared.claimDurationTypeContinuous)",
    continuousTypeLabel:
      "I need to take off work completely for a period of time.",
    continuousWeeksHint:
      'Refer to Question 24 in the "Estimated leave period" section of the Healthcare Provider Form.',
    continuousWeeksLabel:
      "How many weeks will you need to take continuous leave from work?",
    durationTypeSectionHint:
      'Refer to Question 18 in the "Ability to work" section of the Healthcare Provider Form.',
    durationTypeSectionLabel: "Which of the following situations apply?",
    durationTypeSelectAllHint: "Select all that apply.",
    intermittentDurationBasisDaysLabel: "At least a day",
    intermittentDurationBasisHint:
      'Refer to Question 28 in the "Estimated leave period" section of the Healthcare Provider Form.',
    intermittentDurationBasisHoursLabel: "Less than a full work day",
    intermittentDurationBasisLabel: "How long will an absence typically last?",
    intermittentDurationHint:
      'Refer to Question 28 in the "Estimated leave period" section of the Healthcare Provider Form.',
    intermittentDurationLabel: "",
    intermittentDurationLabelBase:
      "How many {{unit}} of work will you miss per absence?",
    intermittentDurationLabel_Days:
      '$t(pages.claimsDuration.intermittentDurationLabelBase, {"unit": "days"})',
    intermittentDurationLabel_Hours:
      '$t(pages.claimsDuration.intermittentDurationLabelBase, {"unit": "hours"})',
    intermittentFrequencyBasisDaysLabel: "Irregular over the next 6 months",
    intermittentFrequencyBasisHint:
      'Refer to Question 27 in the "Estimated leave period" section of the Healthcare Provider Form.',
    intermittentFrequencyBasisLabel:
      "How often might you need to be absent from work?",
    intermittentFrequencyBasisMonthsLabel: "At least once a month",
    intermittentFrequencyBasisWeeksLabel: "At least once a week",
    intermittentFrequencyHint:
      'Refer to Question 27 in the "Estimated leave period" section of the Healthcare Provider Form.',
    intermittentFrequencyLabel: "",
    intermittentFrequencyLabelBase: "Estimate how many absences {{per}}.",
    intermittentFrequencyLabel_Months:
      '$t(pages.claimsDuration.intermittentFrequencyLabelBase, {"per": "per month"})',
    intermittentFrequencyLabel_Weeks:
      '$t(pages.claimsDuration.intermittentFrequencyLabelBase, {"per": "per week"})',
    intermittentFrequencyLabel_every6months:
      '$t(pages.claimsDuration.intermittentFrequencyLabelBase, {"per": "over the next 6 months"})',
    intermittentSectionLabel:
      "Tell us the estimated frequency and duration of your intermittent leave.",
    intermittentTypeHint: "Intermittent leave",
    intermittentTypeLabel: "I need to take off work at irregular intervals.",
    reducedHoursPerWeekHint:
      'Refer to Question 26 in the "Estimated leave period" section of the Healthcare Provider Form.',
    reducedHoursPerWeekLabel:
      "How many hours will your work schedule be reduced by each week?",
    reducedTypeHint: "$t(shared.claimDurationTypeReducedSchedule)",
    reducedTypeLabel: "I need to work a reduced schedule for a period of time.",
    reducedWeeksHint:
      'Refer to Question 25 in the "Estimated leave period" section of the Healthcare Provider Form.',
    reducedWeeksLabel:
      "How many weeks of a reduced leave schedule do you need?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsEmployerBenefitDetails: {
    addButton: "Add another benefit",
    amountExample: "For example, $250 every month",
    amountLabel: "How much will you receive?",
    cardHeadingPrefix: "$t(shared.employerBenefitEntryPrefix)",
    choiceHint_familyOrMedicalLeave:
      "For example, a paid maternity leave policy",
    choiceHint_paidLeave:
      "For example, vacation time, sick leave, or personal time",
    choiceHint_permanentDisability:
      "Also known as a permanent disability policy",
    choiceHint_shortTermDisability:
      "Also known as temporary disability insurance",
    choiceLabel_familyOrMedicalLeave:
      "$t(shared.employerBenefitType_familyOrMedicalLeave)",
    choiceLabel_paidLeave: "$t(shared.employerBenefitType_paidLeave)",
    choiceLabel_permanentDisability:
      "$t(shared.employerBenefitType_permanentDisability)",
    choiceLabel_shortTermDisability:
      "$t(shared.employerBenefitType_shortTermDisability)",
    endDateLabel: "When will you stop using the benefit?",
    removeButton: "Remove benefit",
    sectionLabel: "Tell us about benefits you will receive from your employer.",
    startDateLabel: "When will you start using the benefit?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeLabel: "What kind of benefit is it?",
  },
  claimsEmployerBenefits: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hintHeader: "Employer-sponsored benefits you must report are:",
    hintList: [
      "Accrued paid leave, such as vacation time, sick time, personal time, or other paid time off",
      "Short-term disability insurance",
      "Permanent disability insurance",
      "Family or medical leave insurance, such as a maternity leave policy",
    ],
    sectionLabel:
      "Will you use any employer-sponsored benefits during your leave?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsEmploymentStatus: {
    choiceLabel_employed: "I'm employed in Massachusetts",
    choiceLabel_selfEmployed: "I'm self-employed",
    choiceLabel_unemployed: "I'm unemployed",
    feinHint:
      "This number is 9-digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W-2 or 1099-MISC. Ask your employer if you need help getting this information.",
    feinLabel:
      "What is your employer's Federal Employer Identification Number (FEIN)?",
    furloughAnswer:
      'If your hours have been cut or significantly reduced but you have not been laid off, select "$t(pages.claimsEmploymentStatus.choiceLabel_employed)"',
    furloughQuestion: "What if I've been furloughed?",
    multipleEmployerAppAlert: "$t(shared.multipleEmployerAppAlert)",
    sectionLabel: "What is your employment status?",
    title: "Employment information",
  },
  claimsLeaveDates: {
    endDateHint_bonding:
      "If you have already returned to work, when was your last day of leave?",
    endDateHint_medical:
      'Refer to Question 20 in the "Ability to work" section of the Healthcare Provider Form.',
    endDateLabel_bonding: "When will your leave end?",
    endDateLabel_medical: "When will your leave end or be re-evaluated?",
    startDateHint_bonding:
      "You can take up to 12 weeks of family leave to bond with your child or children. You can take this leave at any point within the first year of your child’s birth, adoption, or placement. You do not need to take this leave all at once.",
    startDateHint_medical:
      'Refer to Question 19 in the "Ability to work" section of the Healthcare Provider Form.',
    startDateLabel_bonding: "When will you first take leave?",
    startDateLabel_medical: "When will you first need to take leave?",
    startDateLeadHint_bonding:
      "If you have already taken some or all of your family leave, when did you first miss work to bond with your child?",
    startDateLeadHint_medical:
      "If you have already taken some or all of your leave for this condition, when did you first miss work?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeaveReason: {
    activeDutyFamilyLeaveHint: "Family leave",
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    bondingLeaveHint: "Family leave",
    bondingLeaveLabel: "I need to bond with my child after birth or placement.",
    medicalLeaveHint: "Medical leave",
    medicalLeaveLabel: "I can’t work due to an illness, injury, or pregnancy.",
    sectionLabel: "Why do you need to take time off?",
    serviceMemberFamilyLeaveHint: "Family leave",
    serviceMemberFamilyLeaveLabel:
      "I need to care for a family member who serves in the armed forces.",
    title: "Leave type",
  },
  claimsName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    lead:
      "Fill out your name as it appears on official documents like your driver’s license or W-2.",
    middleNameLabel: "Middle name",
    sectionLabel: "What's your name?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsNotifiedEmployer: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    employerNotificationDateHint: "This can be an approximate date.",
    employerNotificationLabel: "When did you tell them?",
    hint:
      "Notify your employer at least 30 days before the start of your leave if possible.",
    multipleEmployerAppAlert: "$t(shared.multipleEmployerAppAlert)",
    mustNotifyEmployerWarning:
      "Before you can submit an application, you must tell your employer that you're taking leave.",
    sectionLabel: "Have you told your employer that you are taking leave?",
    title: "Employment information",
  },
  claimsOtherIncomes: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hintHeader: "Other sources of income you must report are:",
    hintList: [
      "Workers Compensation",
      "Unemployment Insurance",
      "Social Security Disability Insurance",
      "Disability benefits under a governmental retirement plan such as STRS or PERS",
      "Jones Act benefits",
      "Railroad Retirement benefits",
      "Earnings from another employer or through self-employment",
    ],
    sectionLabel:
      "Will you receive income from any other sources during your leave?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsOtherIncomesDetails: {
    addButton: "Add another income",
    amountExample: "For example, $250 every month.",
    amountLabel: "How much will you receive?",
    cardHeadingPrefix: "$t(shared.otherIncomeEntryPrefix)",
    endDateLabel: "When will you stop receiving this income?",
    removeButton: "Remove income",
    sectionLabel: "Tell us about your other sources of income.",
    startDateLabel: "When will you start receiving this income?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeChoiceLabel_jonesAct: "$t(shared.otherIncomeType_jonesAct)",
    typeChoiceLabel_otherEmployer: "$t(shared.otherIncomeType_otherEmployer)",
    typeChoiceLabel_railroadRetirement:
      "$t(shared.otherIncomeType_railroadRetirement)",
    typeChoiceLabel_retirementDisability:
      "$t(shared.otherIncomeType_retirementDisability)",
    typeChoiceLabel_selfEmployment: "$t(shared.otherIncomeType_selfEmployment)",
    typeChoiceLabel_ssdi: "$t(shared.otherIncomeType_ssdi)",
    typeChoiceLabel_unemployment: "$t(shared.otherIncomeType_unemployment)",
    typeChoiceLabel_workersCompensation:
      "$t(shared.otherIncomeType_workersCompensation)",
    typeLabel: "What kind of income is it?",
  },
  claimsPaymentMethod: {
    accountNumberLabel: "Account number",
    achLead:
      "We need this information so you can receive your weekly benefit through Direct Deposit. Contact your bank if you are having trouble finding this information.",
    achSectionLabel: "Enter your bank account information",
    addressCityLabel: "City",
    addressLine1Label: "Street address 1",
    addressLine2Label: "Street address 2",
    addressStateLabel: "State",
    addressZipLabel: "ZIP Code",
    choiceAch: "$t(shared.paymentMethodAch)",
    choiceDebit: "$t(shared.paymentMethodDebit)",
    choiceHintAch: "Requires a bank account",
    debitSectionLabel: "Where should we send your debit card?",
    routingNumberHint:
      "This is the 9-digit number found on the lower left corner of a check.",
    routingNumberLabel: "Routing number",
    sectionLabel: "How do you want to get your weekly benefit?",
    title: "Payment method",
  },
  claimsPreviousLeaves: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    detailsLabel: "What counts as a qualifying reason?",
    hintHeader:
      "The following are qualifying reasons for taking paid or unpaid leave:",
    hintList: [
      "You couldn’t work due to an illness, injury, or pregnancy.",
      "You bonded with your child after birth or placement.",
      "You needed to manage family affairs while a family member is on active duty in the armed forces.",
      "You needed to care for a family member who serves in the armed forces.",
      "You needed to care for a sick family member.",
    ],
    sectionLabel:
      "Have you taken paid or unpaid leave since January 1, 2021 for a qualifying reason?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesDetails: {
    addButton: "Add another leave",
    cardHeadingPrefix: "$t(shared.previousLeaveEntryPrefix)",
    endDateLabel: "When did your leave end?",
    removeButton: "Remove leave",
    sectionLabel: "Tell us about previous paid or unpaid leave",
    startDateLabel: "When did your leave begin?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsReasonPregnancy: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    pregnancyOrRecentBirthLabel: "$t(shared.pregnancyOrRecentBirthLabel)",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsReview: {
    averageWorkHoursLabel: "Average hours worked per week",
    bondingLeaveLabel: "Child's date of birth or placement date",
    confirmationAction: "Confirm information is correct",
    editLink: "Edit",
    employerBenefitEntryLabel:
      "$t(shared.employerBenefitEntryPrefix) {{count}}",
    employerBenefitLabel: "Employer-sponsored benefits?",
    employerBenefitType_familyOrMedicalLeave:
      "$t(shared.employerBenefitType_familyOrMedicalLeave)",
    employerBenefitType_paidLeave: "$t(shared.employerBenefitType_paidLeave)",
    employerBenefitType_permanentDisability:
      "$t(shared.employerBenefitType_permanentDisability)",
    employerBenefitType_shortTermDisability:
      "$t(shared.employerBenefitType_shortTermDisability)",
    employerFeinLabel: "Employer's FEIN",
    employerNotifiedLabel: "Notified employer",
    employerNotifiedValue: "No",
    employerNotifiedValue_true: "Notified employer on {{date}}",
    employmentSectionHeading: "Employment information",
    employmentStatusLabel: "Employment status",
    employmentStatusValue_employed: "Currently employed",
    employmentStatusValue_selfEmployed: "Self-employed",
    employmentStatusValue_unemployed: "Unemployed",
    leaveDurationLabel: "Leave duration",
    leaveDurationTypeContinuous: "$t(shared.claimDurationTypeContinuous)",
    leaveDurationTypeIntermittent: "$t(shared.claimDurationTypeIntermittent)",
    leaveDurationTypeLabel: "Leave duration type",
    leaveDurationTypeReducedSchedule:
      "$t(shared.claimDurationTypeReducedSchedule)",
    leaveReasonLabel: "Leave type",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveSectionHeading: "$t(shared.claimsLeaveDetailsTitle)",
    otherIncomeEntryLabel: "$t(shared.otherIncomeEntryPrefix) {{count}}",
    otherIncomeLabel: "Other sources of income?",
    otherIncomeType_jonesAct: "$t(shared.otherIncomeType_jonesAct)",
    otherIncomeType_otherEmployer: "$t(shared.otherIncomeType_otherEmployer)",
    otherIncomeType_railroadRetirement:
      "$t(shared.otherIncomeType_railroadRetirement)",
    otherIncomeType_retirementDisability:
      "$t(shared.otherIncomeType_retirementDisability)",
    otherIncomeType_selfEmployment: "$t(shared.otherIncomeType_selfEmployment)",
    otherIncomeType_ssdi: "$t(shared.otherIncomeType_ssdi)",
    otherIncomeType_unemployment: "$t(shared.otherIncomeType_unemployment)",
    otherIncomeType_workersCompensation:
      "$t(shared.otherIncomeType_workersCompensation)",
    otherLeaveChoiceNo: "$t(shared.choiceNo)",
    otherLeaveChoiceYes: "$t(shared.choiceYes)",
    // eslint-disable-next-line no-template-curly-in-string
    otherLeaveDollarAmount: "${{amount}} every month",
    otherLeaveSectionHeading: "$t(shared.claimsOtherLeaveTitle)",
    paymentMethodLabel: "Payment method",
    paymentMethodValue_ach: "$t(shared.paymentMethodAch)",
    paymentMethodValue_debit: "$t(shared.paymentMethodDebit)",
    paymentSectionHeading: "Payment information",
    pregnancyChoiceNo: "$t(shared.choiceNo)",
    pregnancyChoiceYes: "$t(shared.choiceYes)",
    pregnancyOrRecentBirthLabel: "$t(shared.pregnancyOrRecentBirthLabel)",
    previousLeaveEntryLabel: "$t(shared.previousLeaveEntryPrefix) {{count}}",
    previousLeaveLabel: "Previous paid or unpaid leave?",
    title: "Check your answers before sending your application",
    userDateOfBirthLabel: "Date of birth",
    userNameLabel: "Full name",
    userSectionHeading: "Verify your identity",
    userSsnLabel: "Social security number",
    userStateIdLabel: "Massachusetts driver's license or ID",
  },
  claimsSsn: {
    lead:
      "It’s recommended that you enter your SSN. Don’t have an SSN? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What's your Social Security Number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsStateId: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasStateIdLabel: "Do you have a Massachusetts driver's license or ID card?",
    idLabel: "Enter your license or ID number",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsSuccess: {
    body:
      "We are reviewing your application. You can check the status of your application anytime in the portal.",
    dashboardLink: "Return to dashboard",
    title: "Your leave application was submitted successfully",
  },
  claimsUploadCertification: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose a file",
    fileHeadingPrefix: "File",
    lead_bonding:
      "You need to upload a document to confirm your child’s date of birth, due date, or date of placement.",
    lead_medical:
      "You need to upload a copy of the <healthcare-provider-form-link>PFML Healthcare Provider Form (opens in new tab)</healthcare-provider-form-link> to prove that you need to take medical leave. You can upload a completed Family and Medical Leave Act (FMLA) form instead if your provider filled one out.",
    sectionLabel: "Upload your documentation",
    sectionLabel_medical: "Upload your Healthcare Provider form",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsUploadId: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose a file",
    fileHeadingPrefix: "File",
    lead_mass:
      "In order to verify your identity, upload a copy of both the front and the back of your ID card.",
    // TODO (CP-496): update this with the real documents users can use to ID proof
    lead_other:
      "Upload one of the following: Document 1, Document 2, or Document 3.",
    sectionLabel_mass: "Upload your Massachusetts driver’s license or ID card",
    sectionLabel_other: "Upload an identification document",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  index: {
    afterApplyingHeading: "What to expect after you apply",
    afterApplyingIntro:
      "After you complete and submit your application, Paid Family and Medical Leave staff will review it to:",
    afterApplyingList: [
      "Make sure you have worked enough hours to qualify",
      "Record the length of leave that your medical provider has certified for your own medical leave",
      "Determine how much the Commonwealth should pay you during your leave",
    ],
    afterApplyingOutro:
      "If your application is approved, you will receive weekly payments while you’re on leave.",
    applicationTimeEstimate: "Applying takes around 10 minutes.",
    createClaimButton: "Create an application",
    needForApplyingHeading: "What you need to apply",
    needForApplyingList: {
      employerFein: "Your employer FEIN",
      healthcareProviderForm:
        "Your <healthcare-provider-form-link>Healthcare Provider Form</healthcare-provider-form-link>, which your healthcare provider has completed",
      leaveDates:
        "When you are planning to take leave or when you started on leave",
      leaveReason: "Why you are taking leave",
      paymentInformation: "Your bank account information",
      proofOfIdentity: "Proof of your identity, like a driver’s license",
      ssnItin:
        "Your Social Security Number or Individual Taxpayer Identification Number",
    },
    title: "Create an application",
  },
  userConsentToDataSharing: {
    agreementBody:
      "By continuing, I am indicating that I have read and understood the above user agreements. I give the DFML permission to collect, share, and use my information consistent with the terms of the agreements linked above.",
    applicationUsage: "",
    applicationUsageHeading: "Applying for PFML",
    applicationUsageIntro: "We need this information to:",
    applicationUsageList: [
      "Check your eligibility for coverage",
      "Determine your benefit amount",
      "Give you the best service possible",
    ],
    continueButton: "Agree and Continue",
    dataUsageBody:
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to your claim with your employer, health care provider(s), and contracted private partners.",
    dataUsageHeading: "How we use your data",
    fullUserAgreementBody:
      "To find out more about how the Commonwealth might use the information you share with DFML, please read the <informed-consent-link>DFML Informed Consent Agreement</informed-consent-link> and the <privacy-policy-link>Privacy Policy for Mass.gov</privacy-policy-link>.",
    fullUserAgreementHeading: "Full user agreements",
    intro:
      "The information you provide on this website will be used to administer the Department of Family and Medical Leave (DFML) program.",
    title: "How this website uses your information",
  },
};

const components = {
  applicationCard: {
    feinHeading: "Employer FEIN",
    heading: "Application {{number}}",
    leaveDurationHeading: "Leave duration",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    resumeClaimButton: "Complete your application",
  },
  authNav: {
    logOutButton: "Log out",
  },
  backButton: {
    label: "Back",
  },
  confirmSignUp: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    confirmButton: "Submit",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    signInFooterLink: "$t(shared.backToLoginLink)",
    title: "Verify your email address",
    verifyHint:
      "We sent a 6-digit verification code to {{emailAddress}}. Enter the code to verify your email.",
  },
  dashboardNavigation: {
    applicationsLink: "View your applications",
    createApplicationLink: "Create an application",
  },
  dropdown: {
    emptyChoiceLabel: "- Select an answer -",
  },
  errorBoundary: {
    message:
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
    reloadButton: "Reload this page",
  },
  errorsSummary: {
    genericHeading: "An error was encountered",
    genericHeading_plural: "{{count}} errors were encountered",
  },
  fieldsetAddress: {
    cityLabel: "City",
    line1Label: "Street address 1",
    line2Label: "Street address 2",
    stateLabel: "State",
    zipLabel: "ZIP",
  },
  fileCard: {
    removeButton: "Remove file",
  },
  fileUploadDetails: {
    label: "Some tips for uploading documents and images",
    sizeNotice:
      "Files should be 22 MB or smaller. If your file is larger than 22 MB, try resizing it or splitting it into separate files.",
    tips: [
      {
        listHeading: "This website only accepts:",
        listItems: ["PDF documents", "Images (.jpg, .jpeg, .png, .gif, .webp)"],
      },
      {
        listHeading:
          "If your file is not in one of these formats, try one of the following:",
        listItems: [
          "Take a picture of the document",
          "Take a screenshot of the document",
          "Save the document as a PDF or image, and try uploading again",
        ],
      },
      {
        listHeading: "If you're taking a picture of your document:",
        listItems: [
          "Take a picture of each document page and upload the pictures individually",
          "If you're uploading an ID card, upload separate pictures for both the front and back of the card",
          "Make sure the picture is clear and readable",
        ],
      },
      {
        listHeading: "If your document is attached to an email:",
        listItems: [
          "Open the file on your computer or phone",
          "Save it as a PDF or image, and try uploading again",
        ],
      },
    ],
  },
  footer: {
    description:
      "Paid Family and Medical Leave is a state-offered benefit for anyone who works in Massachusetts and is eligible to take up to 26 weeks of paid leave for medical or family reasons.",
    // TODO (CP-698): correct address
    orgAddress: "xxxx, Boston, MA 02210",
    orgName: "Department of Family and Medical Leave (DFML)",
    // TODO (CP-698): correct phone number
    orgPhoneNumber: "(XXX) XXX-XXXX",
    title: "Paid Family and Medical Leave (PFML)",
  },
  form: {
    continueButton: "Continue",
    dateInputDayLabel: "Day",
    dateInputExample: "For example: 04 / 28 / 1986",
    dateInputMonthLabel: "Month",
    dateInputYearLabel: "Year",
    optional: "(optional)",
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave",
  },
  signUp: {
    createAccountButton: "Create account",
    haveAnAccountFooterLabel: "Have an account?",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    signInFooterLink: "Log in",
    title: "Create an account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  siteLogo: {
    alt: "Massachusetts state seal",
  },
  spinner: {
    label: "Loading",
  },
  withClaims: {
    loadingLabel: "Loading claims",
  },
  withUser: {
    loadingLabel: "Loading account",
  },
};

const englishLocale = {
  translation: Object.assign({}, { components, errors, pages, shared }),
};

export default englishLocale;
