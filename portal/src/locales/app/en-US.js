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
    attemptBlocked_forgotPassword:
      "Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the contact center at $t(shared.contactCenterPhoneNumber).",
    attemptBlocked_login:
      "Your log in attempt was blocked due to suspicious activity. You will need to reset your password to continue. We’ve also sent you an email to confirm your identity.",
    attemptsLimitExceeded_forgotPassword:
      "Your account is temporarily locked because of too many forget password requests. Wait 15 minutes before trying again.",
    attemptsLimitExceeded_login:
      "Your account is temporarily locked because of too many failed login attempts. Wait 15 minutes before trying again.",
    code: {
      deliveryFailure:
        "We encountered an error while sending the verification code. Try again.",
      expired:
        "Sorry, your verification code has expired or has already been used.",
      mismatchException:
        "Invalid verification code. Make sure the code matches the code emailed to you.",
      pattern:
        "Enter the 6 digit code sent to your email and ensure it does not include any punctuation.",
      required: "Enter the 6 digit code sent to your email",
    },
    // TODO (CP-1768) Remove these auth.ein strings once requests flow through API
    ein: {
      invalid: "Invalid employer ID number. Please try again.",
      required: "Enter your 9-digit Employer Identification Number.",
    },
    expiredVerificationCode:
      "Invalid verification code. Please request a new code.",
    incorrectEmailOrPassword: "Incorrect email or password",
    invalidParametersFallback: "Enter all required information",
    invalidParametersIncludingMaybePassword:
      "Check the requirements and try again. Ensure all required information is entered and the password meets the requirements.",
    invalidPhoneFormat: "Invalid phone number",
    isEmployer: {
      required:
        "Select Yes if you are you creating an employer account to manage leave for your company.",
    },
    password: {
      insecure: "$t(shared.auth.passwordError_insecure)",
      invalid: "$t(shared.auth.passwordError_invalid)",
      required: "$t(shared.auth.passwordError_required)",
      resetRequiredException:
        'Your password must be reset before you can log in again. Click the "Forgot your password?" link below to reset your password.',
    },
    userNotConfirmed:
      "Confirm your account by following the instructions in the verification email sent to your inbox.",
    userNotFound: "Incorrect email",
    username: {
      exists: "$t(shared.auth.emailError_exists)",
      required: "$t(shared.auth.emailError_required)",
    },
  },
  caughtError:
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber).",
  caughtError_DocumentsLoadError: "$t(shared.documentsLoadError)",
  caughtError_DocumentsUploadError: "$t(shared.documentsUploadError)",
  caughtError_ForbiddenError:
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
  caughtError_NetworkError: "$t(shared.networkError)",
  caughtError_NotFoundError:
    "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
  caughtError_UserNotReceivedError:
    "Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  claims: {
    date_of_birth: {
      format: "Your date of birth must include a valid month, day, and year.",
      invalid_age: "The person taking leave must be at least 14 years old.",
      invalid_year_range: "Your date of birth must include a valid year.",
      required: "Enter your date of birth.",
    },
    employer_benefits: {
      benefit_amount_dollars: {
        required:
          "Enter the amount you will receive, or remove how often you will receive that amount.",
      },
      benefit_amount_frequency: {
        required: "Enter how often you will receive this amount.",
      },
      benefit_end_date: {
        format:
          "Date you stop receiving this benefit must include a valid month, day, and year.",
        invalid_date_range:
          "Date you stop using this benefit must be on or after the date you start using this benefit.",
        minimum: "Benefit end date must be after December 31, 2020",
        required: "Enter the date you will stop using this benefit.",
      },
      benefit_start_date: {
        format:
          "Date you start receiving this benefit must include a valid month, day, and year.",
        minimum: "Benefit start date must be after December 31, 2020",
        required: "Enter the date you will start using this benefit.",
      },
      benefit_type: {
        required: "Select the kind of benefit you will use.",
      },
    },
    employer_fein: {
      pattern:
        "Enter the Employer Identification Number in the correct format.",
      require_contributing_employer:
        "Enter a valid Employer Identification Number (EIN). Check that you entered your employer’s EIN correctly. You can find this number on all notices your employer sent about Paid Family and Medical Leave, or on your W‑2 or 1099‑MISC. If you continue to get this error, contact your employer and confirm that you have the correct EIN, and that they are contributing to Paid Family and Medical Leave.",
      required: "Enter your employer’s Employer Identification Number.",
    },
    employer_notified: {
      required:
        "Select yes if you told your employer that you are taking leave.",
    },
    employment_status: {
      required: "Enter your employment status.",
    },
    fineos_case_creation_issues:
      "We couldn’t find you in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, <mass-gov-form-link>follow these instructions</mass-gov-form-link> and we’ll set up your application through our Contact Center.",
    fineos_case_error:
      "There was a problem when trying to send your information to our system. Try submitting this information again.",
    first_name: {
      required: "Enter a first name.",
    },
    has_continuous_leave_periods: {
      required: "Select Yes if you are taking continuous leave.",
    },
    has_employer_benefits: {
      required:
        "Select yes if you will you use any employer-sponsored benefits during your leave.",
    },
    has_intermittent_leave_periods: {
      required: "Select Yes if you are taking intermittent leave.",
    },
    has_mailing_address: {
      required: "Select yes if you get your mail at this address.",
    },
    has_other_incomes: {
      required:
        "Select yes if you will receive income from any other sources during your leave.",
    },
    has_reduced_schedule_leave_periods: {
      required: "Select Yes if you are working a reduced schedule.",
    },
    has_state_id: {
      required:
        "Select yes if you have a Massachusetts driver’s license or ID card.",
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
      caring_leave_metadata: {
        family_member_date_of_birth: {
          format:
            "Your family member’s date of birth must include a valid month, day, and year.",
          invalid_year_range:
            "Your family member’s date of birth must include a valid year.",
          required: "Enter your family member’s date of birth.",
        },
        family_member_first_name: {
          required: "Enter your family member's first name.",
        },
        family_member_last_name: {
          required: "Enter your family member's last name.",
        },
        relationship_to_caregiver: {
          required:
            "Select your relationship with the family member you are caring for.",
        },
      },
      child_birth_date: {
        format: "Date of birth must include a valid month, day, and year.",
        required: "Enter your child’s date of birth or due date.",
      },
      child_placement_date: {
        format: "Placement date must include a valid month, day, and year.",
        required: "Enter the date your child arrived in your home.",
      },
      continuous_leave_periods: {
        end_date: {
          format: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter the last day of your continuous leave.",
        },
        start_date: {
          format: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter the first day of your continuous leave.",
        },
      },
      employer_notification_date: {
        format:
          "Date you notified your employer must include a valid month, day, and year.",
        minimum:
          "Year you notified your employer must be within the past two years.",
        required: "Enter the date you notified your employer.",
      },
      employer_notified: {
        required:
          "Select yes if you told your employer that you are taking leave",
      },
      intermittent_leave_periods: {
        duration: {
          days_absent_per_intermittent_interval_maximum:
            "The total amount of time you may be absent is greater than the length of the frequency interval you have selected. Check the frequency and duration.",
          intermittent_duration_hours_maximum:
            "An absence should be 23 hours or fewer. For absences that are 24 hours or longer, select that the absence will last at least a full day.",
          required: "Enter how long each absence may last.",
        },
        duration_basis: {
          required:
            "Select if absences may last at least a day or less than a full workday.",
        },
        end_date: {
          format: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter the last day of your intermittent leave.",
        },
        frequency: {
          required: "Enter how often absences may occur.",
        },
        frequency_interval_basis: {
          intermittent_interval_maximum:
            "Sorry, our intermittent leave request service is a work in progress. Use our <intermittent-leave-guide>step-by-step guide to intermittent leave</intermittent-leave-guide> to complete your application. You can also complete your application by calling our Contact Center at $t(shared.contactCenterPhoneNumber).",
          required: "Select how often absences may occur.",
        },
        start_date: {
          format: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter the first day of your intermittent leave.",
        },
      },
      pregnant_or_recent_birth: {
        required:
          "Select yes if are you taking medical leave because you are pregnant or recently gave birth.",
      },
      reason: {
        required: "Select the reason for taking paid leave.",
      },
      reason_qualifier: {
        required:
          "Select the reason for taking family leave to bond with a child.",
      },
      reduced_schedule_leave_periods: {
        end_date: {
          format: "End date must include a valid month, day, and year.",
          minimum:
            "Last day of leave must be on or after the first day of leave.",
          required: "Enter the last day of your reduced leave schedule.",
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
          format: "Start date must include a valid month, day, and year.",
          minimum:
            "Paid Family and Medical Leave cannot be taken before Jan 1, 2021. Enter a date after December$t(chars.nbsp)31,$t(chars.nbsp)2020.",
          required: "Enter the first day of your reduced leave schedule.",
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
        invalid_masked_field: "Enter the full ZIP code to make a change.",
        pattern: "Mailing address ZIP code must be 5 or 9 digits.",
        required: "Enter a ZIP code for your mailing address.",
      },
    },
    mass_id: {
      pattern:
        "License or ID number must be 9 characters, and may begin with S or SA.",
      required: "Enter your license or ID number.",
    },
    other_incomes: {
      income_amount_dollars: {
        required:
          "Enter the amount you will receive, or remove how often you will receive that amount.",
      },
      income_amount_frequency: {
        required: "Enter how often you will receive this amount.",
      },
      income_end_date: {
        format:
          "Date you stop receiving this income must include a valid month, day, and year.",
        invalid_date_range:
          "Date you stop receiving this income must be on or after the date you start receiving this income.",
        minimum: "Income end date must be after December 31, 2020",
        required: "Enter the date you will stop receiving this income.",
      },
      income_start_date: {
        format:
          "Date you start receiving this income must include a valid month, day, and year.",
        minimum: "Income start date must be after December 31, 2020",
        required: "Enter the date you will start receiving this income.",
      },
      income_type: {
        required: "Select the kind of income.",
      },
    },
    payment_preference: {
      account_number: {
        invalid_masked_field: "Enter the full account number to make a change.",
        maxLength: "Account number must be 17 digits or fewer.",
        minLength: "Account number must be at least 6 digits.",
        required: "Enter an account number.",
      },
      bank_account_type: {
        required: "Select if this is a savings or checking account.",
      },
      payment_method: {
        required: "Select how you want to get your weekly benefit.",
      },
      routing_number: {
        pattern: "Enter your routing number in the correct format.",
        required: "Enter a routing number.",
      },
    },
    phone: {
      phone_number: {
        invalid_masked_field: "Enter the full phone number to make a change.",
        invalid_phone_number:
          "That phone number is invalid. Check the number and try again.",
        pattern: "Enter your 10 digit phone number, with the area code first.",
        required: "Enter a phone number.",
      },
      phone_type: {
        required: "Select a number type.",
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
        invalid_masked_field: "Enter the full ZIP code to make a change.",
        pattern: "Residential address ZIP code must be 5 or 9 digits.",
        required: "Enter a ZIP code for your residential address.",
      },
    },
    rules: {
      disallow_12mo_continuous_leave_period:
        "$t(shared.disallow12moLeavePeriod)",
      disallow_12mo_intermittent_leave_period:
        "$t(shared.disallow12moLeavePeriod)",
      disallow_12mo_leave_period: "$t(shared.disallow12moLeavePeriod)",
      disallow_12mo_reduced_leave_period: "$t(shared.disallow12moLeavePeriod)",
      disallow_attempts:
        "We already have an account set up for you. Please sign in with that account. If that doesn’t sound familiar to you, call the Contact Center at $t(shared.contactCenterPhoneNumber).",
      disallow_hybrid_intermittent_leave:
        "You cannot request intermittent leave in the same application as your continuous or reduced schedule leave. Create a separate application for your intermittent leave dates.",
      disallow_overlapping_leave_periods:
        "Your reduced leave schedule cannot overlap with your continuous or intermittent leave. Check whether you’ve entered the correct start and end dates for each leave period.",
      disallow_submit_over_60_days_before_start_date:
        "The date your leave begins is more than 60 days in the future. Submit your application within 60 days of your leave start date.",
      min_leave_periods:
        "You must choose at least one kind of leave (continuous, reduced schedule, or intermittent).",
      min_reduced_leave_minutes:
        "The total time entered for your hours off must be greater than 0.",
      require_employee:
        "We couldn’t find you in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, call the Contact Center at $t(shared.contactCenterPhoneNumber).",
      require_employer_notified:
        "You must tell your employer that you’re taking leave before you can submit an application. If you’ve told your employer, update your application with the date that you notified them.",
    },
    tax_identifier: {
      invalid_masked_field:
        "Enter the full Social Security Number or ITIN to make a change.",
      pattern: "Your Social Security Number or ITIN must be 9 digits.",
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
        required: "Select your work schedule.",
      },
    },
  },
  documents: {
    file: {
      required: "Upload at least one file to continue.",
    },
    fineos_client: "$t(shared.documentsUploadError)",
  },
  employers: {
    ein: {
      employer_verification_data_required:
        "$t(shared.ein.employer_verification_data_required)",
    },
    employer_benefits: {
      benefit_end_date: {
        format: "End date must include a valid month, day, and year.",
        minimum:
          "Last day of benefit must be on or after the first day of benefit.",
      },
      benefit_start_date: {
        format: "Start date must include a valid month, day, and year.",
      },
    },
    employer_fein: {
      duplicate:
        "The employer ID you entered is already associated with your account.",
      employer_verification_data_required:
        "$t(shared.ein.employer_verification_data_required)",
      invalid:
        "Enter your 9-digit Employer Identification Number in the correct format.",
    },
    hours_worked_per_week: {
      // TODO (EMPLOYER-723) remove this
      invalid_hours_worked_per_week:
        "Average weekly hours must be 168 or fewer.",
      maximum: "Average weekly hours must be 168 or fewer.",
      minimum: "Enter the average weekly hours.",
    },
    outstanding_information_request_required:
      "This application has already been reviewed.",
    unauthorized_leave_admin:
      "Sorry, you do not have permission to view that page. To access it, you need to <add-org-link>add that organization</add-org-link> to your account.",
    withholding_amount: {
      incorrect: "The amount does not match our records. Please try again.",
    },
  },
  invalidFile_size:
    "We could not upload: {{disallowedFileNames}}. Files must be smaller than 4.5 MB.",
  invalidFile_sizeAndType:
    "We could not upload: {{disallowedFileNames}}. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than 4.5 MB.",
  invalidFile_type:
    "We could not upload: {{disallowedFileNames}}. Choose a PDF or an image file (.jpg, .jpeg, .png).",
  network:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  users: {
    email_address: {
      exists: "$t(shared.auth.emailError_exists)",
      format: "Enter a valid email address",
      required: "$t(shared.auth.emailError_required)",
    },
    password: {
      insecure: "$t(shared.auth.passwordError_insecure)",
      invalid: "$t(shared.auth.passwordError_invalid)",
      required: "$t(shared.auth.passwordError_required)",
    },
    user_leave_administrator: {
      employer_fein: {
        pattern:
          "Enter your 9-digit Employer Identification Number in the correct format.",
        require_contributing_employer:
          "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly and the associated business is contributing to Paid Family and Medical Leave.",
        require_employer:
          "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly.",
        required: "Enter your 9-digit Employer Identification Number.",
      },
    },
  },
  // These fallbacks shouldn't normally render, but they may if a validation rule or
  // field is introduced and we don't add a custom field-level error message for it.
  validationFallback: {
    invalid: "Field ({{field}}) has invalid value.",
    invalid_masked_field: "Re-enter the full value to make a change.",
    // Field's value didn't match an expected regex pattern:
    pattern: "Field ({{field}}) didn’t match expected format.",
  },
};

