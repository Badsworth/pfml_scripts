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
    insecurePassword:
      "Please use a different password. Avoid commonly used passwords and avoid using the same password on multiple websites.",
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
      invalid_age: "The person taking leave must be at least 14 years old.",
      invalid_year_range: `Date of birth year is not in a valid range (on or after ${new Date().getFullYear() - 100
        }).`,
      pattern: "Please enter a valid date of birth.",
    },
    employer_fein: {
      pattern: "Please enter a 9-digit FEIN.",
    },
    leave_details: {
      employer_notification_date: {
        pattern: "Please enter a valid notification date.",
      },
    },
    mailing_address: {
      zip: {
        pattern: "Please enter a 5- or 9-digit ZIP code.",
      },
    },
    mass_id: {
      pattern:
        "Please enter your license or ID number. It should be a total of nine digits including letters and numbers.",
    },
    payment_preferences: {
      account_details: {
        account_number: {
          minLength:
            "Account number too short: Account number must be at least 6 digits.",
          maxLength:
            "Account number too long: Account number must be 17 digits or fewer.",
        },
        routing_number: {
          pattern: "Please enter a 9 digit routing number.",
        },
      },
    },
    residential_address: {
      zip: {
        pattern: "Please enter a 5- or 9-digit ZIP code.",
      },
    },
    tax_identifier: {
      pattern: "Please enter a 9-digit number.",
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
  achTypeChecking: "Checking",
  achTypeSavings: "Savings",
  backToLoginLink: "Back to log in",
  // TODO (CP-143): Correct phone number, but preserve usage of non-breaking hyphens to avoid awkward text wrapping
  // https://alignedonline.com/non%E2%80%91breaking-spaces
  callCenterPhoneNumber: "XXX‑XXX‑XXXX",
  choiceNo: "No",
  choiceYes: "Yes",
  claimDurationTypeContinuous: "Continuous leave",
  claimDurationTypeIntermittent: "Intermittent leave",
  claimDurationTypeReducedSchedule: "Reduced leave schedule",
  claimsEmploymentInfoTitle: "Employment information",
  claimsLeaveDetailsTitle: "Leave details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsOtherLeaveTitle: "Other leave, income, and benefits",
  claimsVerifyIdTitle: "Your identity",
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Short-term disability insurance",
  fileUpload_addAnotherFileButton: "Choose another file",
  fileUpload_addFirstFileButton: "Choose a file",
  fileUpload_fileHeadingPrefix: "File",
  filesUploaded: "Number of files uploaded",
  leavePeriodMedicalAlert:
    "You will need a completed medical leave certification form for this section.",
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
  paymentMethodDebit: "MA PFML Prepaid Debit Card",
  pregnancyOrRecentBirthLabel:
    "Are you pregnant or have you recently given birth?",
  previousLeaveEntryPrefix: "Previous leave",
  qualifyingReasonDetailsLabel: "What counts as a qualifying reason?",
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
  claimsAddress: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasMailingAddressHint:
      "We may send notices to this address. If you choose to get your payments through a debit card, we will mail the card to this address.",
    hasMailingAddressLabel: "Do you get your mail at this address?",
    hint:
      "If you are part of an Address Confidentiality Program, please provide your substitute address.",
    mailingAddressLabel: "What is your mailing address?",
    sectionLabel: "What is your current residential address?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsBondingDateOfChild: {
    birthHint:
      "If your child has not been born yet, enter the expected due date.",
    sectionLabel_adopt_foster:
      "When did the child arrive in your home through foster care or adoption?",
    sectionLabel_newborn: "When was your child born?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsChecklist: {
    backButtonLabel: "Back to Dashboard",
    completed_editable: "Completed",
    completed_uneditable: "Confirmed",
    edit: "Edit",
    resume: "Resume",
    screenReaderNumberPrefix: "Step",
    start: "Start",
    stepHTMLDescription_bondingAdoptFoster:
      "You need to provide a statement confirming the placement and the date of placement.",
    stepHTMLDescription_bondingNewborn:
      "You need to provide your child's birth certificate or a document from a health care provider that shows the child’s birth date.",
    stepHTMLDescription_employerInformation:
      "You will need to know:<ul><li>Your employer’s 9-digit federal employer identification number (FEIN or EIN). <br><strong>Where to find this: </strong>on your W-2 or 1099, or ask your employer’s finance department.</li><li>The date you told your employer you were taking leave.</li></ul>",
    stepHTMLDescription_leaveDetails:
      "<p>If you are taking medical leave due to injury, illness, or pregnancy, you need to have your health care provider fill out <healthcare-provider-form-link>the certification form</healthcare-provider-form-link>. Some of the answers you will need for the online application will come from your health care provider’s answers on the certification form.</p><p>If you are taking leave to bond with a child, you will need to know:</p><ul><li>The child's date of birth, due date, or the date they arrived in your home for adoption or foster care.</li><li>When you want your leave to begin and end.</li></ul>",
    stepHTMLDescription_medical:
      "You need to provide your completed <healthcare-provider-form-link>Health Care Provider Certification</healthcare-provider-form-link>. ",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul><li>If you will use any benefits from your employer because you are taking leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any leave you’ve taken since January 1, 2021 for a condition that is covered by Paid Family and Medical Leave.</li></ul>",
    stepHTMLDescription_payment:
      "<p>Tell us how you want to receive payment.</p><p>If you want to receive payment by direct deposit, you will need to provide your bank account information, including a routing number and account number.</p>",
    stepHTMLDescription_reviewAndConfirm:
      "<p>Once you confirm your leave information, we’ll notify your employer. Your job will be protected. To complete your application, you will need to finish the last three steps and submit.</p><p>If you need to edit your information in Part 1 after completing this step, you’ll need to call the Contact Center at $t(shared.callCenterPhoneNumber).</p>",
    stepHTMLDescription_uploadId:
      "Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same ID.",
    stepHTMLDescription_verifyId:
      "<p>You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card.</p><p>You will need to provide:</p><ul><li>Your name as it appears on your ID.</li><li>Your driver’s license number or Mass ID number, if you have one.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListDescription_1:
      "Your progress is automatically saved as you complete the application. You can edit any information you enter in Part 1 until step 5 is completed.",
    stepListDescription_1_submitted:
      "If you need to edit your information in Part 1, you’ll need to call the Contact Center at $t(shared.callCenterPhoneNumber). Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_2:
      "Entering payment information here leads to faster processing, but you can also call $t(shared.callCenterPhoneNumber).",
    // TODO (CP-907): Add correct fax # and address
    stepListDescription_3:
      "Uploading documents online leads to faster processing, but you can also fax documents to NNN-NNN-NNNN, or mail them to 123 Address.",
    stepListTitlePrefix: "Part {{number}}",
    stepListTitle_1: "Tell us about yourself and your leave",
    stepListTitle_2: "Enter your payment information",
    stepListTitle_3: "Upload your documents",
    stepTitle_employerInformation: "Enter employment information",
    stepTitle_leaveDetails: "Enter leave details",
    stepTitle_otherLeave: "Report other leave, income, and benefits",
    stepTitle_payment: "Add payment information",
    stepTitle_reviewAndConfirm: "Review and confirm",
    stepTitle_uploadCertification: "Upload leave certification documents",
    stepTitle_uploadId: "Upload identity document",
    stepTitle_verifyId: "Verify your identity",
    submitButton: "Review and submit application",
    title: "Checklist: Create a new application",
  },
  claimsDateOfBirth: {
    sectionLabel: "What's your birthdate?",
    title: "$t(shared.claimsVerifyIdTitle)",
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
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsHoursWorkedPerWeek: {
    hint:
      "We’ll confirm this information and use it to calculate your benefit amount. If your schedule varies, tell us the average number of hours you worked over the past 52 weeks.",
    sectionLabel: "On average, how many hours do you work each week?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsIntermittentFrequency: {
    durationBasisChoice_days: "At least a day",
    durationBasisChoice_hours: "Less than a full work day",
    durationBasisHint_medical:
      'Refer to Question 32 in the "Estimate leave details" section of the certification form (page 6).',
    durationBasisLabel: "How long will an absence typically last?",
    durationHint_medical:
      'Refer to Question 32 in the "Estimate leave details" section of the certification form (page 6).',
    durationLabel_days: "How many days of work will you miss per absence?",
    durationLabel_hours: "How many hours of work will you miss per absence?",
    frequencyBasisChoice_irregular: "Irregular over the next 6 months",
    frequencyBasisChoice_months: "At least once a month",
    frequencyBasisChoice_weeks: "At least once a week",
    frequencyBasisHint_medical:
      'Refer to Question 31 in the "Estimate leave details" section of the certification form (page 6).',
    frequencyBasisLabel: "How often might you need to be absent from work?",
    frequencyHint_medical:
      'Refer to Question 31 in the "Estimate leave details" section of the certification form (page 6).',
    frequencyLabel_irregular:
      "Estimate how many absences over the next 6 months.",
    frequencyLabel_months: "Estimate how many absences per month.",
    frequencyLabel_weeks: "Estimate how many absences per week.",
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    sectionLabel:
      "Tell us the estimated frequency and duration of your intermittent leave.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodContinuous: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave, tell us when you first missed work and your last day of leave.",
    datesLead_medical:
      'If you have already taken some or all of your leave for this condition, tell us when you first missed work and your last day of leave.<br /><br />Refer to Question 27 in the "Estimate leave details" section of the certification form (page 6).',
    datesSectionLabel:
      "Enter the start and end dates for your continuous leave.",
    endDateLabel: "Last day of leave",
    hasLeaveHint_medical:
      'Refer to Question 26 in the "Estimate leave details" section of the certification form (page 6).',
    hasLeaveLabel:
      "Do you need to take off work completely for a period of time (continuous leave)?",
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodIntermittent: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave, tell us when you first missed work and your last day of leave.",
    datesLead_medical:
      'If you have already taken some or all of your leave for this condition, tell us when you first missed work and your last day of leave.<br /><br />Refer to Question 33 in the "Estimate leave details" section of the certification form (page 6).',
    datesSectionLabel:
      "Enter the start and end dates for your intermittent leave.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical: "Last day of leave or re-evaluation date",
    hasLeaveHint_medical:
      'Refer to Question 31 in the "Estimate leave details" section of the certification form (page 6).',
    hasLeaveLabel:
      "Do you need to take off work at irregular intervals (intermittent leave)?",
    hybridLeaveWarning:
      "You have to create a separate application for intermittent leave.",
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodReducedSchedule: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave, tell us when you first missed work and your last day of leave.",
    datesLead_medical:
      'If you have already taken some or all of your leave for this condition, tell us when you first missed work and your last day of leave.<br /><br />Refer to Question 30 in the "Estimate leave details" section of the certification form (page 6).',
    datesSectionLabel:
      "Enter the start and end dates for your reduced leave schedule.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical: "Last day of leave or re-evaluation date",
    hasLeaveHint_medical:
      'Refer to Question 28 in the "Estimate leave details" section of the certification form (page 6).',
    hasLeaveLabel:
      "Do you need to work a reduced schedule for a period of time (reduced leave schedule)?",
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeaveReason: {
    activeDutyFamilyLeaveHint: "Family leave",
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    bondingLeaveHint: "Family leave",
    bondingLeaveLabel:
      "I need to bond with my child after birth, adoption, or foster placement.",
    bondingTypeAdoptionLabel: "Adoption",
    bondingTypeFosterLabel: "Foster placement",
    bondingTypeLabel:
      "Will you take leave for a birth, an adoption, or a foster placement?",
    bondingTypeMultipleBirthsDetailsLabel:
      "What if I've had multiple births or placements within one year?",
    bondingTypeMultipleBirthsDetailsSummary:
      "Leave is determined based on benefit year (365 days from the first day you take leave), not based on number of children. You have 1 year to take your bonding leave from the date of the birth/placement of the child (whichever is later). ",
    bondingTypeNewbornLabel: "Birth",
    medicalLeaveHint: "Medical leave",
    medicalLeaveLabel: "I can’t work due to an illness, injury, or pregnancy.",
    sectionHint: "You can only request one leave at a time.",
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
      "Notify your employer at least 30 days before the start of your leave if possible.",
    multipleEmployerAppAlert: "$t(shared.multipleEmployerAppAlert)",
    mustNotifyEmployerWarning:
      "Before you can submit an application, you must tell your employer that you're taking leave.",
    sectionLabel: "Have you told your employer that you are taking leave?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
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
    achTypeChecking: "$t(shared.achTypeChecking)",
    achTypeLabel: "Account type",
    achTypeSavings: "$t(shared.achTypeSavings)",
    choiceAch: "$t(shared.paymentMethodAch)",
    choiceDebit: "$t(shared.paymentMethodDebit)",
    choiceHintAch: "Requires a bank account",
    choiceHintDebit: "Does not require a bank account",
    debitDestinationInfo:
      "You will receive the card in the mail at the address you listed as your mailing address.",
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
    detailsLabel: "$t(shared.qualifyingReasonDetailsLabel)",
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
    achTypeLabel: "Account type",
    achType_checking: "$t(shared.achTypeChecking)",
    achType_savings: "$t(shared.achTypeSavings)",
    childBirthDateLabel: "Child's date of birth",
    childPlacementDateLabel: "Child's placement date",
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
    employmentStatusLabel: "Employment status",
    employmentStatusValue_employed: "Currently employed",
    employmentStatusValue_selfEmployed: "Self-employed",
    employmentStatusValue_unemployed: "Unemployed",
    familyLeaveTypeLabel: "Family leave type",
    familyLeaveTypeValue_adoption: "Adoption",
    familyLeaveTypeValue_fosterCare: "Foster care",
    familyLeaveTypeValue_newBorn: "Birth",
    leaveDetailsSectionHeading: "$t(shared.leaveDetailsStepTitle)",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
    leavePeriodNotSelected: "$t(shared.choiceNo)",
    leaveReasonLabel: "Leave type",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
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
    partDescription_1:
      "If you need to make edits to Part 1, you’ll need to contact our call center at $t(shared.callCenterPhoneNumber). Your application ID is <strong>{{absence_id}}</strong>",
    partHeadingPrefix: "Part {{number}}",
    partHeading_1_final: "Review: Tell us about yourself and your leave",
    partHeading_1_part1:
      "Review and confirm: Tell us about yourself and your leave",
    partHeading_2: "Review: Your payment information",
    partOneNextStepsLine1:
      "Once you review and confirm Part 1, your in-progress application will be viewable by our call center staff. If you need to make edits to Part 1, you’ll need to contact our call center at $t(shared.callCenterPhoneNumber).",
    partOneNextStepsLine2:
      "We’ll also notify your employer that you’ve started an application for paid family and medical leave.",
    partOneNextStepsLine3:
      "Next, you’ll be able to work on Parts 2 and 3, and submit your application.",
    paymentAccountNumLabel: "Account number",
    paymentAddressLabel: "Mailing address",
    paymentMethodLabel: "Payment method",
    paymentMethodValue_ach: "$t(shared.paymentMethodAch)",
    paymentMethodValue_debit: "$t(shared.paymentMethodDebit)",
    paymentRoutingNumLabel: "Routing number",
    pregnancyOrRecentBirthLabel: "$t(shared.pregnancyOrRecentBirthLabel)",
    pregnancyOrRecentBirth_no: "$t(shared.choiceNo)",
    pregnancyOrRecentBirth_yes: "$t(shared.choiceYes)",
    previousLeaveEntryLabel: "$t(shared.previousLeaveEntryPrefix) {{count}}",
    previousLeaveLabel: "Previous paid or unpaid leave?",
    residentialAddressLabel: "Residential address",
    stepHeading_employerInformation: "$t(shared.claimsEmploymentInfoTitle)",
    stepHeading_leaveDetails: "$t(shared.claimsLeaveDetailsTitle)",
    stepHeading_otherLeave: "$t(shared.claimsOtherLeaveTitle)",
    stepHeading_payment: "Payment information",
    stepHeading_verifyId: "$t(shared.claimsVerifyIdTitle)",
    submitAction_final: "Submit application",
    submitAction_part1: "Submit Part 1",
    title: "Check your answers before submitting your application.",
    userDateOfBirthLabel: "Date of birth",
    userNameLabel: "Name",
    userStateIdLabel: "Driver's License Number",
    userTaxIdLabel: "Social Security Number or ITIN",
  },
  claimsSsn: {
    lead:
      "It’s recommended that you enter your SSN. Don’t have an SSN? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What's your Social Security Number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsStart: {
    explanation1:
      "We use this application to determine the leave time and benefit amount you will receive.",
    explanation2:
      "We need true answers to every question so that we can manage this program the way the law requires. Please confirm that you will answer as truthfully as you can.",
    submitApplicationButton: "I understand and agree",
    title: "Start your application",
    truthAttestation:
      "I understand that I need to give true answers to all questions in order to receive and keep my paid leave benefits and job protections. I understand false answers may forfeit my rights to paid leave.",
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
      "We are reviewing your application. You can check the status of your application anytime in the portal.",
    dashboardLink: "Return to dashboard",
    title: "Your leave application was submitted successfully",
  },
  claimsUploadCertification: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose a file",
    certificationDocumentsCount: "$t(shared.filesUploaded)",
    fileHeadingPrefix: "File",
    leadListNewborn: [
      "Your child's birth certificate.",
      "A note from your child's health care provider stating your child's birth date.",
      "A note from the health care provider of the person who gave birth stating your child's birth date.",
    ],
    lead_bonding_adopt_foster:
      "You need to upload a statement from your adoption or foster agency or from the Massachusetts Department of Children and Families to confirm the placement and the date of the placement.",
    lead_bonding_newborn:
      "You need to upload one of the following documents to confirm your child’s date of birth:",
    lead_medical:
      "You need to upload a copy of the <healthcare-provider-form-link>PFML Healthcare Provider Form (opens in new tab)</healthcare-provider-form-link> to prove that you need to take medical leave. You can upload a completed Family and Medical Leave Act (FMLA) form instead if your provider filled one out.",
    sectionLabel_bonding: "Upload your documentation",
    sectionLabel_medical: "Upload your Healthcare Provider form",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsUploadId: {
    addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
    addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
    fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
    idDocumentsCount: "$t(shared.filesUploaded)",
    lead_mass:
      "In order to verify your identity, upload a copy of both the front and the back of your ID card.",
    lead_other:
      "To verify your identity you will need valid documentation issued by state or federal government.",
    sectionLabel_mass: "Upload your Massachusetts driver’s license or ID card",
    sectionLabel_other: "Upload an identification document",
    title: "$t(shared.claimsVerifyIdTitle)",
    validIdDocumentation:
      "<p><strong>You can use:</strong></p><ul><li>U.S. State or Territory Real ID</li><li>U.S. passport or passport card</li><li>Permanent Resident Card issued by DHS or INS</li><li>Employment Authorization Document (EAD) issued by DHS</li><li>Foreign passport <strong>and</strong> a <work-visa-link>work visa</work-visa-link></li></ul><p><strong>If you don’t have any of those, you can provide one of the following plus proof of your  Social Security Number or Individual Tax Identification Number:</strong></p><ul><li>Valid U.S. State or Territory License or ID</li><li>Certified copy of a birth certificate filed with a State Office of Vital Statistics or equivalent agency in the individual's state of birth. (You can only use a <puerto-rican-birth-certificate-link>Puerto Rican birth certificate</puerto-rican-birth-certificate-link> if it was issued on or after July 1, 2010.)</li><li>Certificate of Citizenship (Form N-560, or Form N-561)</li><li>Certificate of Naturalization (Form N-550 or N-570)</li></ul><p><strong>You can provide proof of your Social Security Number using one of the following documents displaying your complete Social Security Number:</strong></p><ul><li>Social Security card</li><li>W-2 Form</li><li>SSA-1099 Form</li><li>Non-SSA-1099 Form</li><li>Pay stub with your name on it</li></ul><p>Learn more about verifying your identity with different documents at <identity-proof-link>Mass.gov</identity-proof-link>.</p>",
  },
  employersClaimsReview: {
    amend: "Amend",
    documentationLabel: "Documentation",
    durationBasis_days: "{{numOfDays}} days",
    employeeInformation: {
      addressLabel: "Mailing address",
      dobLabel: "Birthdate",
      employeeNameLabel: "Employee name",
      header: "Employee information",
      ssnOrItinLabel:
        "Social Security Number or Individual Taxpayer Identification Number",
    },
    employerBenefits: {
      benefitTypeLabel: "Benefit type",
      dateRangeLabel: "Date range",
      detailsLabel: "Details",
      employerBenefitType_familyOrMedicalLeave:
        "$t(shared.employerBenefitType_familyOrMedicalLeave)",
      employerBenefitType_paidLeave: "$t(shared.employerBenefitType_paidLeave)",
      employerBenefitType_permanentDisability:
        "$t(shared.employerBenefitType_permanentDisability)",
      employerBenefitType_shortTermDisability:
        "$t(shared.employerBenefitType_shortTermDisability)",
      header: "Employer benefits",
      tableName: "Employer-sponsored benefit details",
    },
    employerIdentifierLabel: "Employer ID number (EIN)",
    feedback: {
      addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
      addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
      choiceNo: "$t(shared.choiceNo)",
      choiceYes: "$t(shared.choiceYes)",
      fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
      instructionsLabel: "Do you have any additional comments or concerns?",
      supportingDocumentationLabel:
        "If you have any supporting documentation, please attach it for review.",
      tellUsMoreLabel: "Please tell us more.",
    },
    instructionsAmendment:
      "Please review the details of this application carefully. If anything seems incorrect, you can add an amendment within each section or include general comments at the end.",
    instructionsDueDate: "Review and respond by: <strong>{{date}}</strong>",
    leaveDetails: {
      applicationIdLabel: "Application ID",
      employerNotifiedLabel: "Employer notified",
      header: "Leave details",
      leaveDurationLabel: "Leave duration",
      leaveReasonValue_activeDutyFamily:
        "$t(shared.leaveReasonActiveDutyFamily)",
      leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
      leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
      leaveReasonValue_serviceMemberFamily:
        "$t(shared.leaveReasonServiceMemberFamily)",
      leaveTypeLabel: "Leave type",
      natureOfLeaveLabel: "Nature of leave",
    },
    leaveSchedule: {
      header: "Leave schedule",
      healthCareProviderFormLink: "Health care provider form",
      intermittentDetails_estimatedAbsences:
        "Estimated <strong>{{frequency}}</strong> absences each lasting <strong>less than a full work day</strong> for <strong>{{duration}}</strong> {{durationBasis}}.",
      intermittentDetails_oncePerMonth: "At least once per month.",
      tableHeader_details: "Details",
      tableHeader_frequency: "Frequency",
      tableName: "Leave schedule details table",
      type_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    },
    noneReported: "None reported",
    notApplicable: "-",
    previousLeaves: {
      detailsLabel: "$t(shared.qualifyingReasonDetailsLabel)",
      explanation:
        "Employees have listed when they took leave for qualifying reasons",
      header: "Past leave",
      qualifyingReasonContent: "Some content here",
      tableFooter_totalLeave: "Total leave",
      tableHeader_dateRange: "Date range",
      tableHeader_days: "Days",
    },
    submitButton: "Submit",
    supportingWorkDetails: {
      header: "Supporting work details",
      hoursWorkedLabel: "Weekly hours worked",
      viewScheduleLink: "View detailed work schedule",
    },
    title: "Review application for {{name}}",
  },
  employersClaimsSuccess: {
    applicationIdLabel: "<strong>Application ID:</strong> {{absenceId}}",
    instructions_benefitsGuide:
      "To learn more about how benefits are calculated, visit our <benefits-guide-link>PFML Benefits Guide</benefits-guide-link>.",
    instructions_emailNotification:
      "Once we’ve made a decision, you’ll receive an email notification with a link to details about the decision.",
    instructions_processingApplication:
      "We’ll begin processing this application and your employee should hear from us within 14 calendar days.",
    title: "Thanks for reviewing the application",
  },
  index: {
    createClaimButton: "Create an application",
    familyLeaveAfterAdoptionBody:
      "You need to provide a statement that confirms the placement and the date of placement. This can come from the child's health care provider, the adoption or foster agency, or the Massachusetts Department of Children and Families.",
    familyLeaveAfterAdoptionHeading:
      "Family leave to bond with your child after adoption or foster placement",
    familyLeaveAfterBirthBodyLine1:
      "You need a document that confirms your child’s date of birth, such as a birth certificate or statement from a health care provider stating your child's birth date.",
    familyLeaveAfterBirthBodyLine2:
      "You can apply before your child is born. You will need to provide proof of birth in order for your application to be approved.",
    familyLeaveAfterBirthHeading:
      "Family leave to bond with your child after birth",
    medicalLeaveBody:
      "Your health care provider must complete the <healthcare-provider-form-link>PFML Health Care Provider Certification</healthcare-provider-form-link>",
    medicalLeaveHeading: "Medical leave due to injury, illness, or pregnancy",
    stepOneHeading:
      "Step one: Tell your employer that you need to take Paid Family and Medical Leave. ",
    stepOneLeadLine1:
      "If you can, tell your employer at least 30 days before your leave begins. If you need to take leave right away, tell your employer as soon as possible.",
    stepOneLeadLine2:
      " Once you tell your employer, you have the right to apply and your job is protected. Keep a record of what date you notified your employer. You will need to provide this date in your leave application.",
    stepThreeHeading: "Step three: Apply",
    stepThreeLead:
      "Applying takes around 15 minutes. Your information will save as you go, so you can finish your application later if you need to.",
    stepTwoHeading:
      "Step two: Get documentation that supports your leave request",
    title: "Get ready to apply",
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
    continueButton: "Agree and continue",
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
  amendmentForm: {
    cancel: "Cancel amendment",
    question_benefitAmount: "How much will they receive each month?",
    question_benefitEndDate: "When will the employee stop using the benefit?",
    question_benefitStartDate:
      "When will the employee start using the benefit?",
    question_leaveEndDate: "When did the leave end?",
    question_leavePeriodDuration:
      "On average, how many hours does the employee work each week?",
    question_leavePeriodDuration_hint:
      "If their schedule varies, tell us the average number of hours worked over the past 52 weeks.",
    question_leaveStartDate: "When did the leave begin?",
    question_notificationDate:
      "When did the employee tell you about their expected leave?",
  },
  applicationCard: {
    feinHeading: "Employer FEIN",
    heading: "Application {{number}}",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
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
        listItems: [
          "PDF documents",
          "Images (.jpg, .jpeg, .png, .tiff, .heic)",
        ],
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
    continueButton: "Save and continue",
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
