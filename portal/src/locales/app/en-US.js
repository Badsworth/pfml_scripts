/**
 *
 * @file US English language file for i18next-based i18n.
 * @see docs/internationalization.md
 *
 */

// When editing this file, be mindful that many of its strings use non-breaking
// hyphen and non-breaking space characters.
// https://alignedonline.com/non%E2%80%91breaking-spaces
const chars = {
  // Non-breaking hyphen characters are used in phone and fax numbers to avoid
  // the numbers awkwardly wrapping to multiple lines.
  nbhyphen: "‑",
  // Non-breaking space characters are used to keep cardinal adjectives on the
  // same line as the nouns they describe or between the last two words of a
  // sentence to prevent line breaks that would cause orphaned words.
  nbsp: " ",
};

const errors = {
  auth: {
    attemptBlocked:
      "Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the contact center at $t(shared.contactCenterPhoneNumber).",
    attemptBlocked_login:
      "Your log in attempt was blocked due to suspicious activity. You will need to reset your password to continue. We've also sent you an email to confirm your identity.",
    attemptsLimitExceeded_forgotPassword:
      "Your account is temporarily locked because of too many forget password requests. Wait 15 minutes before trying again.",
    attemptsLimitExceeded_login:
      "Your account is temporarily locked because of too many failed login attempts. Wait 15 minutes before trying again.",
    codeDeliveryFailure:
      "We encountered an error while sending the verification code. Try again.",
    codeExpired:
      "Sorry, your verification code has expired or has already been used.",
    codeFormat:
      "Enter the 6 digit code sent to your email and ensure it does not include any punctuation.",
    codeMismatchException:
      "Invalid verification code. Make sure the code matches the code emailed to you.",
    codeRequired: "Enter the 6 digit code sent to your email",
    emailRequired: "Enter your email address",
    employerIdNumberRequired: "Enter your employer ID number",
    expiredVerificationCode:
      "Invalid verification code. Please request a new code.",
    incorrectEmailOrPassword: "Incorrect email or password",
    insecurePassword:
      "Choose a different password. Avoid commonly used passwords and avoid using the same password on multiple websites.",
    invalidEmployerIdNumber: "Invalid employer ID number. Please try again.",
    invalidParametersFallback: "Enter all required information",
    invalidParametersIncludingMaybePassword:
      "Check the requirements and try again. Ensure all required information is entered and the password meets the requirements.",
    invalidPhoneFormat: "Invalid phone number",
    passwordErrors:
      "Your password does not meet the requirements. Please check the requirements and try again.",
    passwordRequired: "Enter your password",
    userNotConfirmed:
      "Confirm your account by following the instructions in the verification email sent to your inbox.",
    userNotFound: "Incorrect email",
    usernameExists: "An account with the given email already exists",
  },
  caughtError:
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber).",
  caughtError_DocumentsRequestError: "$t(shared.documentsRequestError)",
  caughtError_ForbiddenError:
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
  caughtError_NetworkError: "$t(shared.networkError)",
  caughtError_NotFoundError:
    "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
  caughtError_UserNotFoundError:
    "Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  claims: {
    date_of_birth: {
      date: "Date of birth must include a valid month, day, and year.",
      invalid_age: "The person taking leave must be at least 14 years old.",
      invalid_year_range: `Date of birth year is not in a valid range (on or after ${
        new Date().getFullYear() - 100
      }).`,
      required: "Enter a date of birth.",
    },
    employer_fein: {
      pattern: "Enter a 9-digit number formatted as XX-XXXXXXX.",
      required: "Enter your employer's Employer Identification Number.",
    },
    employer_notified: {
      required:
        "Select yes if you told your employer that you are taking leave.",
    },
    employment_status: {
      required: "Enter your employment status.",
    },
    first_name: {
      required: "Enter a first name.",
    },
    has_continuous_leave_periods: {
      required: "Select Yes if you are taking continuous leave.",
    },
    has_intermittent_leave_periods: {
      required: "Select Yes if you are taking intermittent leave.",
    },
    has_mailing_address: {
      required: "Please indicate whether you get mail at this address.",
    },
    has_reduced_schedule_leave_periods: {
      required: "Select Yes if you are working a reduced schedule.",
    },
    has_state_id: {
      required:
        "Enter whether or not you have a Massachusetts driver's license or ID.",
    },
    hours_worked_per_week: {
      maximum: "The average hours you work each week must be less than 168.",
      minimum: "The average hours you work each week must be greater than 1.",
      required: "Enter how many hours you work on average each week.",
      type: "The average hours you work each week must be a number.",
    },
    last_name: {
      required: "Enter a last name.",
    },
    leave_details: {
      child_birth_date: {
        date: "Date of birth must include a valid month, day, and year.",
        required: "Enter a date of birth for the child.",
      },
      child_placement_date: {
        date: "Placement date must include a valid month, day, and year.",
        required: "Enter a date of placement for the child.",
      },
      continuous_leave_periods: {
        end_date: {
          date: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter an end date for this continuous leave period.",
        },
        start_date: {
          date: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter a start date for this continuous leave period.",
        },
      },
      employer_notification_date: {
        date: "Notification date must include a valid month, day, and year.",
        required: "Enter the date you notified your employer.",
      },
      employer_notified: {
        required:
          "Select yes if you told your employer that you are taking leave",
      },
      intermittent_leave_periods: {
        duration: {
          required: "Enter a duration.",
        },
        duration_basis: {
          required: "Select a duration option.",
        },
        end_date: {
          date: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter an end date for this intermittent leave period.",
        },
        frequency: {
          required: "Enter a frequency.",
        },
        frequency_interval_basis: {
          required: "Select a frequency option.",
        },
        start_date: {
          date: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter a start date for this intermittent leave period.",
        },
      },
      pregnant_or_recent_birth: {
        required:
          "Select yes if are you taking medical leave because you are pregnant or recently gave birth.",
      },
      reason: {
        required: "Enter a reason for taking time off.",
      },
      reason_qualifier: {
        required: "Enter why you are taking leave.",
      },
      reduced_schedule_leave_periods: {
        end_date: {
          date: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter an end date for this reduced leave period.",
        },
        friday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Friday.",
        },
        monday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Monday.",
        },
        saturday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Saturday.",
        },
        start_date: {
          date: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter a start date for this reduced leave period.",
        },
        sunday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Sunday.",
        },
        thursday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Thursday.",
        },
        tuesday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Tuesday.",
        },
        wednesday_off_minutes: {
          maximum: "$t(shared.maximumReducedLeaveMinutes)",
          minimum: "$t(shared.minimumReducedLeaveMinutes)",
          required: "Enter your hours off for Wednesday.",
        },
      },
    },
    mailing_address: {
      city: {
        required: "Enter a city for your mailing address.",
      },
      line_1: {
        required: "Enter the street address for your mailing address.",
      },
      required: "Enter a mailing address.",
      state: {
        required: "Enter a state for your mailing address.",
      },
      zip: {
        pattern: "Enter a 5- or 9-digit ZIP code for your mailing address.",
        required: "Enter a ZIP code for your mailing address.",
      },
    },
    mass_id: {
      pattern:
        "License or ID number must be 9 characters, and may begin with S or SA.",
      required: "Enter your license or ID number.",
    },
    payment_preferences: {
      account_details: {
        account_number: {
          maxLength:
            "Account number too long: Account number must be 17 digits or fewer.",
          minLength:
            "Account number too short: Account number must be at least 6 digits.",
          required: "Enter an account number.",
        },
        account_type: {
          required: "Enter an account type.",
        },
        routing_number: {
          pattern: "Enter a 9 digit routing number.",
          required: "Enter a routing number.",
        },
      },
    },
    residential_address: {
      city: {
        required: "Enter a city for your residential address.",
      },
      line_1: {
        required: "Enter the street address for your residential address.",
      },
      required: "Enter a residential address.",
      state: {
        required: "Enter a state for your residential address.",
      },
      zip: {
        pattern: "Enter a 5 or 9 digit ZIP code for your residential address.",
        required: "Enter a ZIP code for your residential address.",
      },
    },
    rules: {
      disallow_attempts:
        "We already have an account set up for you. Please sign in with that account. If that doesn't look familiar to you, call the Contact Center at $t(shared.contactCenterPhoneNumber).",
      disallow_hybrid_intermittent_leave:
        "You cannot request intermittent leave in the same application as your continuous or reduced schedule leave. Create a separate application for your intermittent leave dates.",
      disallow_overlapping_leave_periods:
        "Your reduced leave schedule cannot overlap with your continuous leave. Check whether you’ve entered the correct start and end dates for each leave period.",
      disallow_submit_over_60_days_before_start_date:
        "The date your leave begins is more than 60 days in the future. Submit your application within 60 days of your leave start date.",
      min_leave_periods:
        "You must choose at least one kind of leave (continuous, reduced schedule, or intermittent).",
      min_reduced_leave_minutes:
        "The total time entered for your hours off must be greater than 0.",
      require_employer_notified:
        "You must tell your employer that you’re taking leave before you can submit an application. If you’ve told your employer, update your application with the date that you notified them.",
    },
    tax_identifier: {
      pattern: "Enter a 9 digit number formatted as XXX-XX-XXXX.",
      required: "Enter a Social Security Number or ITIN.",
    },
    upload_docs_options: {
      required: "Select the kind of document.",
    },
    work_pattern: {
      work_pattern_days: {
        minimum: "Enter the hours you work.",
        minutes: {
          maximum: "The hours entered are more than possible hours.",
          required: "Enter the hours you work.",
        },
      },
      work_pattern_type: {
        required: "Select a work schedule type.",
      },
    },
  },
  documents: {
    file: {
      required: "Upload at least one file to continue.",
    },
    fineos_client:
      "We encountered an error when uploading your file. Try uploading your file again. If you get this error again, call the Contact Center at $t(shared.contactCenterPhoneNumber).",
  },
  invalidFile_size:
    "We could not upload: {{disallowedFileNames}}. Files must be smaller than 5 megabytes.",
  invalidFile_sizeAndType:
    "We could not upload: {{disallowedFileNames}}. Choose a PDF or image file that is smaller than 5 megabytes.",
  invalidFile_type:
    "We could not upload: {{disallowedFileNames}}. Choose a PDF or image file.",
  network:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
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
  contactCenterAddress:
    "PO Box 838$t(chars.nbsp)Lawrence, MA$t(chars.nbsp)01843",
  contactCenterFaxNumber: "(617)$t(chars.nbsp)855$t(chars.nbhyphen)6180",
  contactCenterPhoneNumber: "(833)$t(chars.nbsp)344$t(chars.nbhyphen)7365",
  day_Friday: "Friday",
  day_Monday: "Monday",
  day_Saturday: "Saturday",
  day_Sunday: "Sunday",
  day_Thursday: "Thursday",
  day_Tuesday: "Tuesday",
  day_Wednesday: "Wednesday",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime: "{{hours}}h {{minutes}}m",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime_noMinutes: "{{hours}}h",
  documentsRequestError:
    "An error was encountered while checking your application for documents. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitFrequency_allAtOnce: "All at once",
  employerBenefitFrequency_daily: "Daily",
  employerBenefitFrequency_monthly: "Monthly",
  employerBenefitFrequency_weekly: "Weekly",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Short-term disability insurance",
  fileUpload_addAnotherFileButton: "Choose another file",
  fileUpload_addFirstFileButton: "Choose a file",
  fileUpload_fileHeadingPrefix: "File",
  filesUploaded: "Number of files uploaded",
  hoursLabel: "Hours",
  leavePeriodMedicalAlert:
    "You will need a completed medical leave certification form for this section.",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Family leave",
  leaveReasonMedical: "Medical leave",
  leaveReasonServiceMemberFamily: "Military family",
  maximumReducedLeaveMinutes:
    "Hours you will take off cannot exceed your work schedule.",
  minimumReducedLeaveMinutes:
    "Reduced leave schedule hours must be 0 or greater.",
  minutesLabel: "Minutes",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  noticeDate: "Posted {{date}}",
  noticeName: "Other notice (PDF)", // it should fallback to this if we receive an unexpected or undefined enum
  noticeName_approvalNotice: "Approval notice (PDF)",
  noticeName_denialNotice: "Denial notice (PDF)",
  noticeName_requestForInfoNotice: "Request for more information (PDF)",
  otherIncomeEntryPrefix: "Income",
  otherIncomeType_jonesAct: "Jones Act benefits",
  otherIncomeType_otherEmployer: "Earnings from another employer",
  otherIncomeType_railroadRetirement: "Railroad Retirement benefits",
  otherIncomeType_retirementDisability:
    "Disability benefits under a governmental retirement$t(chars.nbsp)plan",
  otherIncomeType_selfEmployment: "Earnings from self-employment",
  otherIncomeType_ssdi: "Social Security Disability Insurance",
  otherIncomeType_unemployment: "Unemployment Insurance",
  otherIncomeType_workersCompensation: "Workers Compensation",
  passwordHint:
    "Your password must be at least 12$t(chars.nbsp)characters long and include at least 1$t(chars.nbsp)number, 1$t(chars.nbsp)symbol, and both uppercase and lowercase letters.",
  passwordLabel: "Password",
  paymentMethodAch: "Direct deposit into my bank account",
  paymentMethodCheck: "Paper check",
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
    uploadSuccessHeading: "You successfully submitted your documents",
    uploadSuccessMessage:
      "Our Contact Center staff will review your documents for {{absence_id}}.",
  },
  authCreateAccount: {
    alertBody:
      "<p>You can apply online if you’re currently employed in Massachusetts.</p><p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at $t(shared.contactCenterPhoneNumber).</p><p>Learn more about the <mass-benefits-timeline-link>PFML benefit timeline on mass.gov</mass-benefits-timeline-link>.</p>",
    alertHeading:
      "You can now apply for paid family leave to bond with your$t(chars.nbsp)child.",
    areAnEmployer:
      "<strong>Are you a Massachusetts employer?</strong> <employer-create-account-link>Create an employer account</employer-create-account-link> to manage leave for your team.",
    backButton: "Back to Mass.gov",
    createAccountButton: "Create account",
    haveAnAccountFooterLabel: "Have an account?",
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
    createClaimantAccount:
      "Need to apply for paid leave? <create-account-link>Create an account</create-account-link>",
    createEmployerAccount:
      "Are you a Massachusetts employer? <create-employer-account-link>Create an employer account</create-employer-account-link>",
    forgotPasswordLink: "Forgot your password?",
    loginButton: "Log in",
    passwordLabel: "$t(shared.passwordLabel)",
    sessionTimedOut: "You were logged out due to inactivity",
    sessionTimedOutHeading: "Session timed out",
    title: "Log in to your paid leave account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authResetPassword: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead:
      "If an account exists for the email you provide, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    lead_email:
      "If an account exists for {{emailAddress}}, we emailed a 6 digit verification code to it. Enter the code below to confirm your email and reset your password.",
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
    codeResent:
      "We sent a new 6 digit verification code to your email address. Enter the new code to verify your email.",
    codeResentHeading: "New verification code sent",
    confirmButton: "Submit",
    einLabel: "Employer ID number",
    employerAccountLabel:
      "I need an employer account to manage leave for my team.",
    lead:
      "We sent a 6 digit verification code to your email address. Enter the code to verify your email.",
    lead_email:
      "We sent a 6 digit verification code to {{emailAddress}}. Enter the code to verify your email.",
    logInFooterLink: "$t(shared.backToLoginLink)",
    resendCodeLink: "Send a new code",
    title: "Verify your email address",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  claimsAddress: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasMailingAddressHint:
      "We may send notices to this address. If you choose to get your payments through paper checks, we will mail the checks to this address.",
    hasMailingAddressLabel: "Do you get your mail at this address?",
    hint:
      "We will use this as your residential address for any previous claims you have submitted. If you are part of an Address Confidentiality Program, please provide your substitute address.",
    mailingAddressHint:
      "We will use this as your mailing address for any previous claims you have submitted.",
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
  claimsBondingLeaveAttestation: {
    lead:
      "<p>This paid leave applies to parents of children who have joined their family in the past 12 months via:</p><ul><li>Birth</li><li>Foster placement</li><li>Adoption</li></ul>",
    submitApplicationButton: "I understand and agree",
    title: "Confirm that you are an eligible parent",
    truthAttestation:
      "I agree that I am a new parent by one of the routes above and can provide certification to support this relationship.",
  },
  claimsChecklist: {
    backButtonLabel: "Back to Dashboard",
    completed_editable: "Completed",
    completed_uneditable: "Confirmed",
    documentsRequestError: "$t(shared.documentsRequestError)",
    edit: "Edit",
    partOneSubmittedDescription:
      "Your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you'll need to call our Contact Center at $t(shared.contactCenterPhoneNumber). Now, you can work on Parts 2 and 3, and submit your application.",
    partOneSubmittedHeading: "Part 1 of your application was confirmed.",
    resume: "Resume",
    // Resume button aria-label for screen readers, since VoiceOver reads "résumé":
    resumeScreenReader: "Continue with",
    screenReaderNumberPrefix: "Step",
    start: "Start",
    stepHTMLDescription_bondingAdoptFoster:
      "You need to provide a statement confirming the placement and the date of placement.",
    stepHTMLDescription_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to provide a statement confirming the placement and the date of placement.",
    stepHTMLDescription_bondingNewborn:
      "You need to provide your child's birth certificate or a document from a health care provider that shows the child’s date of birth.",
    stepHTMLDescription_bondingNewbornFuture:
      "After your child is born you will need to provide your child’s birth certificate or a document from a health care provider that shows the child’s date of birth.",
    stepHTMLDescription_employerInformation:
      "You will need to know:<ul><li>Your employer’s 9 digit federal employer identification number (FEIN or EIN). <br><strong>Where to find this: </strong>on your W$t(chars.nbhyphen)2 or 1099, or ask your employer’s finance department.</li><li>The date you told your employer you were taking leave.</li></ul><p>If you are taking leave from multiple employers, you must create separate applications for each job.</p>",
    stepHTMLDescription_leaveDetails:
      "<p>If you are taking medical leave due to injury, illness, or pregnancy, you need to have your health care provider fill out <healthcare-provider-form-link>the certification form</healthcare-provider-form-link>. Some of the answers you will need for the online application will come from your health care provider’s answers on the certification form.</p><p>If you are taking family leave to bond with a child, you will need to know:</p><ul><li>The child's date of birth, due date, or the date they arrived in your home for adoption or foster care.</li><li>When you want your leave to begin and end.</li></ul>",
    stepHTMLDescription_medical:
      "You need to provide your completed <healthcare-provider-form-link>Health Care Provider Certification</healthcare-provider-form-link>. ",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul><li>If you will use any benefits from your employer because you are taking leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any leave you’ve taken since January 1, 2021 for a condition that is covered by Paid Family and Medical Leave.</li></ul>",
    stepHTMLDescription_payment:
      "<p>Tell us how you want to receive payment.</p><p>If you want to receive payment by direct deposit, you will need to provide your bank account information, including a routing number and account number.</p>",
    stepHTMLDescription_reviewAndConfirm:
      "<p>Once you confirm your leave information, we’ll notify your employer. Your job will be protected. To complete your application, you will need to finish steps 6-8 and submit.</p><p>If you need to edit your information in Part 1 after completing this step, you’ll need to call the Contact Center at $t(shared.contactCenterPhoneNumber).</p>",
    stepHTMLDescription_uploadId:
      "Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same ID.",
    stepHTMLDescription_verifyId:
      "<p>You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card.</p><p>You will need to provide:</p><ul><li>Your name as it appears on your ID.</li><li>Your driver’s license number or Mass ID number, if you have one.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListDescription_1:
      "Your progress is automatically saved as you complete the application. You can edit any information you enter in Part 1 until step 5 is completed.",
    stepListDescription_1_submitted:
      "If you need to edit your information in Part 1, you’ll need to call the Contact Center at $t(shared.contactCenterPhoneNumber). Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_2:
      "Entering payment information here leads to faster processing, but you can also call$t(chars.nbsp)$t(shared.contactCenterPhoneNumber).",
    stepListDescription_3:
      "Uploading documents online leads to faster processing, but you can also fax or mail documents. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.",
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
    sectionLabel: "What's your date of birth?",
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
    alertBody:
      "<p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at $t(shared.contactCenterPhoneNumber).</p><p>You can apply online if you’re currently employed in Massachusetts.</p>",
    choiceLabel_employed: "I'm employed in Massachusetts",
    choiceLabel_selfEmployed: "I'm self-employed",
    choiceLabel_unemployed: "I'm unemployed",
    feinHint:
      "This number is 9-digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W$t(chars.nbhyphen)2 or 1099$t(chars.nbhyphen)MISC. Ask your employer if you need help getting this information.",
    feinLabel: "What is your employer's Employer Identification Number (EIN)?",
    furloughAnswer:
      'If your hours have been cut or significantly reduced but you have not been laid off, select "$t(pages.claimsEmploymentStatus.choiceLabel_employed)"',
    furloughQuestion: "What if I've been furloughed?",
    sectionLabel: "What is your employment status?",
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
      "Tell us the estimated frequency and duration of your intermittent$t(chars.nbsp)leave.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodContinuous: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave, tell us when you first missed work and your last day of leave.",
    datesLead_medical:
      'If you have already taken some or all of your leave for this condition, tell us when you first missed work and your last day of leave.<br /><br />Refer to Question 27 in the "Estimate leave details" section of the certification form (page$t(chars.nbsp)6).',
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
    endDateLabel_medical:
      "Last day of leave or re$t(chars.nbhyphen)evaluation date",
    hasLeaveHint_bonding:
      "For example, you need to take time off for: <ul><li>Court dates for your foster child</li><li>Social worker visits</li><li>Gaps in your childcare</li></ul>",
    hasLeaveHint_medical:
      'Refer to Question 31 in the "Estimate leave details" section of the certification form (page 6).',
    hasLeaveLabel:
      "Do you need to take off work in uneven blocks of time (intermittent leave)?",
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
    endDateLabel_medical:
      "Last day of leave or re$t(chars.nbhyphen)evaluation date",
    hasLeaveHint_medical:
      'Refer to Question 28 in the "Estimate leave details" section of the certification form (page 6).',
    hasLeaveLabel:
      "Do you need to work fewer hours than usual for a period of time (reduced leave schedule)?",
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeaveReason: {
    activeDutyFamilyLeaveHint: "Family leave",
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    alertBody:
      "<p>Starting January$t(chars.nbsp)1, 2021, you can also apply for the following paid$t(chars.nbsp)benefits:</p><ul><li>Medical leave to manage your own <mass-benefits-guide-serious-health-condition>serious health$t(chars.nbsp)condition</mass-benefits-guide-serious-health-condition></li><li>Family leave to manage family affairs while a family member is on active duty$t(chars.nbsp)overseas</li><li>Family leave to care for a family member who serves in the armed$t(chars.nbsp)forces</li></ul>",
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
      "Leave is determined based on benefit year (365 days from the first day you take leave), not based on number of children. You have 1 year to take your family leave from the date of the birth/placement of the child (whichever is later). ",
    bondingTypeNewbornLabel: "Birth",
    medicalLeaveHint: "Medical leave",
    medicalLeaveLabel: "I can’t work due to an illness, injury, or pregnancy.",
    sectionHint: "You can only request one leave at a time.",
    sectionLabel: "Why do you need to take leave?",
    serviceMemberFamilyLeaveHint: "Family leave",
    serviceMemberFamilyLeaveLabel:
      "I need to care for a family member who serves in the armed forces.",
    title: "Leave type",
  },
  claimsName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    lead:
      "Fill out your name as it appears on official documents like your driver’s license or W$t(chars.nbhyphen)2.",
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
      "Notify your employer at least 30 days before the start of your leave if$t(chars.nbsp)possible.",
    mustNotifyEmployerWarning:
      "Before you can submit an application, you must tell your employer that you're taking$t(chars.nbsp)leave.",
    sectionLabel:
      "Have you told your employer that you are taking$t(chars.nbsp)leave?",
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
    sectionLabel: "Tell us about your other sources of$t(chars.nbsp)income.",
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
    choiceCheck: "$t(shared.paymentMethodCheck)",
    choiceHintAch:
      "It can take us additional time to set up direct deposit with your bank. Your first payment might be a check sent to the address you listed as your mailing address.",
    choiceHintCheck:
      "You will receive your checks at the address you listed as your mailing address.",
    routingNumberHint:
      "This is the 9-digit number found on the lower left corner of a$t(chars.nbsp)check.",
    routingNumberLabel: "Routing number",
    sectionLabel: "How do you want to get your weekly benefit?",
    sectionLabelHint:
      "You can expect your first payment to arrive about 3 weeks after your leave starts. Your choice will be applied to any previous claims you have submitted.",
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
    pregnancyOrRecentBirthLabel:
      "Are you taking medical leave because you are pregnant or recently gave birth?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsReducedLeaveSchedule: {
    hoursLabel: "$t(shared.hoursLabel)",
    inputHoursLabel_Friday: "$t(shared.day_Friday)",
    inputHoursLabel_Monday: "$t(shared.day_Monday)",
    inputHoursLabel_Saturday: "$t(shared.day_Saturday)",
    inputHoursLabel_Sunday: "$t(shared.day_Sunday)",
    inputHoursLabel_Thursday: "$t(shared.day_Thursday)",
    inputHoursLabel_Tuesday: "$t(shared.day_Tuesday)",
    inputHoursLabel_Wednesday: "$t(shared.day_Wednesday)",
    inputHoursLabel_weekly: "Hours off per week",
    lead_bonding: "You can enter time in 15-minute increments if needed.",
    lead_medical:
      'You can enter time in 15-minute increments if needed.<br /><br />Refer to Question 31 in the "Estimate leave details" section of the certification form (page 8).',
    medicalAlert: "$t(shared.leavePeriodMedicalAlert)",
    minutesLabel: "$t(shared.minutesLabel)",
    sectionLabel:
      "How many hours will you take off while you are on a reduced leave schedule?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
    workScheduleToggle: "View your work schedule",
  },
  claimsReview: {
    achTypeLabel: "Account type",
    achType_checking: "$t(shared.achTypeChecking)",
    achType_savings: "$t(shared.achTypeSavings)",
    childBirthDateLabel: "Child's date of birth",
    childPlacementDateLabel: "Child's placement date",
    documentsRequestError: "$t(shared.documentsRequestError)",
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
    employerFeinLabel: "Employer's EIN",
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
    intermittentFrequencyDurationLabel: "Frequency of intermittent leave",
    intermittentFrequencyDuration_irregularMonths_days:
      "Estimated {{frequency}} absences over the next 6 months, each lasting {{duration}} days.",
    intermittentFrequencyDuration_irregularMonths_hours:
      "Estimated {{frequency}} absences over the next 6 months, each lasting {{duration}} hours.",
    intermittentFrequencyDuration_months_days:
      "Estimated {{frequency}} absences per month, each lasting {{duration}} days.",
    intermittentFrequencyDuration_months_hours:
      "Estimated {{frequency}} absences per month, each lasting {{duration}} hours.",
    intermittentFrequencyDuration_weeks_days:
      "Estimated {{frequency}} absences per week, each lasting {{duration}} days.",
    intermittentFrequencyDuration_weeks_hours:
      "Estimated {{frequency}} absences per week, each lasting {{duration}} hours.",
    leaveDetailsSectionHeading: "$t(shared.leaveDetailsStepTitle)",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "Reduced leave",
    leavePeriodNotSelected: "$t(shared.choiceNo)",
    leaveReasonLabel: "Leave type",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    mailingAddressLabel: "Mailing address",
    numberOfFilesLabel: "$t(shared.filesUploaded)",
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
      "If you need to make edits to Part 1, you’ll need to call our Contact Center at $t(shared.contactCenterPhoneNumber). Your application ID is <strong>{{absence_id}}</strong>",
    partHeadingPrefix: "Part {{number}}",
    partHeading_1_final:
      "Review: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_1_part1:
      "Review and confirm: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_2: "Review: Your payment information",
    partHeading_3: "Review: Upload document",
    partOneNextStepsLine1:
      "Once you review and confirm Part 1, your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at $t(shared.contactCenterPhoneNumber).",
    partOneNextStepsLine2:
      "We’ll also notify your employer that you’ve started an application for paid family and medical leave.",
    partOneNextStepsLine3:
      "Next, you’ll be able to work on Parts 2 and 3, and submit your application.",
    paymentAccountNumLabel: "Account number",
    paymentMethodLabel: "Payment method",
    paymentMethodValue_ach: "$t(shared.paymentMethodAch)",
    paymentMethodValue_check: "$t(shared.paymentMethodCheck)",
    paymentRoutingNumLabel: "Routing number",
    pregnancyOrRecentBirthLabel: "Medical leave for pregnancy or birth",
    pregnancyOrRecentBirth_no: "$t(shared.choiceNo)",
    pregnancyOrRecentBirth_yes: "$t(shared.choiceYes)",
    previousLeaveEntryLabel: "$t(shared.previousLeaveEntryPrefix) {{count}}",
    previousLeaveLabel: "Previous paid or unpaid leave?",
    reducedLeaveScheduleLabel: "Hours off per week",
    reducedLeaveScheduleWeeklyTotal: "$t(shared.displayTime)",
    reducedLeaveScheduleWeeklyTotal_noMinutes:
      "$t(shared.displayTime_noMinutes)",
    residentialAddressLabel: "Residential address",
    stepHeading_employerInformation: "$t(shared.claimsEmploymentInfoTitle)",
    stepHeading_leaveDetails: "$t(shared.claimsLeaveDetailsTitle)",
    stepHeading_otherLeave: "$t(shared.claimsOtherLeaveTitle)",
    stepHeading_payment: "Payment information",
    stepHeading_uploadCertification: "Upload certification document",
    stepHeading_uploadId: "Upload identity document",
    stepHeading_verifyId: "$t(shared.claimsVerifyIdTitle)",
    submitAction_final: "Submit application",
    submitAction_part1: "Submit Part 1",
    submitLoadingMessage: "Submitting… Do not refresh or go back.",
    title:
      "Check your answers before submitting your$t(chars.nbsp)application.",
    userDateOfBirthLabel: "Date of birth",
    userNameLabel: "Name",
    userStateIdLabel: "Driver's License Number",
    userTaxIdLabel: "Social Security Number or ITIN",
    workPatternDaysFixedLabel: "Weekly work hours",
    workPatternDaysVariableLabel: "Average weekly hours",
    workPatternTypeLabel: "Work schedule type",
    workPatternTypeValue_fixed:
      "Each week I work the same number of hours on the same days.",
    workPatternTypeValue_variable:
      "My schedule is not consistent from week to week.",
    workPatternVariableTime: "$t(shared.displayTime)",
    workPatternVariableTime_noMinutes: "$t(shared.displayTime_noMinutes)",
  },
  claimsScheduleFixed: {
    hoursLabel: "$t(shared.hoursLabel)",
    inputHoursHeading: "Tell us your work schedule.",
    inputHoursHeadingHint:
      "Enter the number of hours you work each day. You can enter time in 15-minute increments if needed.",
    inputHoursLabel_Friday: "$t(shared.day_Friday)",
    inputHoursLabel_Monday: "$t(shared.day_Monday)",
    inputHoursLabel_Saturday: "$t(shared.day_Saturday)",
    inputHoursLabel_Sunday: "$t(shared.day_Sunday)",
    inputHoursLabel_Thursday: "$t(shared.day_Thursday)",
    inputHoursLabel_Tuesday: "$t(shared.day_Tuesday)",
    inputHoursLabel_Wednesday: "$t(shared.day_Wednesday)",
    minutesLabel: "$t(shared.minutesLabel)",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsScheduleRotating: {
    choicePatternStartWeek_1: "Week 1",
    choicePatternStartWeek_2: "Week 2",
    choicePatternStartWeek_3: "Week 3",
    choicePatternStartWeek_4: "Week 4",
    hoursLabel: "$t(shared.hoursLabel)",
    inputHoursHeading: "Tell us your work hours.",
    inputHoursHeadingHint:
      "Enter the number of hours you work for each week of your rotating schedule.",
    inputHoursLabel_1: "Week 1",
    inputHoursLabel_2: "Week 2",
    inputHoursLabel_3: "Week 3",
    inputHoursLabel_4: "Week 4",
    minutesLabel: "$t(shared.minutesLabel)",
    scheduleStartDateLabel: "Which week will your leave start during?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsScheduleRotatingNumberWeeks: {
    choice2Weeks: "2",
    choice3Weeks: "3",
    choice4Weeks: "4",
    choiceMoreThan4Weeks: "More than 4",
    howManyWeeksLabel: "How many weekly schedules do you have?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsScheduleVariable: {
    heading: "Help us calculate your weekly hours.",
    hint:
      "We'll confirm your hours with your employer after you submit your application.",
    hoursLabel: "$t(shared.hoursLabel)",
    inputHoursLabel: "Average Weekly Hours",
    lead: "How many hours do you work on average each week?",
    minutesLabel: "$t(shared.minutesLabel)",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsSsn: {
    lead:
      "Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What's your Social Security Number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsStart: {
    explanation:
      "<p>We use this application to determine the leave time and benefit amount you will receive.</p><p>We need true answers to every question so that we can manage the program the way the law requires. You can read more about the requirement to answer truthfully at <mass-consent-agreement-link>Mass.gov</mass-consent-agreement-link>.</p><p>Please confirm that you will answer as truthfully as you can.</p>",
    submitApplicationButton: "I understand and agree",
    title: "Start your application",
    truthAttestation:
      "I understand that I need to give true answers to all questions in order to receive and keep my paid leave benefits and job protections. I understand false answers may forfeit my rights to paid leave and job protections.",
  },
  claimsStateId: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasStateIdLabel: "Do you have a Massachusetts driver's license or ID card?",
    idHint:
      "This may be a 9 digit number or begin with an S or SA followed by numbers for a total of 9 characters.",
    idLabel: "Enter your license or ID number",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsSuccess: {
    adjudicationProcess:
      "<ul> <li>Your employer has 10 days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> </ul>",
    adjudicationProcessHeading: "What happens next",
    adjudicationProcess_bondingAdoptFosterFuture:
      "<ul> <li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of placement, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child arrived in your home earlier or later than expected, you must call the DFML Contact Center at $t(shared.contactCenterPhoneNumber).</li></ul>",
    adjudicationProcess_bondingNewbornFuture:
      "<ul> <li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of birth, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child was born earlier or later than expected, you must call the DFML Contact Center at $t(shared.contactCenterPhoneNumber).</li></ul>",
    adjudicationProcess_medicalPregnantFuture:
      "<ul> <li>Your employer has 10 days to provide feedback on your application.</li> <li>When your leave begins, call the DFML Contact Center at $t(shared.contactCenterPhoneNumber) to tell us. Then we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> </ul>",
    exitLink: "Return to applications",
    familyLeaveToBond:
      "You can take up to 12 weeks of paid family leave to bond with your child after your medical leave ends. You do not need to take this leave all at once. You must create a separate leave application if you want to take family leave.",
    familyLeaveToBondHeading: "You can also apply for paid family leave.",
    medicalLeaveAfterBirth:
      "You can take up to 20 weeks of paid medical leave if you're unable to work during your pregnancy and to recover from childbirth. Your health care provider determines how much medical leave you will need. You'll need to fill out a separate application to take medical leave in addition to your family leave.",
    medicalLeaveAfterBirthHeading:
      "If you gave birth, you may also be eligible for paid medical leave.",
    proofRequired_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to upload, mail, or fax a document that shows your child’s placement date.",
    proofRequired_bondingNewbornFuture:
      "After your child is born, you will need to upload, mail, or fax a document that shows your child’s date of birth.",
    proofRequired_medicalPregnantFuture:
      "You must call the DFML Contact Center at $t(shared.contactCenterPhoneNumber) once your medical leave begins. We can’t approve your application until we hear from you.",
    reportReductionsHeading: "We may need more information from you",
    reportReductionsProcess:
      "<p>Call the Contact Center at $t(shared.contactCenterPhoneNumber) if you'll receive:</p><ul><li>Any benefits from your employer that you’ll be using in addition to Massachusetts paid leave (for example, maternity leave, or paid sick time)</li></ul><ul><li>Income from any other sources during your leave</li></ul>",
    title: "You submitted your leave application",
    title_bonding: "You submitted your family leave application",
    title_medical: "You submitted your medical leave application",
  },
  claimsUploadCertification: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose a file",
    certificationDocumentsCount: "$t(shared.filesUploaded)",
    documentsRequestError: "$t(shared.documentsRequestError)",
    fileHeadingPrefix: "File",
    leadListNewborn: [
      "Your child's birth certificate.",
      "A note from your child's health care provider stating your child's date of birth.",
      "A note from the health care provider of the person who gave birth stating your child's date of birth.",
    ],
    lead_bonding_adopt_foster:
      "<p>It's faster to upload your documents online, but you can fax or mail your documents if you prefer. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.</p><p>You need to upload a statement from your adoption or foster agency or from the Massachusetts Department of Children and Families to confirm the placement and the date of the placement.</p>",
    lead_bonding_newborn:
      "<p>It's faster to upload your documents online, but you can fax or mail your documents if you prefer. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.</p><p>You need to upload one of the following documents to confirm your child’s date of birth:</p>",
    lead_medical:
      "<p>It's faster to upload your documents online, but you can fax or mail your documents if you prefer. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.</p><p>You need to upload a copy of the <healthcare-provider-form-link>PFML Healthcare Provider Form</healthcare-provider-form-link> to prove that you need to take medical leave. You can upload a completed Family and Medical Leave Act (FMLA) form instead if your provider filled$t(chars.nbsp)one$t(chars.nbsp)out.</p>",
    sectionLabel_bonding: "Upload your documentation",
    sectionLabel_medical: "Upload your Healthcare Provider$t(chars.nbsp)form",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsUploadDocsOptions: {
    certLabel_bonding_adopt_foster: "Proof of placement",
    certLabel_bonding_newborn: "Proof of birth",
    certLabel_medical: "Health Care Provider Certification",
    nonStateIdLabel: "Different identification documentation",
    sectionHint:
      "You only need to complete this if you received a notice from the Department of Family and Medical Leave asking you to provide additional documents or you need to provide proof of birth or placement. ",
    sectionLabel: "What kind of document are you uploading?",
    stateIdLabel: "Massachusetts driver's license or ID",
    title: "Additional documentation",
  },
  claimsUploadId: {
    accordionContent:
      "<p><strong>If you don’t have any of those, you can provide one of the following plus proof of your  Social Security Number or Individual Tax Identification Number:</strong></p><ul><li>Valid U.S. State or Territory License or ID</li><li>Certified copy of a birth certificate filed with a State Office of Vital Statistics or equivalent agency in the individual's state of birth. (You can only use a <puerto-rican-birth-certificate-link>Puerto Rican birth certificate</puerto-rican-birth-certificate-link> if it was issued on or after July 1, 2010.)</li><li>Certificate of Citizenship (Form N$t(chars.nbhyphen)560, or Form N$t(chars.nbhyphen)561)</li><li>Certificate of Naturalization (Form N$t(chars.nbhyphen)550 or N$t(chars.nbhyphen)570)</li></ul><p><strong>You can provide proof of your Social Security Number using one of the following documents displaying your complete Social Security Number:</strong></p><ul><li>Social Security card</li><li>W$t(chars.nbhyphen)2 Form</li><li>SSA$t(chars.nbhyphen)1099 Form</li><li>Non$t(chars.nbhyphen)SSA$t(chars.nbhyphen)1099 Form</li><li>Pay stub with your name on it</li></ul><p>Learn more about verifying your identity with different documents at <identity-proof-link>Mass.gov</identity-proof-link>.</p>",
    accordionHeading: "If you don't have any of those documents:",
    addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
    addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
    documentsRequestError: "$t(shared.documentsRequestError)",
    fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
    idDocumentsCount: "$t(shared.filesUploaded)",
    lead_mass:
      "<p>It's faster to upload your documents online, but you can fax or mail your documents if you prefer. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.</p><p>In order to verify your identity, upload a copy of both the front and the back of your ID card.</p>",
    lead_other:
      "<p>It's faster to upload your documents online, but you can fax or mail your documents if you prefer. Follow the instructions on <mail-fax-instructions-link>Mass.gov</mail-fax-instructions-link>.<p>To verify your identity you will need valid documentation issued by state or federal government.</p>",
    otherIdentityDocs:
      "<p><strong>You can use:</strong></p><ul><li>U.S. State or Territory Real ID</li><li>U.S. passport or passport card</li><li>Permanent Resident Card issued by DHS or INS</li><li>Employment Authorization Document (EAD) issued by DHS</li><li>Foreign passport <strong>and</strong> a <work-visa-link>work visa</work-visa-link></li></ul>",
    sectionLabel_mass: "Upload your Massachusetts driver’s license or ID card",
    sectionLabel_other: "Upload an identification document",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsWorkPatternType: {
    choiceHint_fixed:
      "For example, every Monday I work 6 hours, and every Tuesday I work 7 hours.",
    choiceHint_variable:
      "For example, I work 40 hours every week but the days differ, or my schedule changes from week to week.",
    choiceLabel_fixed:
      "Each week I work the same number of hours on the same days.",
    choiceLabel_variable: "My schedule is not consistent from week to week.",
    sectionLabel: "How would you describe your work schedule?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  dashboard: {
    applyByPhone:
      "<p>Apply by calling the Department of Family and Medical Leave Contact Center at $t(shared.contactCenterPhoneNumber) if you meet the following criteria:</p><ul><li>Self-employed or unemployed</li><li>Applying for paid family leave to bond with your child after birth, adoption, or foster$t(chars.nbsp)placement</li></ul>",
    applyByPhoneTitle: "Apply by phone",
    applyMore:
      '<p>More benefits will be available starting January$t(chars.nbsp)1, 2021. Learn more at <a href="https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-timeline#december-2,-2020-">mass.gov</a>.</p>',
    applyOnline:
      "<p>You can apply online if you meet the following criteria:</p><ul><li>Currently employed in$t(chars.nbsp)Massachusetts</li><li>Not self-employed</li><li>Applying for paid family leave to bond with your child after birth, adoption, or foster$t(chars.nbsp)placement</li></ul>",
    applyOnlineTitle: "Apply online",
    createClaimButton: "Create an application",
    familyLeaveAfterAdoptionBody:
      "You need to provide a statement that confirms the placement and the date of placement. This can come from the child's health care provider, the adoption or foster agency, or the Massachusetts Department of Children and Families.",
    familyLeaveAfterAdoptionHeading:
      "Family leave to bond with your child after adoption or foster$t(chars.nbsp)placement",
    familyLeaveAfterBirthBodyLine1:
      "You need a document that confirms your child’s date of birth, such as a birth certificate or statement from a health care provider stating your child's birth date.",
    familyLeaveAfterBirthBodyLine2:
      "You can apply before your child is born. You will need to provide proof of birth in order for your application to be approved.",
    familyLeaveAfterBirthHeading:
      "Family leave to bond with your child after birth",
    medicalLeaveBody:
      "Your health care provider must complete the <healthcare-provider-form-link>PFML Health Care Provider Certification</healthcare-provider-form-link>",
    medicalLeaveHeading: "Medical leave due to injury, illness, or pregnancy",
    multipleApplicationsListIntro:
      "There are some cases where you might need to create multiple leave applications:",
    multipleApplicationsList_intermittent:
      "If you need to take time off at irregular intervals (intermittent leave), you must create an application for the irregular time off you will need. If you also need to take off work completely or work a reduced schedule, you must create a separate application for that time period.",
    multipleApplicationsList_multipleEmployers:
      "If you are taking leave from multiple employers, you must create separate applications for each job.",
    multipleApplicationsList_pregnancy:
      "You can take paid medical leave if you're unable to work during your pregnancy and to recover from childbirth. You can also take paid family leave to bond with your child after your medical leave ends. You must create separate applications for your paid medical leave and family leave.",
    stepOneHeading:
      "Step one: Tell your employer that you need to take Paid Family and Medical Leave. ",
    stepOneLeadLine1:
      "If you can, tell your employer at least 30 days before your leave begins. If you need to take leave right away, tell your employer as soon as possible.",
    stepOneLeadLine2:
      " Once you tell your employer, you have the right to apply and your job is protected. Keep a record of what date you notified your employer. You will need to provide this date in your leave application.",
    stepThreeHeading: "Step three: Create an application",
    stepThreeLead:
      "Applying takes around 15 minutes. Your information will save as you go, so you can finish your application later if you need to.",
    stepTwoHeading:
      "Step two: Get documentation that supports your leave request",
    stepsTitle: "Getting started",
    title: "Only some people can apply online for now",
  },
  employersAuthCreateAccount: {
    createAccountButton: "Create account",
    createClaimantAccount:
      "Need to apply for paid leave? <create-account-link>Create an account</create-account-link>",
    detailsLabel: "What you can do with this account",
    detailsList:
      "<ul><li>Review paid leave applications from your employees</li><li>Get updates about the program by email</li><li>Download documents and decision letters</li></ul>",
    einHint:
      "Your Employer Identification Number (EIN) is a <ein-link>9-digit number</ein-link> assigned by the Internal Revenue Service. It is listed on tax returns and your payroll department should have this information.",
    einLabel: "Employer ID number",
    haveAnAccount: "Have an account? <log-in-link>Log in</log-in-link>",
    lead:
      "Welcome! If you’re a Massachusetts employer and you manage leave for your team, you need to create an employer account with information from your company.",
    nextStep: "We'll send you a 6-digit code to verify your email address.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create an employer account",
    usernameHint: "Use your work email address.",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  employersAuthFinishAccountSetup: {
    lead:
      "Please verify your email address. If an account exists for the email you provide, you’ll receive a 6-digit verification code. After that, you’ll be prompted to create a new password.",
    logInFooterLink: "$t(shared.backToLoginLink)",
    submitButton: "Submit",
    title: "Finish setting up your account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  employersClaimsConfirmation: {
    applicationIdLabel: "<strong>Application ID:</strong> {{absenceId}}",
    instructions:
      "<p>Thanks for letting us know that you’re not the right person to review this.</p><ul><li>Please check with your human resources team and your colleagues to see who should respond.</li><li>If the right person already has an employer account with your company info, you can forward them the email you received so they can respond directly.</li><li>Otherwise, please ask them to call us at $t(shared.contactCenterPhoneNumber).</li></ul>",
    instructions_benefitsGuide:
      "To learn more about how benefits are calculated, visit our <benefits-guide-link>PFML Benefits Guide</benefits-guide-link>.",
    instructions_processingApplication:
      "If we do not hear from anyone at your company before the deadline, we will process the application solely based on the information the employee provided.",
    reviewByLabel: "<div><strong>Review by:</strong> {{employerDueDate}}</div>",
    title: "Help us find the right person to review the application",
  },
  employersClaimsNewApplication: {
    agreementBody:
      "I certify under penalty of perjury that the above information is true and correct. I understand that I need to give true answers to all questions in order to fulfill my responsibilities as a Massachusetts employer.",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    dobLabel: "Date of birth",
    employeeNameLabel: "Employee name",
    employerIdNumberLabel: "Employer ID number",
    instructions:
      "We need true answers to every question so that we can manage this program the way the law requires. Please confirm that you will answer as truthfully as you can.",
    instructionsDueDate: "Review and respond by: <strong>{{date}}</strong>",
    instructionsLabel:
      "Are you the right person to respond to this leave application?",
    submitButton: "Agree and submit",
    title: "New application from {{name}}",
    truthAttestationHeading: "Confirm and submit",
  },
  employersClaimsReview: {
    amend: "Amend",
    documentationLabel: "Documentation",
    durationBasis_days: "{{numOfDays}} days",
    employeeInformation: {
      addressLabel: "Mailing address",
      dobLabel: "Date of birth",
      employeeNameLabel: "Employee name",
      header: "Employee information",
      ssnOrItinLabel:
        "Social Security Number or Individual Taxpayer Identification Number",
    },
    employerBenefits: {
      amountValue_allAtOnce: "{{amount, currency}} all at once",
      amountValue_daily: "{{amount, currency}} per day",
      amountValue_monthly: "{{amount, currency}} per month",
      amountValue_weekly: "{{amount, currency}} per week",
      benefitTypeLabel: "Benefit type",
      dateRangeLabel: "Date range",
      detailsLabel: "Details",
      employerBenefitFrequencyValue_allAtOnce:
        "$t(shared.employerBenefitFrequency_allAtOnce)",
      employerBenefitFrequencyValue_daily:
        "$t(shared.employerBenefitFrequency_daily)",
      employerBenefitFrequencyValue_monthly:
        "$t(shared.employerBenefitFrequency_monthly)",
      employerBenefitFrequencyValue_weekly:
        "$t(shared.employerBenefitFrequency_weekly)",
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
    employerDecision: {
      choiceApprove: "Approve",
      choiceDeny: "Deny",
      heading: "What would be your decision on this leave request?",
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
    fraudReport: {
      alertBody:
        "We take allegations about fraud seriously. Selecting this will begin further investigation. Please only select if you are convinced this is fraudulent. If you have questions, feel free to call us at $t(shared.contactCenterPhoneNumber) from 8am$t(chars.nbhyphen)5pm ET.",
      alertHeading: "You are reporting fraud.",
      choiceNo: "$t(shared.choiceNo)",
      choiceYes: "$t(shared.choiceYes)",
      commentSolicitation: "Please provide a comment below",
      heading: "Do you have any reason to suspect fraud?",
    },
    instructionsAmendment:
      "Please review the details of this application carefully. If anything seems incorrect, you can add an amendment within each section or include general comments at the end.",
    instructionsComment:
      "If you have not been notified of this, please include a comment at the end.",
    instructionsDueDate: "Review and respond by: <strong>{{date}}</strong>",
    leaveDetails: {
      applicationIdLabel: "Application ID",
      header: "Leave details",
      leaveDurationLabel: "Leave duration",
      leaveReasonValue_activeDutyFamily:
        "$t(shared.leaveReasonActiveDutyFamily)",
      leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
      leaveReasonValue_care: "$t(shared.leaveReasonMedical)",
      leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
      leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
      leaveReasonValue_serviceMemberFamily:
        "$t(shared.leaveReasonServiceMemberFamily)",
      leaveTypeLabel: "Leave type",
      natureOfLeaveLabel: "Nature of leave",
    },
    leaveSchedule: {
      frequencyBasis_irregular: "Irregular over the next 6 months",
      frequencyBasis_months: "At least once a month",
      frequencyBasis_weeks: "At least once a week",
      header: "Leave schedule",
      healthCareProviderFormLink: "Health care provider form",
      intermittentFrequencyDuration_irregularMonths_days:
        "Estimated <strong>{{frequency}}</strong> absences over the next 6 months, each lasting <strong>at least a day</strong> for <strong>{{duration}}</strong> days.",
      intermittentFrequencyDuration_irregularMonths_hours:
        "Estimated <strong>{{frequency}}</strong> absences over the next 6 months, each lasting <strong>less than a full work day</strong> for <strong>{{duration}}</strong> hours.",
      intermittentFrequencyDuration_months_days:
        "Estimated <strong>{{frequency}}</strong> absences per month, each lasting <strong>at least a day</strong> for <strong>{{duration}}</strong> days.",
      intermittentFrequencyDuration_months_hours:
        "Estimated <strong>{{frequency}}</strong> absences per month, each lasting <strong>less than a full work day</strong> for <strong>{{duration}}</strong> hours.",
      intermittentFrequencyDuration_weeks_days:
        "Estimated <strong>{{frequency}}</strong> absences per week, each lasting <strong>at least a day</strong> for <strong>{{duration}}</strong> days.",
      intermittentFrequencyDuration_weeks_hours:
        "Estimated <strong>{{frequency}}</strong> absences per week, each lasting <strong>less than a full work day</strong> for <strong>{{duration}}</strong> hours.",
      reducedHoursPerWeek: "Reduced by {{numOfHours}} hours per week",
      tableHeader_dateRange: "Date range",
      tableHeader_details: "Details",
      tableHeader_leaveFrequency: "Leave frequency",
      tableName: "Leave schedule details table",
      type_continuous: "$t(shared.claimDurationTypeContinuous)",
      type_intermittent: "$t(shared.claimDurationTypeIntermittent)",
      type_reducedSchedule: "$t(shared.claimDurationTypeReducedSchedule)",
    },
    noneReported: "None reported",
    notApplicable: "-",
    previousLeaves: {
      detailsLabel: "$t(shared.qualifyingReasonDetailsLabel)",
      explanation:
        "Employees have listed when they took leave for qualifying reasons.",
      header: "Past leave",
      qualifyingReasonContent: "An employee can take paid or unpaid leave to:",
      qualifyingReason_activeDuty:
        "Manage family affairs when a family member is on active duty in the armed forces",
      qualifyingReason_bondWithChild:
        "Bond with a child after birth or placement",
      qualifyingReason_careForFamily:
        "Care for a family member with a serious health condition",
      qualifyingReason_manageHealth: "Manage a serious health condition",
      tableHeader_dateRange: "Date range",
    },
    submitButton: "Submit",
    supportingWorkDetails: {
      header: "Supporting work details",
      hoursWorkedLabel: "Weekly hours worked",
    },
    title: "Review application for {{name}}",
  },
  employersClaimsStatus: {
    applicationIdLabel: "Application ID",
    lead:
      "A decision has been made for this application. No action is required of you, but you can download a copy of the decision notice for details. Your employee has the right to appeal this decision under Massachusetts regulations (<dfml-regulations-link>458 CMR 2.14</dfml-regulations-link>).",
    leaveDetailsLabel: "$t(shared.claimsLeaveDetailsTitle)",
    leaveDurationLabel: "$t(shared.claimsLeaveDurationTitle)",
    leaveReasonLabel: "Leave type",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_care: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    noticeDate: "$t(shared.noticeDate)",
    noticeName: "$t(shared.noticeName)",
    noticeName_approvalNotice: "$t(shared.noticeName_approvalNotice)",
    noticeName_denialNotice: "$t(shared.noticeName_denialNotice)",
    noticeName_requestForInfoNotice:
      "$t(shared.noticeName_requestForInfoNotice)",
    noticesLabel: "Notices",
    statusLabel: "Status",
    title: "Notices for {{name}}",
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
  employersDashboard: {
    checkEmailBody:
      "When an employee applies for leave, you’ll receive email updates about their application status and any steps you need to take. We’ll include everyone who has an employer account with your company in case you’re out of the office.",
    checkEmailTitle: "Check your email regularly",
    learnMoreLinks:
      "<ul><li><mass-employer-role-link>Your role as a Massachusetts employer</mass-employer-role-link></li><li><reimbursements-link>Employer reimbursements</reimbursements-link></li><li><employer-pfml-guide-link>Employer's guide to Paid Family and Medical Leave (PFML)</employer-pfml-guide-link></li></ul>",
    learnMoreTitle: "Learn more",
    respondBody:
      "When an application is submitted, you have 10 business days to open the direct link from your email and review it online. You can comment on the application, approve or deny it, and report fraud if needed. Reviewing takes about 10 minutes. If we don’t hear from anyone at your company before the deadline, we’ll process the application solely based on the information the employee provided.",
    respondTitle: "Respond to applications within 10 business days",
    viewFormsBody:
      "You’ll get an email about our application decision with a direct link to download the letter your employee received. For medical leave, you can download the Certification of a serious health condition form during the review process.",
    viewFormsTitle: "View forms and notices online",
    welcomeBody:
      "Thanks for joining the paid leave program. There’s no further action for you to take now, but you’ll be able to review applications online starting December 15, 2020.",
    welcomeTitle: "Welcome",
  },
  index: {
    claimantCardBody:
      "You can now create an account and apply for Paid Family and Medical Leave.",
    claimantCardBodyPrelaunch:
      "Later this month, you can create an account to apply for Paid Family and Medical Leave. Learn more about the <mass-benefits-timeline-link>PFML benefit timeline on mass.gov</mass-benefits-timeline-link>.",
    claimantCreateAccountButton: "Create an account",
    claimantHeading: "Workers",
    createAccountHeading: "Create an account",
    employerCardBody: "Register now so you can manage leave for your team.",
    employerCardBody_prelaunch:
      "Register now so your team is ready for December 15, 2020, when workers can start requesting leave.",
    employerCreateAccountButton: "Create an employer account",
    employerHeading: "Employers",
    seoTitle: "Massachusetts Paid Family and Medical Leave",
    title:
      "Massachusetts workers can now apply for Paid Family and Medical Leave. Learn more about this <mass-paid-leave-link>new paid leave program</mass-paid-leave-link>.",
    title_prelaunch:
      "Massachusetts employers: Register now so you can manage leave for your team.",
  },
  userConsentToDataSharing: {
    agreementBody:
      "By continuing, I am indicating that I have read and understood the above user agreements. I give the Department of Family and Medical Leave permission to collect, share, and use my information consistent with the terms of the agreements linked$t(chars.nbsp)above.",
    applicationUsage: "",
    applicationUsageHeading_employer: "Reviewing paid leave applications",
    applicationUsageHeading_user: "Applying for PFML",
    applicationUsageIntro: "We need this information to:",
    applicationUsageList_employer: [
      "Check eligibility for coverage",
      "Determine your employee’s benefit amount",
      "Administer the program and meet reporting requirements",
      "Give you the best service possible",
    ],
    applicationUsageList_user: [
      "Check your eligibility for coverage",
      "Determine your benefit amount",
      "Give you the best service possible",
    ],
    continueButton: "Agree and continue",
    dataUsageBody_employer:
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to a claim with health care providers and contracted private partners.",
    dataUsageBody_user:
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to your claim with your employer, health care provider(s), and contracted private partners.",
    dataUsageHeading: "How we use your data",
    fullUserAgreementBody:
      "To find out more about how the Commonwealth might use the information you share with the Department of Family and Medical Leave, please read the <informed-consent-link>DFML Informed Consent Agreement</informed-consent-link> and the <privacy-policy-link>Privacy Policy for Mass.gov</privacy-policy-link>.",
    fullUserAgreementHeading: "Full user agreements",
    intro:
      "The information you provide on this website will be used to administer the Paid Family and Medical Leave (PFML) program.",
    title: "How this website uses your information",
  },
};

const components = {
  amendmentForm: {
    cancel: "Cancel amendment",
    question_benefitAmount: "How much will they receive?",
    question_benefitEndDate: "When will the employee stop using the benefit?",
    question_benefitFrequency: "How often will they receive the benefit?",
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
    bondingLeaveDocsRequired_adopt_foster:
      "Once your child arrives, submit proof of placement so that we can make a decision.",
    bondingLeaveDocsRequired_newborn:
      "Once your child is born, submit proof of birth so that we can make a decision.",
    documentsRequestError: "$t(shared.documentsRequestError)",
    feinHeading: "Employer EIN",
    heading: "Application {{number}}",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    noticeDate: "$t(shared.noticeDate)",
    noticeName: "$t(shared.noticeName)",
    noticeName_approvalNotice: "$t(shared.noticeName_approvalNotice)",
    noticeName_denialNotice: "$t(shared.noticeName_denialNotice)",
    noticeName_requestForInfoNotice:
      "$t(shared.noticeName_requestForInfoNotice)",
    noticesHeading: "View your notices",
    resumeClaimButton: "Complete your application",
    uploadDocsButton: "Upload additional documents",
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
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
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
    removalWarning: "You can't remove files previously uploaded.",
    removeButton: "Remove file",
    uploadDate: "Date of upload: {{date}}",
  },
  fileUploadDetails: {
    label: "Some tips for uploading documents and images",
    sizeNotice:
      "Files should be 5 MB or smaller. If your file is larger than 5 MB, try resizing it or splitting it into separate files.",
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
    logoTitle: "Go to PFML homepage",
    orgAddress: "PO Box 838 Lawrence, MA 01843",
    orgName: "Department of Family and Medical Leave (DFML)",
    orgPhoneNumber: "$t(shared.contactCenterPhoneNumber)",
    title: "Paid Family and Medical Leave (PFML)",
  },
  form: {
    continueButton: "Save and continue",
    dateInputDayLabel: "Day",
    dateInputExample: "mm / dd / yyyy",
    dateInputMonthLabel: "Month",
    dateInputYearLabel: "Year",
    optional: "(optional)",
  },
  header: {
    skipToContent: "Skip to main content",
    appTitle: "Paid Family and Medical Leave",
  },
  signUp: {
    createAccountButton: "Create an account to apply for paid leave",
    haveAnAccountFooterLabel: "Have an account?",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    signInFooterLink: "Log in",
    title: "Create an account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  siteLogo: {
    dfmlAlt: "Department of Family and Medical Leave logo",
    pfmlAlt: "Paid Family and Medical Leave program logo",
    sealAlt: "Massachusetts state seal",
  },
  spinner: {
    label: "Loading",
  },
  tag: {
    state_approved: "Approved",
  },
  userFeedback: {
    instructions:
      "We'd like to hear more about your experience on this site. Please take a few minutes to share your feedback.",
    surveyLink: "<user-feedback-link>Take the survey</user-feedback-link>",
    title: "Help us improve this site",
  },
  weeklyTimeTable: {
    dayAbbr_Friday: "Fri",
    dayAbbr_Monday: "Mon",
    dayAbbr_Saturday: "Sat",
    dayAbbr_Sunday: "Sun",
    dayAbbr_Thursday: "Thur",
    dayAbbr_Tuesday: "Tues",
    dayAbbr_Wednesday: "Wed",
    time: "$t(shared.displayTime)",
    time_noMinutes: "$t(shared.displayTime_noMinutes)",
  },
  withClaims: {
    loadingLabel: "Loading claims",
  },
  withUser: {
    loadingLabel: "Loading account",
  },
};

const englishLocale = {
  translation: Object.assign({}, { chars, components, errors, pages, shared }),
};

export default englishLocale;