const shared = {
  absenceCaseStatus_approved: "Approved",
  absenceCaseStatus_closed: "Closed",
  absenceCaseStatus_denied: "Denied",
  achTypeChecking: "Checking",
  achTypeSavings: "Savings",
  amountFrequency_daily: "Daily",
  amountFrequency_inTotal: "All at once",
  amountFrequency_monthly: "Monthly",
  amountFrequency_unknown: "Unknown",
  amountFrequency_weekly: "Weekly",
  amountPerFrequency_daily: "{{amount, currency}} per day",
  amountPerFrequency_inTotal: "{{amount, currency}} all at once",
  amountPerFrequency_monthly: "{{amount, currency}} per month",
  amountPerFrequency_unknown: "{{amount, currency}} (frequency unknown)",
  amountPerFrequency_weekly: "{{amount, currency}} per week",
  auth: {
    emailError_exists: "An account with the given email already exists",
    emailError_required: "Enter your email address",
    passwordError_insecure:
      "Choose a different password. Avoid commonly used passwords and avoid using the same password on multiple websites.",
    passwordError_invalid:
      "Your password does not meet the requirements. Please check the requirements and try again.",
    passwordError_required: "Enter your password",
  },
  backToLoginLink: "Back to log in",
  bondingRegsLeavePeriodDetailsLabel:
    "Do you work in an acute care hospital or the teaching hospital of the University of Massachusetts Medical School?",
  bondingRegsLeavePeriodDetailsSummary:
    "If you had a child join your family in 2020, you may be eligible for paid leave anytime in 2021. <emergency-bonding-regs-worker-link>Learn more about emergency Covid-19 regulations for hospital workers.</emergency-bonding-regs-worker-link>",
  caregiverCertificationForm: "Certification to Care for a Family Member",
  choiceNo: "No",
  choicePendingOtherIncomes:
    "I’ve applied for another benefit that hasn’t been approved$t(chars.nbsp)yet.",
  choiceYes: "Yes",
  claimDurationTypeContinuous: "Continuous leave",
  claimDurationTypeIntermittent: "Intermittent leave",
  claimDurationTypeReducedSchedule: "Reduced leave schedule",
  claimsEmploymentInfoTitle: "Employment information",
  claimsLeaveDetailsTitle: "Leave details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsOtherLeaveTitle: "Other leave, benefits, and income",
  claimsVerifyIdTitle: "Your identification",
  contactCenterAddress:
    "PO Box 838$t(chars.nbsp)Lawrence, MA$t(chars.nbsp)01842",
  contactCenterFaxNumber: "(617)$t(chars.nbsp)855$t(chars.nbhyphen)6180",
  contactCenterPhoneNumber: "(833)$t(chars.nbsp)344$t(chars.nbhyphen)7365",
  day_Friday: "Friday",
  day_Monday: "Monday",
  day_Saturday: "Saturday",
  day_Sunday: "Sunday",
  day_Thursday: "Thursday",
  day_Tuesday: "Tuesday",
  day_Wednesday: "Wednesday",
  departmentOfRevenuePhoneNumber:
    "(617)$t(chars.nbsp)466$t(chars.nbhyphen)3950",
  disallow12moLeavePeriod: "Your leave cannot be 12 months or more.",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime: "{{hours}}h {{minutes}}m",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime_noMinutes: "{{hours}}h",
  documentsLoadError:
    "An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>",
  documentsUploadError:
    "We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at $t(shared.contactCenterPhoneNumber).",
  ein: {
    employer_verification_data_required:
      "Your account can’t be verified yet, because your organization has not made any paid leave contributions. Once this organization pays quarterly taxes, you can verify your account and review applications. <file-a-return-link>Learn more about filing returns and remitting contributions</file-a-return-link>.",
  },
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Short-term disability insurance",
  employerInstructions_addComment:
    "If something is incomplete, add a comment at the end of the page.",
  employerInstructions_followUpDate:
    "<strong>Review and respond by:</strong> {{date}} at 11:59 p.m. Eastern time",
  fileUpload_addAnotherFileButton: "Choose another file",
  fileUpload_addFirstFileButton: "Choose files",
  fileUpload_fileHeadingPrefix: "File",
  filesUploaded: "Number of files uploaded",
  hoursLabel: "Hours",
  leavePeriodCaringAlert:
    "You will need a completed $t(shared.caregiverCertificationForm) for this section.",
  leavePeriodMedicalAlert:
    "You will need a completed Certification of a Serious Health Condition form for this section.",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Bond with a child",
  leaveReasonCare: "Care for a family member",
  leaveReasonMedical: "Medical leave",
  leaveReasonServiceMemberFamily: "Military family",
  maximumReducedLeaveMinutes:
    "Hours you will take off cannot exceed your work schedule.",
  minimumReducedLeaveMinutes:
    "Reduced leave schedule hours must be 0 or greater.",
  minutesLabel: "Minutes",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
  noneReported: "None reported",
  noticeDate: "Posted {{date}}",
  noticeName: "Other notice", // it should fallback to this if we receive an unexpected or undefined enum
  noticeName_approvalNotice: "Approval notice",
  noticeName_denialNotice: "Denial notice",
  noticeName_pdf: "Other notice $t(shared.pdfNoticeSuffix)", // it should fallback to this if we receive an unexpected or undefined enum
  noticeName_pdf_approvalNotice: "Approval notice $t(shared.pdfNoticeSuffix)",
  noticeName_pdf_denialNotice: "Denial notice $t(shared.pdfNoticeSuffix)",
  noticeName_pdf_requestForInfoNotice:
    "Request for more information $t(shared.pdfNoticeSuffix)",
  noticeName_requestForInfoNotice: "Request for more information",
  otherIncomeEntryPrefix: "Income",
  otherIncomeType_jonesAct: "Jones Act benefits",
  otherIncomeType_otherEmployer:
    "Earnings or benefits from another employer, or through self-employment",
  otherIncomeType_railroadRetirement: "Railroad Retirement benefits",
  otherIncomeType_retirementDisability:
    "Disability benefits under a governmental retirement$t(chars.nbsp)plan",
  otherIncomeType_ssdi: "Social Security Disability Insurance",
  otherIncomeType_unemployment: "Unemployment Insurance",
  otherIncomeType_workersCompensation: "Workers Compensation",
  passwordHint:
    "Your password must be at least 12$t(chars.nbsp)characters long and include at least 1$t(chars.nbsp)number, 1$t(chars.nbsp)symbol, and both uppercase and lowercase letters.",
  passwordLabel: "Password",
  paymentMethodAch: "Direct deposit into my bank account",
  paymentMethodCheck: "Paper check",
  pdfNoticeSuffix: "(PDF)",
  previousLeaveEntryPrefix: "Previous leave",
  qualifyingReasonDetailsLabel: "What counts as a qualifying reason?",
  resendVerificationCodeLink: "Resend the code",
  siteDescription:
    "Paid Family and Medical Leave is a state-offered benefit for anyone who works in Massachusetts and is eligible to take up to 26 weeks of paid leave for medical or family reasons.",
  submitApplicationButton: "I understand and agree",
  usernameLabel: "Email address",
  verificationCodeLabel: "6-digit code",
};

const pages = {
  app: {
    seoDescription: "$t(shared.siteDescription)",
  },
  applications: {
    claimsReflectPortal:
      "Your applications only reflect what you entered using this website. Any changes you made through the Contact Center will not be shown here.",
    createApplicationHeading: "Create a new application",
    getReadyLink: "Start a new application",
    inProgressHeading: "In-progress applications",
    noClaims: "You don’t have any applications yet.",
    submittedHeading: "Submitted applications",
    title: "Applications",
    uploadSuccessHeading: "You successfully submitted your documents",
    uploadSuccessMessage:
      "Our Contact Center staff will review your documents for {{absence_id}}.",
  },
  authCreateAccount: {
    alertBody:
      "<p>You can apply online if you’re currently employed in Massachusetts.</p><p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p><p><mass-benefits-timeline-link>Learn more about the paid leave benefit timeline.</mass-benefits-timeline-link></p>",
    alertHeading: "You can now apply for paid family and medical leave.",
    areAnEmployer:
      "<strong>Are you a Massachusetts employer?</strong> <employer-create-account-link>Create an employer account</employer-create-account-link> to manage leave for your team.",
    backButton: "Back to Mass.gov",
    createAccountButton: "Create account",
    createEmployerAccount:
      "<strong>Are you a Massachusetts employer?</strong> Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> to create an employer account.",
    haveAnAccountFooterLabel: "Have an account?",
    logInFooterLink: "Log in",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create an account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authForgotPassword: {
    backToLoginLink: "$t(shared.backToLoginLink)",
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead:
      "If an account exists for the email you provide, we will email a 6-digit verification code to it.",
    submitButton: "Send code",
    title: "Forgot your password?",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authLogin: {
    accountVerified:
      "Thanks for verifying your email address. You may now log into your account.",
    accountVerifiedHeading: "Email successfully verified",
    createClaimantAccount:
      "<strong>Need to apply for paid leave? <create-account-link>Create an account</create-account-link></strong>",
    createEmployerAccount:
      "<strong>Are you a Massachusetts employer? <create-employer-account-link>Create an employer account</create-employer-account-link></strong>",
    createEmployerAccount_contactCallCenter:
      "<strong>Are you a Massachusetts employer?</strong> Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> to create an employer account.",
    forgotPasswordLink: "Forgot your password?",
    loginButton: "Log in",
    passwordLabel: "$t(shared.passwordLabel)",
    sessionTimedOut: "You were logged out due to inactivity",
    sessionTimedOutHeading: "Session timed out",
    title: "Log in to your paid leave account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authResetPassword: {
    backToLoginLink: "$t(shared.backToLoginLink)",
    codeLabel: "$t(shared.verificationCodeLabel)",
    codeResent:
      "We sent a new 6 digit verification code to your email address. Enter the new code to reset your password.",
    codeResentHeading: "New verification code sent",
    einLabel: "Employer ID number (EIN)",
    employerAccountLabel:
      "Are you creating an employer account to manage leave for your company?",
    employerChoiceNo: "$t(shared.choiceNo)",
    employerChoiceYes: "$t(shared.choiceYes)",
    lead:
      "If an account exists for the email you provide, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    lead_email:
      "If an account exists for {{emailAddress}}, we emailed a 6 digit verification code to it. Enter the code below to confirm your email and reset your password.",
    lead_userNotFound:
      "Our system timed out, so we need you to verify your account again. Enter your email address to receive a new verification code. Then create a new password.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    submitButton: "Set new password",
    title: "Create a new password",
    title_userNotFound: "Verify your account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authVerifyAccount: {
    backToLoginLink: "$t(shared.backToLoginLink)",
    codeLabel: "$t(shared.verificationCodeLabel)",
    codeResent:
      "We sent a new 6-digit verification code to your email address. Enter the new code to verify your email.",
    codeResentHeading: "New verification code sent",
    confirmButton: "Submit",
    einLabel: "Employer ID number (EIN)",
    employerAccountLabel:
      "Are you creating an employer account to manage leave for your company?",
    employerChoiceNo: "$t(shared.choiceNo)",
    employerChoiceYes: "$t(shared.choiceYes)",
    lead:
      "We sent a 6-digit verification code to your email address. Enter the code to verify your email.",
    lead_email:
      "We sent a 6 digit verification code to {{emailAddress}}. Enter the code to verify your email.",
    resendCodeLink: "Send a new code",
    title: "Verify your email address",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  claimsAddress: {
    choiceNo: "No, I would like to add a mailing address",
    choiceYes: "$t(shared.choiceYes)",
    hasMailingAddressHint:
      "We may send notices to this address. If you choose to get your payments through paper checks, we will mail the checks to this address.",
    hasMailingAddressLabel: "Do you get your mail at this address?",
    hint:
      "We will use this as your residential address for any previous applications you have submitted. If you are part of an Address Confidentiality Program, please provide your substitute address.",
    mailingAddressHint:
      "We will use this as your mailing address for any previous applications you have submitted.",
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
    submitApplicationButton: "$t(shared.submitApplicationButton)",
    title: "Confirm that you are an eligible parent",
    truthAttestation:
      "I agree that I am a new parent by one of the routes listed and can provide certification to support this relationship.",
  },
  claimsCaringLeaveAttestation: {
    lead:
      "This paid leave applies to caregivers with an <eligible-relationship-link>eligible family relationship</eligible-relationship-link>.",
    submitApplicationButton: "$t(shared.submitApplicationButton)",
    title: "Confirm that you are an eligible caregiver",
    truthAttestation_child:
      "I agree that I have an eligible relationship with my child who is experiencing a serious health condition and needs my care.",
    truthAttestation_grandchild:
      "I agree that I have an eligible relationship with my grandchild who is experiencing a serious health condition and needs my care.",
    truthAttestation_grandparent:
      "I agree that I have an eligible relationship with my grandparent who is experiencing a serious health condition and needs my care.",
    truthAttestation_inlaw:
      "I agree that I have an eligible relationship with a parent of my spouse or domestic partner who is experiencing a serious health condition and needs my care.",
    truthAttestation_parent:
      "I agree that I have an eligible relationship with my parent who is experiencing a serious health condition and needs my care.",
    truthAttestation_sibling:
      "I agree that I have an eligible relationship with my sibling who is experiencing a serious health condition and needs my care.",
    truthAttestation_spouse:
      "I agree that I have an eligible relationship with my spouse or domestic partner who is experiencing a serious health condition and needs my care.",
  },
  claimsChecklist: {
    backButtonLabel: "Back to applications",
    completed_editable: "Completed",
    completed_uneditable: "Confirmed",
    documentsLoadError: "$t(shared.documentsLoadError)",
    edit: "Edit",
    partOneSubmittedDescription:
      "Your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>. Now, you can work on Parts 2 and 3, and submit your application.",
    partOneSubmittedHeading: "Part 1 of your application was confirmed.",
    partTwoSubmittedDescription:
      "Now, you can work on Part 3, and submit your application.",
    partTwoSubmittedHeading: "Part 2 of your application was confirmed.",
    resume: "Resume",
    // Resume button aria-label for screen readers, since VoiceOver reads "résumé":
    resumeScreenReader: "Continue with",
    screenReaderNumberPrefix: "Step",
    start: "Start",
    stepHTMLDescription_bondingAdoptFoster:
      "<p>You need to provide a statement confirming the placement and the date of placement.</p><p>Your certification documents will be shared with your employer as part of your application.</p>",
    stepHTMLDescription_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to provide a statement confirming the placement and the date of placement.",
    stepHTMLDescription_bondingNewborn:
      "<p>You need to provide your child’s birth certificate or a document from a health care provider that shows the child’s date of birth.</p><p>Your certification documents will be shared with your employer as part of your application.</p>",
    stepHTMLDescription_bondingNewbornFuture:
      "After your child is born you will need to provide your child’s birth certificate or a document from a health care provider that shows the child’s date of birth.",
    stepHTMLDescription_care:
      "<p>You need to provide your completed <caregiver-certification-form-link>$t(shared.caregiverCertificationForm)</caregiver-certification-form-link>.</p><p>Your certification documents will be shared with your employer as part of your leave application.</p>",
    stepHTMLDescription_employerInformation:
      "You will need to know:<ul><li>Your employer’s 9 digit federal employer identification number (FEIN or EIN). <br><strong>Where to find this: </strong>on your W$t(chars.nbhyphen)2 or 1099, or ask your employer’s finance department.</li><li>The date you told your employer you were taking leave.</li></ul><p>If you are taking leave from multiple employers, you must create separate applications for each job.</p>",
    stepHTMLDescription_leaveDetails:
      "<strong>Are you taking medical leave?</strong><p>You need to have a completed <healthcare-provider-form-link>Certification of a Serious Health Condition</healthcare-provider-form-link>. Use your health care provider’s answers on the certification form to fill out some parts of the application.</p><p><strong>Are you taking leave to bond with a child?</strong></p><p>You need to know the child’s date of birth, due date, or the date they arrived in your home for adoption or foster care.</p><p>You also need to know when you want your leave to begin and end.</p>",
    // TODO (CP-1983) Merge leaveDetails and leaveDetailsWithCaring when showCaringLeave feature flag is not needed
    stepHTMLDescription_leaveDetailsWithCaring:
      "<strong>Are you taking medical leave?</strong><p>You need to have a completed <healthcare-provider-form-link>Certification of a Serious Health Condition</healthcare-provider-form-link>. Use your health care provider’s answers on the certification form to fill out some parts of the application.</p><p><strong>Are you taking leave to bond with a child?</strong></p><p>You need to know the child’s date of birth, due date, or the date they arrived in your home for adoption or foster care.</p><p>You also need to know when you want your leave to begin and end.</p><p><strong>Are you taking leave to care for a family member?</strong></p><p>You need to have the <caregiver-certification-form-link>$t(shared.caregiverCertificationForm)</caregiver-certification-form-link> completed by their health care provider. You will need to use the health care provider’s answers on the certification form to fill out some parts of the application.</p><p>You also need to be sure of the <caregiver-relationship-link>eligibility of your relationship<caregiver-relationship-link/>.</p>",
    stepHTMLDescription_medical:
      "<p>You need to provide your completed <healthcare-provider-form-link>Certification of a Serious Health Condition</healthcare-provider-form-link>.</p><p>Your certification documents will be shared with your employer as part of your leave application.</p>",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul><li>If you will use any benefits from your employer because you are taking leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any leave you’ve taken since January 1, 2021 for a condition that is covered by Paid Family and Medical Leave.</li></ul>",
    stepHTMLDescription_payment:
      "<p>Tell us how you want to receive payment.</p><p>If you want to receive payment by direct deposit, you will need to provide your bank account information, including a routing number and account number.</p>",
    stepHTMLDescription_reviewAndConfirm:
      "<p>Once you confirm your leave information, we’ll notify your employer. Your job will be protected. To complete your application, you will need to finish the following three steps and submit.</p><p>If you need to edit your information in Part 1 after completing this step, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p>",
    stepHTMLDescription_uploadId:
      "<p>Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same$t(chars.nbsp)ID.</p><p>For other IDs, follow the instructions for acceptable proof of identity on the upload page.</p>",
    stepHTMLDescription_verifyId:
      "<p>You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card.</p><p>You will need to provide:</p><ul><li>Your name as it appears on your ID.</li><li>Your driver’s license number or Mass ID number, if you have one.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListDescription_1:
      "Your progress is automatically saved as you complete the application. You can edit any information you enter in Part 1 until step 5 is completed.",
    stepListDescription_1_submitted:
      "If you need to edit your information in Part 1, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_2:
      "Entering payment information here leads to faster processing, but you can also call$t(chars.nbsp)<contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.",
    stepListDescription_2_submitted:
      "If you need to edit your information in Part 2, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_3:
      "Uploading documents online leads to faster processing, but you can also <mail-fax-instructions-link>fax or mail documents</mail-fax-instructions-link>.",
    stepListTitlePrefix: "Part {{number}}",
    stepListTitle_1: "Tell us about yourself and your leave",
    stepListTitle_2: "Enter your payment information",
    stepListTitle_3: "Upload your documents",
    stepTitle_employerInformation: "Enter employment information",
    stepTitle_leaveDetails: "Enter leave details",
    stepTitle_otherLeave: "Report other leave, benefits, and income",
    stepTitle_payment: "Add payment information",
    stepTitle_reviewAndConfirm: "Review and confirm",
    stepTitle_uploadCertification: "Upload leave certification documents",
    stepTitle_uploadId: "Upload identification document",
    stepTitle_verifyId: "Verify your identification",
    submitButton: "Review and submit application",
    title: "Checklist: Create a new application",
  },
  claimsConcurrentLeaves: {
    sectionLabel:
      "Will you use any employer-sponsored accrued paid leave during your PFML leave?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsConcurrentLeavesDetails: {
    sectionLabel:
      "Will you use accrued paid leave from this employer? EIN: {{employer_fein, ein}}",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsConcurrentLeavesIntro: {
    sectionLabel:
      "Tell us about the accrued paid leave you'll use during your PFML leave.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsDateOfBirth: {
    sectionLabel: "What’s your date of birth?",
    title: "$t(shared.claimsVerifyIdTitle)",
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
      "Will you use any employer-sponsored benefits from this employer during your PFML leave?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsEmployerBenefitsDetails: {
    addButton: "Add another benefit",
    amountFrequencyLabel: "Frequency",
    amountFrequency_daily: "$t(shared.amountFrequency_daily)",
    amountFrequency_inTotal: "$t(shared.amountFrequency_inTotal)",
    amountFrequency_monthly: "$t(shared.amountFrequency_monthly)",
    amountFrequency_unknown: "$t(shared.amountFrequency_unknown)",
    amountFrequency_weekly: "$t(shared.amountFrequency_weekly)",
    amountLabel: "Amount",
    amountLegend: "How much will you receive?",
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
    limitMessage: "You can only add up to 3 benefits",
    removeButton: "Remove benefit",
    sectionLabel:
      "Tell us about employer-sponsored benefits you will use during your leave dates for paid leave.",
    startDateLabel: "When will you start using the benefit?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeLabel: "What kind of benefit is it?",
  },
  claimsEmploymentStatus: {
    alertBody:
      "<p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p><p>You can apply online if you’re currently employed in Massachusetts.</p>",
    choiceLabel_employed: "I’m employed in Massachusetts",
    choiceLabel_selfEmployed: "I’m self-employed",
    choiceLabel_unemployed: "I’m unemployed",
    feinHint:
      "This number is 9 digits. You can find this number on all notices your employer sent about Paid Family and Medical Leave. You can also find it on your W$t(chars.nbhyphen)2 or 1099$t(chars.nbhyphen)MISC. Ask your employer if you need help getting this information.",
    feinLabel: "What is your employer’s Employer Identification Number (EIN)?",
    furloughAnswer:
      'If your hours have been cut or significantly reduced but you have not been laid off, select "$t(pages.claimsEmploymentStatus.choiceLabel_employed)"',
    furloughQuestion: "What if I’ve been furloughed?",
    sectionLabel: "What is your employment status?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsFamilyMemberDateOfBirth: {
    sectionLabel: "What is your family member's date of birth?",
  },
  claimsFamilyMemberName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    middleNameLabel: "Middle name",
    sectionHint:
      "Fill out their name as it appears on official documents like their driver’s license or W‑2.",
    sectionLabel: "What is your family member's name?",
  },
  claimsFamilyMemberRelationship: {
    choiceLabel_child: "I am caring for my child.",
    choiceLabel_grandchild: "I am caring for my grandchild.",
    choiceLabel_grandparent: "I am caring for my grandparent.",
    choiceLabel_inlaw:
      "I am caring for a parent of my spouse or domestic partner.",
    choiceLabel_parent: "I am caring for my parent.",
    choiceLabel_sibling: "I am caring for my sibling.",
    choiceLabel_spouse: "I am caring for my spouse or domestic partner.",
    sectionHint: "Learn more about which relationships are covered.",
    sectionLabel:
      "What is your relationship with the family member you are caring for?",
  },
  claimsIntermittentFrequency: {
    durationBasisChoice_days: "At least a day",
    durationBasisChoice_hours: "Less than a full work day",
    durationBasisLabel: "How long will an absence typically last?",
    durationLabel_days: "How many days of work will you miss per absence?",
    durationLabel_hours: "How many hours of work will you miss per absence?",
    frequencyBasisChoice_irregular: "Irregular over the next 6 months",
    frequencyBasisChoice_months: "At least once a month",
    frequencyBasisChoice_weeks: "At least once a week",
    frequencyBasisLabel:
      "How often might you need to be absent from work (frequency interval)?",
    frequencyHint_care:
      "Your answers must match Questions # and # in the completed $t(shared.caregiverCertificationForm).",
    frequencyHint_medical:
      "Your answers must match Questions 35 and 36 in the Certification of a Serious Health Condition form.",
    frequencyLabel_irregular:
      "Estimate how many absences over the next 6 months.",
    frequencyLabel_months: "Estimate how many absences per month.",
    frequencyLabel_weeks: "Estimate how many absences per week.",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    sectionLabel:
      "Tell us the estimated frequency and duration of your intermittent$t(chars.nbsp)leave.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodContinuous: {
    bondingRegsDetailsLabel: "$t(shared.bondingRegsLeavePeriodDetailsLabel)",
    bondingRegsDetailsSummary:
      "$t(shared.bondingRegsLeavePeriodDetailsSummary)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question # of the $t(shared.caregiverCertificationForm).",
    datesLead_medical:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 29 in the Certification of a Serious Health Condition form.",
    datesSectionLabel:
      "Enter the start and end dates for your continuous leave.",
    endDateLabel: "Last day of leave",
    hasLeaveHint_care:
      "Your answer must match Question # in the completed $t(shared.caregiverCertificationForm).",
    hasLeaveHint_medical:
      "Your answer must match Question 26 in the Certification of a Serious Health Condition form.",
    hasLeaveLabel:
      "Do you need to take off work completely for a period of time (continuous leave)?",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodIntermittent: {
    bondingRegsDetailsLabel: "$t(shared.bondingRegsLeavePeriodDetailsLabel)",
    bondingRegsDetailsSummary:
      "$t(shared.bondingRegsLeavePeriodDetailsSummary)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question # of the $t(shared.caregiverCertificationForm).",
    datesLead_medical:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 34 in the Certification of a Serious Health Condition form.",
    datesSectionLabel:
      "Enter the start and end dates for your intermittent leave.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical:
      "Last day of leave or re$t(chars.nbhyphen)evaluation date",
    hasLeaveHint_bonding:
      "For example, you need to take time off for: <ul><li>Court dates for your foster child</li><li>Social worker visits</li><li>Gaps in your childcare</li></ul>",
    hasLeaveHint_care:
      "Your answer must match Question # in the completed $t(shared.caregiverCertificationForm).",
    hasLeaveHint_medical:
      "Your answer must match Question 26 in the Certification of a Serious Health Condition form.",
    hasLeaveLabel:
      "Do you need to take off work in uneven blocks of time (intermittent leave)?",
    hybridLeaveWarning:
      "You have to create a separate application for intermittent leave.",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodReducedSchedule: {
    bondingRegsDetailsLabel: "$t(shared.bondingRegsLeavePeriodDetailsLabel)",
    bondingRegsDetailsSummary:
      "$t(shared.bondingRegsLeavePeriodDetailsSummary)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question # of the $t(shared.caregiverCertificationForm).",
    datesLead_medical:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 32 in the Certification of a Serious Health Condition form .",
    datesSectionLabel:
      "Enter the start and end dates for your reduced leave schedule.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical:
      "Last day of leave or re$t(chars.nbhyphen)evaluation date",
    hasLeaveHint_care:
      "Your answer must match Question # in the completed $t(shared.caregiverCertificationForm).",
    hasLeaveHint_medical:
      "Your answer must match Question 26 in the Certification of a Serious Health Condition form.",
    hasLeaveLabel:
      "Do you need to work fewer hours than usual for a period of time (reduced leave schedule)?",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeaveReason: {
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    alertBody:
      "<p>To apply for the following paid benefits:</p><ul><li>Paid family leave to care for a family member who serves in the armed forces</li><li>Paid family leave to manage family affairs when a family member is on active duty in the armed forces</li></ul><p>Call the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p>",
    bondingLeaveLabel:
      "I need to bond with my child after birth, adoption, or foster placement.",
    bondingTypeAdoptionLabel: "Adoption",
    bondingTypeFosterLabel: "Foster placement",
    bondingTypeLabel:
      "Will you take leave for a birth, an adoption, or a foster placement?",
    bondingTypeMultipleBirthsDetailsLabel:
      "What if I’ve had multiple births or placements within one year?",
    bondingTypeMultipleBirthsDetailsSummary:
      "Leave is determined based on benefit year (365 days from the start of the first week you take leave), not based on number of children. You have 1 year to take your family leave from the date of the birth/placement of the child. <multiple-births-link>Learn more about taking leave for multiple childbirths or placements</multiple-births-link>.",
    bondingTypeNewbornLabel: "Birth",
    caringLeaveLabel: "I need to care for my family member",
    medicalLeaveLabel: "I can’t work due to an illness, injury, or pregnancy.",
    sectionHint: "You can only request one leave at a time.",
    sectionLabel: "Why do you need to take leave?",
    serviceMemberFamilyLeaveLabel:
      "I need to care for a family member who serves in the armed forces.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    lead:
      "Fill out your name as it appears on official documents like your driver’s license or W$t(chars.nbhyphen)2.",
    middleNameLabel: "Middle name",
    sectionLabel: "What’s your name?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsNotifiedEmployer: {
    bondingRegsEmployerNotifiedDetailsLabel:
      "Do you work in an acute care hospital or the teaching hospital of the University of Massachusetts Medical School?",
    bondingRegsEmployerNotifiedDetailsSummary:
      "If so, and you had a child join your family in 2020, you may be eligible for paid leave anytime in 2021. You must get approval from your employer by no later than March 21, 2021 and apply for benefits with the Department of Paid Family and Medical Leave not more than 60 days before your anticipated delayed start date. <emergency-bonding-regs-worker-link>Learn more about emergency Covid-19 regulations for hospital workers</emergency-bonding-regs-worker-link>.",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    employerNotificationDateHint: "This can be an approximate date.",
    employerNotificationLabel: "When did you tell them?",
    mustNotifyEmployerWarning:
      "You can continue to enter information about your leave. Before you can submit your application, you must tell your employer that you’re taking$t(chars.nbsp)leave. Notify your employer at least 30 days before the start of your leave if possible.",
    sectionLabel:
      "Have you told your employer that you are taking$t(chars.nbsp)leave?",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsOtherIncomes: {
    choiceNo: "$t(shared.choiceNo)",
    choicePendingOtherIncomes: "$t(shared.choicePendingOtherIncomes)",
    choiceYes: "$t(shared.choiceYes)",
    hintHeader: "Other sources of income you must report are:",
    hintList: [
      "Workers Compensation",
      "Unemployment Insurance",
      "Social Security Disability Insurance",
      "Disability benefits under a governmental retirement plan such as STRS or PERS",
      "Jones Act benefits",
      "Railroad Retirement benefits",
      "Earnings or benefits from another employer, or through self-employment",
    ],
    sectionLabel:
      "Will you receive income from any other sources during your leave dates for paid$t(chars.nbsp)leave?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsOtherIncomesDetails: {
    addButton: "Add another income",
    amountFrequencyLabel: "Frequency",
    amountFrequency_daily: "$t(shared.amountFrequency_daily)",
    amountFrequency_inTotal: "$t(shared.amountFrequency_inTotal)",
    amountFrequency_monthly: "$t(shared.amountFrequency_monthly)",
    amountFrequency_weekly: "$t(shared.amountFrequency_weekly)",
    amountLabel: "Amount",
    amountLegend: "How much will you receive?",
    cardHeadingPrefix: "$t(shared.otherIncomeEntryPrefix)",
    endDateLabel:
      "What is the last day of your leave that this income will pay you for?",
    limitMessage: "You can only add up to 3 incomes",
    removeButton: "Remove income",
    sectionLabel:
      "Tell us about your other sources of income$t(chars.nbsp)during your leave dates for paid$t(chars.nbsp)leave.",
    startDateLabel:
      "What is the first day of your leave that this income will pay you for?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeChoiceLabel_jonesAct: "$t(shared.otherIncomeType_jonesAct)",
    typeChoiceLabel_otherEmployer: "$t(shared.otherIncomeType_otherEmployer)",
    typeChoiceLabel_railroadRetirement:
      "$t(shared.otherIncomeType_railroadRetirement)",
    typeChoiceLabel_retirementDisability:
      "$t(shared.otherIncomeType_retirementDisability)",
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
    partTwoNextSteps:
      "<p>Once you submit Part 2, your payment information will be viewable by our Contact Center staff. To make edits to Part 2, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p><p>Next, you’ll work on Part 3, and submit your application.</p>",
    routingNumberHint:
      "This is the 9-digit number found on the lower left corner of a check or deposit slip.",
    routingNumberLabel: "Routing number",
    sectionLabel: "How do you want to get your weekly benefit?",
    sectionLabelHint:
      "Your choice will be applied to any previous applications you have submitted.",
    submitPart2Button: "Submit Part 2",
    title: "Payment method",
    whenWillIGetPaidDetails:
      "<p>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started.</p><p>If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts.</p><p>After that, you will receive your payments every week.</p>",
    whenWillIGetPaidLabel: "When will I get paid?",
  },
  claimsPhoneNumber: {
    choiceCell: "Mobile",
    choicePhone: "Landline",
    lead:
      "If we need to contact you, we will reach out by phone or mail. We will also use this number for any previous applications you have submitted.",
    phoneNumberHint:
      "Don’t have a personal phone number? Enter a number where we might be able to reach you (for example, a work phone number, or a friend’s phone number).",
    phoneNumberLabel: "Phone number",
    phoneTypeLabel: "Number type",
    sectionLabel: "What’s your phone number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsPreviousLeavesIntro: {
    sectionLabel: "Tell us about your previous leave.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesOtherReason: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    detailsLabel: "What counts as a qualifying reason?",
    hintHeader:
      "Answer yes if you took paid or unpaid leave for a qualifying reason that is not the reason you are applying for paid leave now. The following are qualifying reasons:",
    hintList: [
      "You had a serious health condition, including illness, injury, or pregnancy.",
      "If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care.",
      "You bonded with your child after birth or placement.",
      "You needed to manage family affairs while a family member is on active duty in the armed forces.",
      "You needed to care for a family member who serves in the armed forces.",
      "You needed to care for a family member with a serious health condition.",
    ],
    sectionLabel:
      "Did you take leave between January 1, 2021–{{leaveStartDate}} for a different qualifying reason?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesOtherReasonDetails: {
    addButton: "Add another leave",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hoursLabel: "$t(shared.hoursLabel)",
    isForCurrentEmployerHint:
      "This is the same Employer Identification Number you entered earlier in your application. After you submit your application, we'll give this employer a chance to review information from your application. We won't share any information about leave you took from other employers.",
    isForCurrentEmployerLabel:
      "Did you take leave from this employer? EIN:$t(chars.nbsp){{employer_fein, ein}}",
    leaveEndDateLabel: "What was the last day of this leave?",
    leaveMinutesHint:
      "Add up all the hours you took off between the first and last day of this leave and enter the total. For example, if you took off 8 hours in one week and 12 hours in another, you should enter 20 hours.",
    leaveMinutesLabel: "What was the total number of hours you took off?",
    leaveReasonChoice_activeDutyFamily:
      "Managing family affairs while a family member was on active duty in the armed forces",
    leaveReasonChoice_bonding: "Bonding with my child after birth or placement",
    leaveReasonChoice_care: "Caring for a family member",
    leaveReasonChoice_medical: "An illness or injury",
    leaveReasonChoice_pregnancy: "Pregnancy",
    leaveReasonChoice_serviceMemberFamily:
      "Caring for a family member who served in the armed forces",
    leaveReasonHint:
      "If you didn’t take leave for one of these reasons, go back to the previous screen and select No.",
    leaveReasonLabel: "Why did you need to take this leave?",
    leaveStartDateLabel: "What was the first day of this leave?",
    limitMessage: "You can only add up to {{limit}} leaves",
    minutesLabel: "$t(shared.minutesLabel)",
    previousLeaveEntryPrefix: "$t(shared.previousLeaveEntryPrefix)",
    removeButton: "Remove leave",
    sectionLabel: "Tell us about your previous time off",
    title: "$t(shared.claimsOtherLeaveTitle)",
    workedPerWeekMinutesHint:
      "Enter the number of hours you would have worked each week, if you were not on leave. If your weekly schedule was not consistent, enter the average number of hours you would have worked per week. For example, if your leave was across two different weeks, and your normal work schedule was 40 hours in one week and 20 hours in the next, you should enter 30 hours.",
    workedPerWeekMinutesLabel:
      "How many hours would you have worked per week if you did not take this leave?",
  },
  claimsPreviousLeavesSameReason: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    sectionLabel:
      "Did you take any other leave between January 1, 2021–{{leaveStartDate}} for the same reason as you are applying for paid leave now?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesSameReasonDetails: {
    sectionLabel: "Tell us about your previous time off",
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
    inputHoursLabel_Friday: "Friday time off",
    inputHoursLabel_Monday: "Monday time off",
    inputHoursLabel_Saturday: "Saturday time off",
    inputHoursLabel_Sunday: "Sunday time off",
    inputHoursLabel_Thursday: "Thursday time off",
    inputHoursLabel_Tuesday: "Tuesday time off",
    inputHoursLabel_Wednesday: "Wednesday time off",
    inputHoursLabel_weekly: "Hours off per week",
    lead_bonding: "Enter 0 for days you won’t work a reduced schedule.",
    lead_care:
      "Enter 0 for days you won’t work a reduced schedule.<br /><br />Your answer must match Question # in the $t(shared.caregiverCertificationForm).",
    lead_medical:
      "Enter 0 for days you won’t work a reduced schedule.<br /><br />Your answer must match Question 33 in the Certification of a Serious Health Condition form.",
    minutesLabel: "$t(shared.minutesLabel)",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    sectionLabel:
      "How many hours will you take off while you are on a reduced leave schedule?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
    workScheduleToggle: "View your work schedule",
  },
  claimsReview: {
    achTypeLabel: "Account type",
    achType_checking: "$t(shared.achTypeChecking)",
    achType_savings: "$t(shared.achTypeSavings)",
    amountPerFrequency_daily: "$t(shared.amountPerFrequency_daily)",
    amountPerFrequency_inTotal: "$t(shared.amountPerFrequency_inTotal)",
    amountPerFrequency_monthly: "$t(shared.amountPerFrequency_monthly)",
    amountPerFrequency_weekly: "$t(shared.amountPerFrequency_weekly)",
    childBirthDateLabel: "Child’s date of birth",
    childPlacementDateLabel: "Child’s placement date",
    documentsLoadError: "$t(shared.documentsLoadError)",
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
    employerFeinLabel: "Employer’s EIN",
    employerNotifiedLabel: "Notified employer",
    employerNotifiedValue: "No",
    employerNotifiedValue_true: "Notified employer on {{date}}",
    employerWarning:
      "<p>Once you review and submit your application, we will send a copy of your application to your employer. In addition to details about your leave and employment information, your employer will see the last 4 digits of your Social Security Number or ITIN and your mailing address. They will also get a copy of the certification documents.</p>",
    employmentStatusLabel: "Employment status",
    employmentStatusValue_employed: "Currently employed",
    employmentStatusValue_selfEmployed: "Self-employed",
    employmentStatusValue_unemployed: "Unemployed",
    familyLeaveTypeLabel: "Family leave type",
    familyLeaveTypeValue_adoption: "Adoption",
    familyLeaveTypeValue_fosterCare: "Foster care",
    familyLeaveTypeValue_newBorn: "Birth",
    familyMemberDateOfBirthLabel: "Family member's date of birth",
    familyMemberNameLabel: "Family member's name",
    familyMemberRelationshipLabel: "Family member's relationship",
    familyMemberRelationship_child: "Child",
    familyMemberRelationship_grandchild: "Grandchild",
    familyMemberRelationship_grandparent: "Grandparent",
    familyMemberRelationship_inlaw: "Inlaw",
    familyMemberRelationship_parent: "Parent",
    familyMemberRelationship_serviceMember: "Service Member",
    familyMemberRelationship_sibling: "Sibling - Brother/Sister",
    familyMemberRelationship_spouse: "Spouse",
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
    leaveReasonValue_care: "$t(shared.leaveReasonCare)",
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
    otherIncomeType_ssdi: "$t(shared.otherIncomeType_ssdi)",
    otherIncomeType_unemployment: "$t(shared.otherIncomeType_unemployment)",
    otherIncomeType_workersCompensation:
      "$t(shared.otherIncomeType_workersCompensation)",
    otherLeaveChoiceNo: "$t(shared.choiceNo)",
    otherLeaveChoicePendingOtherIncomes: "$t(shared.choicePendingOtherIncomes)",
    otherLeaveChoiceYes: "$t(shared.choiceYes)",
    otherLeaveDollarAmount: "{{amount, currency}}",
    partDescription_1:
      "If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>",
    partHeadingPrefix: "Part {{number}}",
    partHeading_1_final:
      "Review: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_1_part1:
      "Review and confirm: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_2: "Review: Your payment information",
    partHeading_3: "Review: Upload document",
    partOneNextSteps:
      "<p>Once you review and submit Part 1, your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p><p>We’ll also notify your employer that you’ve started an application for paid family and medical leave.</p><p>Next, you’ll be able to work on Parts 2 and 3, and submit your application.</p>",
    paymentAccountNumLabel: "Account number",
    paymentMethodLabel: "Payment method",
    paymentMethodValue_ach: "$t(shared.paymentMethodAch)",
    paymentMethodValue_check: "$t(shared.paymentMethodCheck)",
    paymentRoutingNumLabel: "Routing number",
    phoneLabel: "Phone number",
    phoneType_cell: "Mobile",
    phoneType_phone: "Landline",
    pregnancyOrRecentBirthLabel: "Medical leave for pregnancy or birth",
    pregnancyOrRecentBirth_no: "$t(shared.choiceNo)",
    pregnancyOrRecentBirth_yes: "$t(shared.choiceYes)",
    previousLeaveEntryLabel: "$t(shared.previousLeaveEntryPrefix) {{count}}",
    previousLeaveFromCurrentEmployer_no:
      "Did not take leave from this employer",
    previousLeaveFromCurrentEmployer_yes: "Took leave from this employer",
    previousLeaveLabel: "Previous paid or unpaid leave?",
    previousLeaveReason_activeDutyFamily:
      "Leave was for managing family affairs while a family member was on active duty in the armed forces",
    previousLeaveReason_bonding:
      "Leave was for bonding with a child after birth or placement",
    previousLeaveReason_care: "Leave was for caring for a family member",
    previousLeaveReason_medical: "Leave was for an illness or injury",
    previousLeaveReason_pregnancy: "Leave was for a pregnancy",
    previousLeaveReason_serviceMemberFamily:
      "Leave was for caring for a family member who serves in the armed forces",
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
    userStateIdLabel: "Driver’s License Number",
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
      "Enter the number of hours you work each day. Enter 0 for days you don't work.",
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
  claimsScheduleVariable: {
    heading: "How many hours do you work on average each week?",
    hoursLabel: "$t(shared.hoursLabel)",
    inputHoursLabel: "Average weekly hours",
    lead:
      "We’ll confirm your hours with your employer after you submit your application. Learn more about <calculate-hours-link>how we use this number</calculate-hours-link> and how to figure out your average.",
    minutesLabel: "$t(shared.minutesLabel)",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsSsn: {
    lead:
      "Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What’s your Social Security Number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsStart: {
    explanation:
      "<p>We use this application to determine the leave time and benefit amount you will receive.</p><p>We need true answers to every question so that we can manage the program the way the law requires. You can read more about the <mass-consent-agreement-link>requirement to answer truthfully</mass-consent-agreement-link>.</p><p>Please confirm that you will answer as truthfully as you can.</p>",
    submitApplicationButton: "$t(shared.submitApplicationButton)",
    title: "Start your application",
    truthAttestation:
      "I understand that I need to give true answers to all questions in order to receive and keep my paid leave benefits and job protections. I understand false answers may forfeit my rights to paid leave and may result in other penalties.",
  },
  claimsStateId: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasStateIdLabel: "Do you have a Massachusetts driver’s license or ID card?",
    idHint:
      "This may be a 9 digit number or begin with an S or SA followed by numbers for a total of 9 characters.",
    idLabel: "Enter your license or ID number",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsSuccess: {
    adjudicationProcess:
      "<ul> <li>Your employer has 10 business days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision. Your employer will also get a copy of the decision.</li><li>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started. If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts. After that, you will receive your payments every week.</li></ul>",
    adjudicationProcessHeading: "What happens next",
    adjudicationProcess_bondingAdoptFosterFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of placement, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child arrived in your home earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    adjudicationProcess_bondingNewbornFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of birth, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child was born earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    adjudicationProcess_caringLeave:
      "<ul><li>Your employer has 10 business days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision. Your employer will also get a copy of the decision.</li><li>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started. If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts. After that, you will receive your payments every week.</li><li>If you need to end your leave early, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</li></ul>",
    adjudicationProcess_medicalPregnantFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>When your leave begins, call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> to tell us. Then we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    claimantApplicationId:
      "Your application ID is <strong>{{absence_id}}</strong>",
    exitLink: "Return to applications",
    familyLeaveToBond:
      "You can take up to 12 weeks of paid family leave to bond with your child after your medical leave ends. Family leave to bond with your child can be <medical-bonding-link>easily added to your claim</medical-bonding-link> by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.",
    familyLeaveToBondHeading: "You may also be eligible for paid family leave",
    medicalLeaveAfterBirth:
      "You can take up to 20 weeks of paid medical leave if you’re unable to work during your pregnancy and to recover from childbirth. Your health care provider determines how much medical leave you will need. Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> if you need <medical-bonding-link>medical leave after giving birth</medical-bonding-link>.",
    medicalLeaveAfterBirthHeading:
      "If you gave birth, you may also be eligible for paid medical leave",
    proofRequired_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to upload, mail, or fax a document that shows your child’s placement date.",
    proofRequired_bondingNewbornFuture:
      "After your child is born, you will need to upload, mail, or fax a document that shows your child’s date of birth.",
    proofRequired_medicalPregnantFuture:
      "You must call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> once your medical leave begins to confirm that your leave has begun. We can’t approve your application until we hear from$t(chars.nbsp)you.",
    reportReductionsHeading: "We may need more information from you",
    reportReductionsProcess:
      "<p>Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> if you’ll receive:</p><ul><li>Any <reductions-employer-benefits-link>benefits from your employer</reductions-employer-benefits-link> that you’ll be using in addition to Massachusetts paid leave (for example, maternity leave, or paid sick time)</li><li>Income from <reductions-overview-link>any other sources</reductions-overview-link> during your leave</li></ul>",
    title: "You submitted your application",
  },
  claimsUploadCertification: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose files",
    certificationDocumentsCount: "$t(shared.filesUploaded)",
    documentsLoadError: "$t(shared.documentsLoadError)",
    fileHeadingPrefix: "File",
    leadListNewborn: [
      "Your child’s birth certificate.",
      "A note from your child’s health care provider stating your child’s date of birth.",
      "A note from the health care provider of the person who gave birth stating your child’s date of birth.",
    ],
    lead_bonding_adopt_foster:
      "You need to upload a statement from your adoption or foster agency or from the Massachusetts Department of Children and Families to confirm the placement and the date of the placement.",
    lead_bonding_newborn:
      "You need to upload one of the following documents to confirm your child’s date of birth:",
    lead_care:
      "You need to upload a completed <caregiver-certification-form-link>$t(shared.caregiverCertificationForm)</caregiver-certification-form-link> to prove that you need to take leave to care for a family member with a serious medical condition.",
    lead_medical:
      "You need to upload a completed <healthcare-provider-form-link>PFML Certification of a Serious Health Condition</healthcare-provider-form-link> to prove that you need to take medical leave.",
    sectionLabel_bonding: "Upload your documentation",
    sectionLabel_care: "Upload your $t(shared.caregiverCertificationForm)",
    sectionLabel_medical:
      "Upload your Certification of a Serious Health Condition",
    title: "Upload certification",
  },
  claimsUploadDocsOptions: {
    certLabel_bonding_adopt_foster: "Proof of placement",
    certLabel_bonding_newborn: "Proof of birth",
    certLabel_medical: "Certification of a Serious Health Condition",
    nonStateIdLabel: "Different identification documentation",
    sectionHint:
      "You only need to complete this if you received a notice from the Department of Family and Medical Leave asking you to provide additional documents or you need to provide proof of birth or placement. ",
    sectionLabel: "What kind of document are you uploading?",
    stateIdLabel: "Massachusetts driver’s license or ID",
    title: "Additional documentation",
  },
  claimsUploadId: {
    accordionContent:
      "<p><strong>If you don’t have any of those, you can provide one of the following plus proof of your Social Security Number or Individual Tax Identification Number:</strong></p><ul><li>Valid, unexpired U.S. State or Territory License or ID, both front and back</li><li>Certified copy of a birth certificate filed with a State Office of Vital Statistics or equivalent agency in the individual’s state of birth. (You can only use a <puerto-rican-birth-certificate-link>Puerto Rican birth certificate</puerto-rican-birth-certificate-link> if it was issued on or after July 1, 2010.)</li><li>Certificate of Citizenship (Form N$t(chars.nbhyphen)560, or Form N$t(chars.nbhyphen)561)</li><li>Certificate of Naturalization (Form N$t(chars.nbhyphen)550 or N$t(chars.nbhyphen)570)</li></ul><p><strong>You can provide proof of your Social Security Number using one of the following documents displaying your complete Social Security Number:</strong></p><ul><li>Social Security card</li><li>W$t(chars.nbhyphen)2 Form</li><li>SSA$t(chars.nbhyphen)1099 Form</li><li>Non$t(chars.nbhyphen)SSA$t(chars.nbhyphen)1099 Form</li><li>Pay stub with your name on it</li></ul><p><identity-proof-link>Learn more about verifying your identity with different documents.</identity-proof-link></p>",
    accordionHeading: "If you don’t have any of those documents:",
    addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
    addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
    documentsLoadError: "$t(shared.documentsLoadError)",
    fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
    idDocumentsCount: "$t(shared.filesUploaded)",
    lead_mass:
      "<p>It’s faster to upload your documents online, but you can fax or mail color copies of your documents if you prefer. Follow the <mail-fax-instructions-link>fax and mail instructions</mail-fax-instructions-link>.</p><p>To verify your identity, <strong>upload a color copy of both the front and back of your ID card.</strong></p>",
    lead_other:
      "<p>It’s faster to upload your documents online, but you can fax or mail color copies of your documents if you prefer. Follow the <mail-fax-instructions-link>fax and mail instructions</mail-fax-instructions-link>.</p><p>To verify your identity you will need valid, unexpired documentation issued by state or federal government.</p>",
    otherIdentityDocs:
      "<p><strong>You can upload a copy of one of the following documents:</strong></p><ul><li>U.S. State or Territory Real ID, both front and back</li><li>U.S. passport or passport card</li><li>Permanent Resident Card issued by DHS or INS</li><li>Employment Authorization Document (EAD) issued by DHS</li><li>Foreign passport <strong>and</strong> a <work-visa-link>work visa</work-visa-link></li></ul>",
    sectionLabel_mass:
      "Upload the front and back of your Massachusetts driver’s license or ID card",
    sectionLabel_other:
      "Upload an identification document issued by state or federal government",
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
  employersAuthCreateAccount: {
    alertHeading:
      "Workers who wish to apply for paid leave should follow <create-account-link>these instructions</create-account-link>.",
    createAccountButton: "Create account",
    createClaimantAccount:
      "Need to apply for paid leave? <create-account-link>Create an account</create-account-link>",
    detailsLabel: "What you can do with this account",
    detailsList:
      "<ul><li>Review paid leave applications from your employees</li><li>Get updates about the program by email</li><li>Download documents and decision letters</li></ul>",
    einHint:
      "Your Employer Identification Number is a <ein-link>9-digit number</ein-link> assigned by the Internal Revenue Service. It is listed on tax returns and your payroll department should have this information.",
    einLabel: "Employer ID number (EIN)",
    haveAnAccount: "Have an account? <log-in-link>Log in</log-in-link>",
    leadBackground:
      "Welcome! Please take a few minutes to create an account for your company so you can manage leave for your team. Massachusetts workers can now apply for paid family and medical leave.",
    leadBackground_accountCreationContactCenter:
      "Please call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> to create an account for your organization.",
    leadBackground_accountCreationInstructions:
      "You'll need the following information to <account-creation-link>get started</account-creation-link>:",
    leadBackground_accountCreationList:
      "<ul><li>Work email address: An email address can only be associated with one account.</li><li>Password: Your password must be at least 12 characters long and include at least 1 number, 1 symbol, and both uppercase and lowercase letters.</li><li>Employer ID number (EIN): A 9-digit number assigned by the Internal Revenue Service. It is listed on tax returns and your payroll department should have this information.</li></ul>",
    leadMultipleCompanies:
      "If you manage leave for multiple companies, please create an account for each Employer ID number (EIN). You’ll be able to add more companies to an existing account in the future.",
    nextStep: "We’ll send you a 6-digit code to verify your email address.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create an employer account",
    usernameHint:
      "Use a secure work address. An email address can only be associated with one account.",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  employersAuthFinishAccountSetup: {
    createAccountFooterLink: "Create a new account",
    lead:
      "Please verify your email address. If an account exists for the email you provide, you’ll receive a 6-digit verification code. After that, you’ll be prompted to create a new password.",
    submitButton: "Submit",
    title: "Finish setting up your account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  employersCannotVerify: {
    body:
      "We can't verify this account because this organization hasn't submitted contributions through MassTaxConnect. Call the Department of Revenue at <dor-phone-link>$t(shared.departmentOfRevenuePhoneNumber)</dor-phone-link> to make arrangements to submit contributions. Once you do that, you'll be able to review leave applications on the next business day. Learn more about <learn-more-link>verifying your account</learn-more-link> on Mass.gov.",
    companyNameLabel: "<strong>Organization:</strong> {{employerDba}}",
    employerIdNumberLabel:
      "<strong>Employer ID number (EIN):</strong> {{employerFein}}",
    title: "We can't verify this organization",
  },
  employersClaimsConfirmation: {
    applicationIdLabel: "<strong>Application ID:</strong> {{absenceId}}",
    instructions:
      "<p>Thanks for letting us know that you’re not the right person to review this.</p><ul><li>Please check with your human resources team and your colleagues to see who should respond.</li><li>If the right person at your company already has an employer account, they received the same email you did and can respond directly.</li><li>Otherwise, please ask them to call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</li></ul>",
    instructionsFollowUpDateLabel:
      "<div><strong>Review by:</strong> {{date}} at 11:59 p.m. Eastern time</div>",
    instructions_processingApplication:
      "If we do not hear from anyone at your company before the deadline, we will process the application solely based on the information the employee provided.",
    title: "Help us find the right person to review the application",
  },
  employersClaimsNewApplication: {
    agreementBody:
      "I understand that I need to give true answers to all questions in order to fulfill my responsibilities as a Massachusetts employer. I certify under penalty of perjury that my answers will be complete and accurate.",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    dobLabel: "Date of birth",
    employeeNameLabel: "Employee name",
    employerIdNumberLabel: "Employer ID number (EIN)",
    instructions:
      "<p>This takes about 10 minutes. We use the information you provide to determine the leave time and benefit amount your employee will receive.</p><p>We need true answers to every question so that we can manage the program the way the law requires. Please confirm that you will answer as truthfully as you can.</p>",
    instructionsFollowUpDate: "$t(shared.employerInstructions_followUpDate)",
    instructionsLabel:
      "Are you the right person to respond to this application?",
    organizationNameLabel: "Organization",
    ssnOrItinLabel:
      "Social Security Number or Individual Taxpayer Identification Number",
    submitButton: "Submit",
    submitButton_secondary: "Agree and submit",
    title: "New application from {{name}}",
    truthAttestationHeading: "Start the review process",
  },
  employersClaimsReview: {
    employerIdentifierLabel: "Employer ID number (EIN)",
    instructionsAmendment:
      "Please review the details of this application carefully. If anything is incorrect or incomplete, you can add an amendment or include specific comments at the end.",
    instructionsFollowUpDate: "$t(shared.employerInstructions_followUpDate)",
    organizationNameLabel: "Organization",
    submitButton: "Submit",
    submitLoadingMessage: "Submitting… Do not refresh or go back.",
    title: "Review application from {{name}}",
  },
  employersClaimsStatus: {
    applicationIdLabel: "Application ID",
    lead_decision:
      "A decision has been made for this application. No action is required of you, but you can download a copy of the decision notice for details. Your employee has the right to appeal this decision under Massachusetts regulations (<dfml-regulations-link>458 CMR 2.14</dfml-regulations-link>).",
    lead_pending:
      "No action is required of you.<br /><br />When the application progresses you'll receive an email with a direct link for more details.",
    leaveDetailsLabel: "$t(shared.claimsLeaveDetailsTitle)",
    leaveDurationLabel: "$t(shared.claimsLeaveDurationTitle)",
    leaveDurationLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leaveDurationLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leaveDurationLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
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
    noticeName_pdf: "$t(shared.noticeName_pdf)",
    noticeName_pdf_approvalNotice: "$t(shared.noticeName_pdf_approvalNotice)",
    noticeName_pdf_denialNotice: "$t(shared.noticeName_pdf_denialNotice)",
    noticeName_pdf_requestForInfoNotice:
      "$t(shared.noticeName_pdf_requestForInfoNotice)",
    noticeName_requestForInfoNotice:
      "$t(shared.noticeName_requestForInfoNotice)",
    noticesLabel: "Notices",
    statusLabel: "Status",
    title: "Application status for {{name}}",
  },
  employersClaimsSuccess: {
    applicationIdLabel: "<strong>Application ID:</strong> {{absenceId}}",
    backToDashboardLabel: "Back to Dashboard",
    instructions_processingApplication:
      "We’ll begin processing this application and your employee should hear from us within 14 calendar days. Once we’ve made a decision, you’ll receive an email with a direct link to details about the decision.",
    instructions_reimbursement:
      "If your company has a paid disability, family, or medical leave policy for employees, you may qualify for <reimbursements-link>reimbursements for payments made during this leave<reimbursements-link>.",
    title: "Thanks for reviewing the application",
  },
  employersDashboard: {
    instructions:
      "Applications will not have a status until the Department has made a decision. Applications that don't have a status may require action from you.",
    noClaimResults: "No applications on file",
    startDateTooltip: "When an employee started a new leave application",
    statusDescription_approved:
      "<strong>Approved:</strong> DFML has approved this leave request.",
    statusDescription_closed:
      "<strong>Closed:</strong> The leave has passed and no action can be taken.",
    statusDescription_denied:
      "<strong>Denied:</strong> DFML has denied this leave request.",
    statusDescription_none:
      "<strong>“--” or no status:</strong> This leave request may require action from you; otherwise, it is awaiting a decision from DFML.",
    statusDescriptionsLabel: "Status descriptions",
    tableColHeading_created_at: "Application start date",
    tableColHeading_employee_name: "Employee name",
    tableColHeading_employer_dba: "Organization",
    tableColHeading_employer_fein: "Employer ID number",
    tableColHeading_fineos_absence_id: "Application ID",
    tableColHeading_status: "Status",
    title: "Dashboard",
    unavailableClaimsBody:
      "Your account has been verified. It may take up to 15 minutes for our systems to update so that you can log in and review applications. If anyone else on your team needs to review applications, they’ll also need to complete the <learn-more-link>verification process</learn-more-link>.",
    unavailableClaimsTitle:
      "Your applications are not accessible right now for: {{employers}}",
    verificationBody:
      "Every employer must verify paid leave contributions when creating an account. You need to <your-organizations-link>complete this process</your-organizations-link> to review applications from your team. If you have an EIN that isn't verified you won't see any applications related to that EIN.",
    verificationInstructions:
      "You have not verified any organizations. <your-organizations-link>Complete this process</your-organizations-link> to review applications.",
    verificationTitle: "Verify your account",
  },
  employersOrganizations: {
    addOrganizationButton: "Add organization",
    backToDashboardLabel: "Back to Dashboard",
    einTableHeader: "Employer ID number (EIN)",
    nearFutureAvailability_addOrganization:
      "You'll be able to add more organizations to your account in the near future.",
    nearFutureAvailability_inviteMembers:
      "You can manage leave for these organizations. In the future, you’ll be able to invite other members of your team to review applications.",
    organizationsTableHeader: "Organization",
    title: "Your organizations",
    verificationBlocked: "Verification blocked",
    verificationBody:
      "Every employer must verify paid leave contributions when creating an account. You need to <your-organizations-link>complete this process</your-organizations-link> to review applications from your team. If you have an EIN that isn't verified you won't see any applications related to that EIN.",
    verificationInstructions:
      "You have not verified any organizations. <your-organizations-link>Complete this process</your-organizations-link> to review applications.",
    verificationRequired: "Verification required",
    verificationTitle: "Verify your account",
  },
  employersOrganizationsAddOrganization: {
    continueButton: "Continue",
    employerIdNumberLabel: "Employer ID number (EIN)",
    instructions:
      "If you manage leave for multiple organizations, you can add them to your account. You’ll need to verify recent paid leave contributions from MassTaxConnect in the following step.",
    title: "Add an organization",
  },
  employersOrganizationsSuccess: {
    companyNameLabel: "<strong>Organization:</strong> {{company}}",
    continueButton: "Continue",
    employerIdNumberLabel: "<strong>Employer ID number (EIN):</strong> {{ein}}",
    instructions:
      "Your account has been verified. It may take up to 15 minutes for our systems to update so that you can log in and review applications. If anyone else on your team needs to review applications, they’ll also need to complete the <learn-more-link>verification process</learn-more-link>.",
    title: "Thanks for verifying your paid leave contributions",
  },
  employersOrganizationsVerifyContributions: {
    companyNameLabel: "<strong>Organization:</strong> {{company}}",
    detailsLabel: "Where to find your paid leave contributions",
    detailsList:
      "Log into <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> or contact your payroll department to complete these steps:<ol><li>On the <strong>Accounts</strong> tab, select <strong>Paid Family and Medical Leave</strong>.</li><li>On the <strong>Periods</strong> tab, select <strong>{{date}}</strong>. If you don't have access to MassTaxConnect, we recommend asking your payroll department to copy the data from the <recent-filing-periods-link>4 most recent filing periods</recent-filing-periods-link>.</li><li>Copy the <strong>Tax</strong> amount from the <strong>Summary</strong> section.</li></ol>If you have any questions about your paid leave contributions, please contact the Department of Revenue at <dor-phone-link><strong>$t(shared.departmentOfRevenuePhoneNumber)</strong></dor-phone-link> from 9am-4pm ET.",
    employerIdNumberLabel: "<strong>Employer ID number (EIN):</strong> {{ein}}",
    haveAnAccount: "Have an account? <log-in-link>Log in</log-in-link>",
    lead:
      "We need more information to verify your identity. We require every employer to verify recent <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> data when creating an account. This helps protect your employees and your company information.",
    submitButton: "Submit",
    title: "Verify your paid leave contributions from MassTaxConnect",
    withholdingAmountHint: "Include the full amount with dollars and cents.",
    withholdingAmountLabel: "Paid leave contributions from {{date}}",
  },
  employersWelcome: {
    checkEmailBody:
      "When an employee applies for leave, you’ll receive email updates about their application status and any steps you need to take. We’ll include everyone who has an employer account with your company in case you’re out of the office.",
    checkEmailTitle: "Check your email regularly",
    learnMoreLinks:
      "<ul><li><mass-employer-role-link>Your role as a Massachusetts employer</mass-employer-role-link></li><li><reimbursements-link>Employer reimbursements</reimbursements-link></li></ul>",
    learnMoreTitle: "Learn more",
    newTag: "New",
    respondBody:
      "When an application is submitted, you have 10 business days to open the direct link from your email and review it online. You can comment on the application, approve or deny it, and report fraud if needed. Reviewing takes about 10 minutes. If we don’t hear from anyone at your company before the deadline, we’ll process the application solely based on the information the employee provided.",
    respondTitle: "Respond to applications within 10 business days",
    settingsLinks:
      "<ul><li><your-organizations-link>Your organizations</your-organizations-link></li></ul>",
    settingsTitle: "Settings",
    verificationBody:
      "We require every employer to verify paid leave contributions when creating an account. You need to <your-organizations-link>complete this process</your-organizations-link> to review applications from your team.",
    verificationTitle: "Verify your account to continue",
    viewApplicationsBody:
      "When you log into your account you can now use the <dashboard-link>dashboard</dashboard-link> to see all the applications submitted by employees from your organization.",
    viewApplicationsTitle: "View all applications",
    viewFormsBody:
      "You’ll get an email about our application decision with a direct link to download the letter your employee received. For medical leave, you can download the <healthcare-provider-form-link>Certification of a Serious Health Condition form</healthcare-provider-form-link> during the review process. ",
    viewFormsBody_caring:
      "You’ll get an email about our application decision with a direct link to download the letter your employee received. For medical leave, you can download the <healthcare-provider-form-link>Certification of a Serious Health Condition form</healthcare-provider-form-link> during the review process. For leave to care for a family member you can download the <caregiver-certification-form-link>Certification to Care for a Family Member</caregiver-certification-form-link> during the review process. ",
    viewFormsTitle: "View forms and notices online",
    welcomeBody:
      "Thanks for joining the paid leave program. Massachusetts workers can now apply for paid family and medical leave.",
    welcomeTitle: "Welcome",
  },
  getReady: {
    alertHeading: "Only some people can apply online for now",
    alertOnline:
      "<p>If you are currently employed in Massachusetts but not self-employed, you can apply online or by phone for the following types of paid leave:</p><ul><li>Medical leave due to your own illness, injury, or pregnancy</li><li>Family leave to bond with your child after birth, adoption, or foster placement — whether you are applying before or after the child arrives</li></ul>",
    alertOnlineHeading: "Apply online",
    alertOnline_caring:
      "<p>If you are currently employed in Massachusetts but not self-employed, you can apply online or by phone for the following types of paid leave:</p><ul><li>Medical leave due to your own illness, injury, or pregnancy</li><li>Family leave to bond with your child after birth, adoption, or foster placement — whether you are applying before or after the child arrives</li><li>Family leave to care for a family member with a serious medical condition</li></ul>",
    alertPhone:
      "<p>Apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> if <strong>any</strong> of the following are true:</p><ul><li>You are self-employed or unemployed and you are applying for paid leave</li><li>You need paid family leave to care for a family member who serves in the armed forces</li><li>You need paid family leave to manage family affairs when a family member is on active duty in the armed forces</li></ul>",
    alertPhoneHeading: "Apply by phone",
    applicationsLink: "View all applications",
    createClaimButton: "Create an application",
    stepOne:
      "<p>If you can, tell your employer at least 30 days before your leave begins. If you need to take leave right away, tell your employer as soon as possible.</p><p>Once you tell your employer, you have the right to apply and your job is protected. Make a note of when you notified your employer. You will need to provide this date in your leave application.</p>",
    stepOneHeading: "1. Tell your employer that you need to take paid leave",
    stepThree:
      "<p>Applying takes around 15 minutes. Your information will save as you go, so you can finish your application later if you need to.</p><p>If you give birth and plan to take both pregnancy-related medical leave and family leave to bond with your newborn, you should apply for medical leave first. Family leave to bond with your child can be <medical-bonding-link>easily added to your claim</medical-bonding-link> by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>.</p><p>You need to create multiple leave applications if you are:</p><ul><li>Taking leave from multiple employers.</li><li>Taking time off in uneven blocks of time (intermittent leave), <strong>and</strong> taking time off completely or on a reduced schedule. You’ll need a separate application for the intermittent leave.</li></ul><p>PFML benefits are subject to reporting for tax purposes and may be subject to taxation. Withholding is not currently supported through the PFML program. Learn more about the <tax-liability-link>possible tax implications</tax-liability-link> of your paid leave benefits.</p>",
    stepThreeHeading: "3. Apply",
    stepTwoBondingLeaveBody:
      "<p>For family leave to bond with your child after birth, foster placement, or adoption you need a document that confirms your child’s date of birth or placement.</p><p>You can apply before your child is born or arrives in your home. You will need to provide proof of birth or placement for your application to be approved.</p>",
    stepTwoBondingLeaveSubhead: "To bond with a child",
    stepTwoCaringLeaveBody:
      "<p>The health care provider of the person you're caring for must complete the <caregiver-certification-form-link>$t(shared.caregiverCertificationForm)</caregiver-certification-form-link>.</p>",
    stepTwoCaringLeaveSubhead:
      "To care for a family member with a serious health condition",
    stepTwoFamilyLeaveSubhead: "Family leave",
    stepTwoHeading: "2. Get documentation that supports your leave request",
    stepTwoMedicalLeaveBody:
      "<p>Your health care provider must complete the <healthcare-provider-form-link>PFML Certification of a Serious Health Condition</healthcare-provider-form-link>.</p>",
    stepTwoMedicalLeaveSubhead: "Medical leave",
    title: "Get ready to apply",
  },
  index: {
    claimantCardBody: "You can now apply for Paid Family and Medical Leave.",
    claimantCreateAccountButton: "Create an account",
    claimantHeading: "Workers",
    createAccountHeading: "Create an account",
    employerCardBody_contactCenter:
      "Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> to create an employer account.",
    employerCardBody_massEmployer: "Are you a Massachusetts employer?",
    employerCardBody_selfRegister:
      "Register now so you can manage leave for your team.",
    employerCreateAccountButton: "Create an employer account",
    employerHeading: "Employers",
    seoTitle: "Massachusetts Paid Family and Medical Leave",
    title:
      "Massachusetts workers can now apply for Paid Family and Medical Leave. Learn more about this <mass-paid-leave-link>new paid leave program</mass-paid-leave-link>.",
  },
  userConsentToDataSharing: {
    agreementBody:
      "By continuing, I am indicating that I have read and understood the above user agreements. I give the Department of Family and Medical Leave permission to collect, share, and use my information consistent with the terms of the agreements linked$t(chars.nbsp)above.",
    applicationUsage: "",
    applicationUsageHeading_employer: "Reviewing paid leave applications",
    applicationUsageHeading_user: "Applying for benefits",
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
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to an application with health care providers and contracted private partners.",
    dataUsageBody_user:
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to your application with your employer, health care provider(s), and contracted private partners.",
    dataUsageHeading: "How we use your data",
    fullUserAgreementBody:
      "To find out more about how the Commonwealth might use the information you share with the Department of Family and Medical Leave, please read the <informed-consent-link>DFML Informed Consent Agreement</informed-consent-link> and the <privacy-policy-link>Privacy Policy for Mass.gov</privacy-policy-link>.",
    fullUserAgreementHeading: "Read the full user agreements",
    intro:
      "The information you provide on this website will be used to administer the Paid Family and Medical Leave program.",
    title: "How this website uses your information",
    updatedMessage:
      "To continue using this website, you must agree to the terms of the user agreements updated as of July$t(chars.nbsp)1,$t(chars.nbsp)2021.",
  },
};

const components = {
  absenceCaseStatusTag: {
    status_approved: "$t(shared.absenceCaseStatus_approved)",
    status_closed: "$t(shared.absenceCaseStatus_closed)",
    status_completed: "$t(shared.absenceCaseStatus_closed)",
    status_declined: "$t(shared.absenceCaseStatus_denied)",
  },
  amendButton: {
    amend: "Amend",
  },
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
    actionsHeading: "Actions",
    bondingLeaveDocsRequired_adopt_foster:
      "Once your child arrives, submit proof of placement so that we can make a decision.",
    bondingLeaveDocsRequired_newborn:
      "Once your child is born, submit proof of birth so that we can make a decision.",
    documentsLoadError: "$t(shared.documentsLoadError)",
    feinHeading: "Employer EIN",
    heading: "Application {{number}}",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_care: "$t(shared.leaveReasonCare)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    noticeDate: "$t(shared.noticeDate)",
    noticeName: "$t(shared.noticeName)",
    noticeName_approvalNotice: "$t(shared.noticeName_approvalNotice)",
    noticeName_denialNotice: "$t(shared.noticeName_denialNotice)",
    noticeName_pdf: "$t(shared.noticeName_pdf)",
    noticeName_pdf_approvalNotice: "$t(shared.noticeName_pdf_approvalNotice)",
    noticeName_pdf_denialNotice: "$t(shared.noticeName_pdf_denialNotice)",
    noticeName_pdf_requestForInfoNotice:
      "$t(shared.noticeName_pdf_requestForInfoNotice)",
    noticeName_requestForInfoNotice:
      "$t(shared.noticeName_requestForInfoNotice)",
    noticesDownload:
      "When you click the notice link, the file will download to your device.",
    noticesFallback:
      "Once we’ve made a decision, you can download the decision notice here. You’ll also get an email notification.",
    noticesHeading: "Download your notices",
    reductionsInstruction_1:
      "Any benefits from your employer that you’ll be using in addition to Massachusetts paid leave (for example, maternity leave, or paid sick time)",
    reductionsInstruction_2: "Income from any other sources during your leave",
    reductionsInstructionsIntro:
      "If you’ll receive <reductions-overview-link>other benefits or income</reductions-overview-link>, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link>. This includes:",
    resumeClaimButton: "Continue application",
    uploadDocsButton: "Upload additional documents",
  },
  authNav: {
    logOutButton: "Log out",
  },
  backButton: {
    label: "Back",
  },
  betaBanner: {
    tag: "Beta",
    message:
      "This is a new service. Help us improve it with <user-feedback-link>your feedback</user-feedback-link>.",
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
  documentRequirements: {
    body_certification:
      "<ul><li>The text must be clear and readable</li><li>Upload every page of the document where you or your health care provider have entered information</li><li>Each file you upload must be smaller than 4.5 MB</li></ul><p>It’s faster to upload your documents online, but you can fax or mail color copies of your documents if you prefer. Follow the <mail-fax-instructions-link>fax and mail instructions</mail-fax-instructions-link>.</p>",
    body_id:
      "<ul><li>The image of the card must be in full color</li><li>The text must be clear and readable</li><li>The front and back can be in one file, or in two separate files</li><li>Each file must be smaller than 4.5 MB</li></ul><p>It’s faster to upload your documents online, but you can fax or mail color copies of your documents if you prefer. Follow the <mail-fax-instructions-link>fax and mail instructions</mail-fax-instructions-link>.</p>",
    header: "Document Requirements:",
  },
  dropdown: {
    emptyChoiceLabel: "- Select an answer -",
  },
  employersEmployeeInformation: {
    addressLabel: "Mailing address",
    dobLabel: "Date of birth",
    employeeNameLabel: "Employee name",
    header: "Employee information",
    ssnOrItinLabel:
      "Social Security Number or Individual Taxpayer Identification Number",
  },
  employersEmployeeNotice: {
    choiceNo: "$t(shared.choiceNo) (explain below)",
    choiceYes: "$t(shared.choiceYes)",
    heading:
      "Did the employee give you at least 30 days notice about their leave?",
  },
  employersEmployerBenefits: {
    amountFrequency: "Select a frequency",
    amountFrequency_daily: "$t(shared.amountFrequency_daily)",
    amountFrequency_inTotal: "$t(shared.amountFrequency_inTotal)",
    amountFrequency_monthly: "$t(shared.amountFrequency_monthly)",
    amountFrequency_unknown: "$t(shared.amountFrequency_unknown)",
    amountFrequency_weekly: "$t(shared.amountFrequency_weekly)",
    amountPerFrequency: "{{amount, currency}}",
    amountPerFrequency_daily: "$t(shared.amountPerFrequency_daily)",
    amountPerFrequency_inTotal: "$t(shared.amountPerFrequency_inTotal)",
    amountPerFrequency_monthly: "$t(shared.amountPerFrequency_monthly)",
    amountPerFrequency_unknown: "$t(shared.amountPerFrequency_unknown)",
    amountPerFrequency_weekly: "$t(shared.amountPerFrequency_weekly)",
    benefitTypeLabel: "Benefit type",
    caption:
      "Your employee is planning to use these benefits during their leave. Learn more about how paid leave works with <reductions-overview-link>other government and private benefit programs</reductions-overview-link>.",
    commentInstructions: "$t(shared.employerInstructions_addComment)",
    dateRangeLabel: "Date range",
    detailsLabel: "Details",
    header: "Employer benefits",
    tableName: "Employer-sponsored benefit details",
  },
  employersEmployerDecision: {
    choiceApprove: "Approve",
    choiceDeny: "Deny (explain below)",
    explanation:
      "Answer based on your company policies and our <mass-employer-role-link>guidelines for employers</mass-employer-role-link>. Your recommendation is helpful to the Department in making its determination.",
    heading: "Have you approved or denied this leave request?",
  },
  employersFeedback: {
    addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
    addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    commentSolicitation: "Please tell us more.",
    commentSolicitation_employeeNotice:
      "Please tell us when your employee notified you about their leave.",
    commentSolicitation_employerDecision:
      "Please tell us why you denied this leave request.",
    commentSolicitation_fraud:
      "Please tell us why you believe this is fraudulent.",
    fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
    instructionsLabel: "Do you have any additional comments or concerns?",
    supportingDocumentationLabel:
      "If you have any supporting documentation, please attach it for review.",
  },
  employersFraudReport: {
    alertBody:
      "We take allegations about fraud seriously. Selecting this will begin further investigation. Please only select if you are convinced this is fraudulent. If you have questions, feel free to call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> from 8am‑5pm ET.",
    alertHeading: "You are reporting fraud.",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes) (explain below)",
    detailsLabel: "What counts as paid leave fraud?",
    example_falseDocuments: "Providing forged or falsified documents",
    example_falseInfo:
      "Withholding information or providing false information to the Department of Family and Medical Leave",
    example_personalInfo:
      "Using someone’s personal information to fraudulently collect benefits",
    heading: "Do you have any reason to suspect this is fraud?",
  },
  employersIntermittentLeaveSchedule: {
    claimDurationType_continuous: "$t(shared.claimDurationTypeContinuous)",
    claimDurationType_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    claimDurationType_reducedSchedule:
      "$t(shared.claimDurationTypeReducedSchedule)",
    downloadAttachments:
      "Download the documentation below or contact us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> for details about the leave schedule.",
    frequencyBasis_irregular: "Irregular over the next 6 months",
    frequencyBasis_months: "At least once a month",
    frequencyBasis_weeks: "At least once a week",
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
  },
  employersLeaveDetails: {
    applicationIdLabel: "Application ID",
    bondingRegsReviewDetailsLabel:
      "Does the employee work at an acute care hospital, or the teaching hospital of the University of Massachusetts Medical School?",
    bondingRegsReviewDetailsSummary:
      "If so, this employee may be eligible to take their paid family leave anytime in 2021, <emergency-bonding-regs-employer-link>due to emergency Covid-19 regulations for hospital workers</emergency-bonding-regs-employer-link>.",
    header: "Leave details",
    leaveDurationLabel: "Leave duration",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_care: "$t(shared.leaveReasonCare)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveTypeLabel: "Leave type",
  },
  employersLeaveSchedule: {
    caption: "This is your employee’s expected leave schedule.",
    caption_documents:
      "This is your employee’s expected leave schedule. Download the attached documentation for more details.",
    caption_intermittentWithDocuments:
      "Download the attached documentation for details about the employee’s intermittent leave schedule.",
    claimDurationType_continuous: "$t(shared.claimDurationTypeContinuous)",
    claimDurationType_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    claimDurationType_reducedSchedule:
      "$t(shared.claimDurationTypeReducedSchedule)",
    dateRangeLabel: "Date range",
    detailsLabel: "Details",
    documentationLabel: "Documentation",
    downloadAttachments:
      "Download the documentation below or contact us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumber)</contact-center-phone-link> for details about the leave schedule.",
    header: "Leave schedule",
    healthCareProviderFormLink: "Certification of a Serious Health Condition",
    leaveFrequencyLabel: "Leave frequency",
    recordkeepingInstructions:
      "To meet <mass-employer-role-link>federal laws and regulations</mass-employer-role-link>, you must keep medical records separate and confidential from any personnel files.",
    reducedHoursPerWeek: "Reduced by {{numOfHours}} hours per week",
    tableName: "Leave schedule details table",
  },
  employersNavigationTabs: {
    dashboard: "Dashboard",
    welcome: "Welcome",
  },
  employersPreviousLeaves: {
    commentInstructions: "$t(shared.employerInstructions_addComment)",
    dateRangeLabel: "Date range",
    explanation:
      "If your employee took any paid or unpaid leave for a qualifying reason since January 1, 2021, it may <calculate-reductions-link>affect their benefit amount</calculate-reductions-link>.",
    header: "Past leave",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_care: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveTypeLabel: "Leave type",
    qualifyingReasonContent:
      "An employee or contractor can take paid or unpaid leave to:",
    qualifyingReasonDetailsLabel: "$t(shared.qualifyingReasonDetailsLabel)",
    qualifyingReason_activeDuty:
      "Manage family affairs when a family member is on active duty in the armed forces",
    qualifyingReason_bondWithChild:
      "Bond with a child after birth or placement",
    qualifyingReason_careForFamilyMedical:
      "Care for a family member with a <mass-benefits-guide-serious-health-condition-link>serious health condition</mass-benefits-guide-serious-health-condition-link>",
    qualifyingReason_careForFamilyMilitary:
      "Care for a family member who serves in the armed forces",
    qualifyingReason_manageHealth:
      "Manage a <mass-benefits-guide-serious-health-condition-link>serious health condition</mass-benefits-guide-serious-health-condition-link>, including illness, injury, or pregnancy",
  },
  employersSupportingWorkDetails: {
    header: "Supporting work details",
    weeklyHoursWorkedLabel: "Weekly hours worked",
  },
  errorBoundary: {
    message:
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumber)",
    reloadButton: "Reload this page",
  },
  errorsSummary: {
    genericHeading: "An error occurred",
    genericHeading_plural: "{{count}} errors occurred",
  },
  fieldsetAddress: {
    cityLabel: "City",
    line1Label_mailing: "Mailing address",
    line1Label_residential: "Address",
    line2Label_mailing: "Mailing address line 2",
    line2Label_residential: "Address line 2",
    stateLabel: "State",
    zipLabel: "ZIP",
  },
  fileCard: {
    removalWarning: "You can’t remove files previously uploaded.",
    removeButton: "Remove file",
    uploadDate: "Date of upload: {{date}}",
  },
  fileCardList: {
    loadingLabel: "Loading files",
  },
  fileUploadDetails: {
    label: "Tips for uploading images or PDFs",
    tips: [
      {
        listHeading: "This website only accepts:",
        listItems: ["PDF documents", "Images (.jpg, .jpeg, .png)"],
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
        listHeading: "If your document is attached to an email:",
        listItems: [
          "Open the file on your computer or phone",
          "Save it as a PDF or image, and try uploading again",
        ],
      },
    ],
  },
  footer: {
    description: "$t(shared.siteDescription)",
    logoTitle: "Go to PFML homepage",
    orgAddress: "PO Box 838 Lawrence, MA 01842",
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
  inputPassword: {
    toggleLabel: "Show password",
  },
  leaveDatesAlert: {
    heading: "Your leave dates for paid leave",
  },
  maintenanceTakeover: {
    lead:
      "This page is currently unavailable while the site is undergoing maintenance. Please check back$t(chars.nbsp)shortly.",
    scheduled:
      "We are performing scheduled maintenance to improve functionality and our overall service. Paid leave applications will be back online on <strong>{{scheduledRemovalDayAndTime}}</strong>.<br/><br/>When we are back, you will be able to access your existing applications or create a new one. Employers will be able to respond to information requests. We appreciate your understanding and patience. To get ready, review <what-to-expect-link>what to expect when you apply for paid family and medical leave benefits</what-to-expect-link>.",
    title: "We’re undergoing maintenance",
  },
  newsBanner: {
    // TODO (EMPLOYER-1296): Add Mass.gov link to banner
    body:
      "Soon you'll be able to see all the applications you need to review using our new dashboard. Over the next few months we'll be adding more features to the dashboard so you can easily find and manage paid leave applications.",
    header: "We're making it easier to manage paid leave applications",
  },
  pagination: {
    nextLabel: "Next",
    previousLabel: "Previous",
    summary:
      "Viewing {{firstRecordNumber}} – {{lastRecordNumber}} of {{totalRecords}} results",
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
  unsupportedBrowserBanner: {
    message:
      "<strong>Your browser is out of date</strong>. Please <update-link>update your browser</update-link> for more security, speed and the best experience on our site.",
  },
  userFeedback: {
    instructions:
      "We’d like to hear more about your experience on this site. Please take a few minutes to share your feedback.",
    surveyLink: "<user-feedback-link>Take the survey</user-feedback-link>",
    title: "Help us improve this site",
  },
  weeklyTimeTable: {
    dayHeader: "Day",
    day_Friday: "$t(shared.day_Friday)",
    day_Monday: "$t(shared.day_Monday)",
    day_Saturday: "$t(shared.day_Saturday)",
    day_Sunday: "$t(shared.day_Sunday)",
    day_Thursday: "$t(shared.day_Thursday)",
    day_Tuesday: "$t(shared.day_Tuesday)",
    day_Wednesday: "$t(shared.day_Wednesday)",
    hoursHeader: "Hours",
    time: "{{minutes, hoursMinutesDuration}}",
  },
  withBenefitsApplications: {
    loadingLabel: "Loading applications",
  },
  withClaims: {
    loadingLabel: "Loading claims",
  },
  withEmployerClaim: {
    loadingLabel: "Loading claim",
  },
  withUser: {
    loadingLabel: "Loading account",
  },
};

const englishLocale = {
  translation: Object.assign({}, { chars, components, errors, pages, shared }),
};

export default englishLocale;
