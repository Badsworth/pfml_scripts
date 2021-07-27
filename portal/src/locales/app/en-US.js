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
  applications: {
    concurrent_leave: {
      is_for_current_employer: {
        required: "Select Yes if your leave is from this employer.",
      },
      leave_end_date: {
        format:
          "The date your leave ends must include a valid month, day, and year.",
        invalid_date_range:
          "The date your leave ends must be on or after the date your leave begins.",
        minimum: "Enter a date after December 31, 2020.",
        required: "Enter the date this leave ends.",
      },
      leave_start_date: {
        format:
          "The date your leave starts must include a valid month, day, and year.",
        minimum: "Enter a date after December 31, 2020.",
        required: "Enter the date this leave starts.",
      },
    },
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
      is_full_salary_continuous: {
        required:
          "Select Yes if this employer-sponsored benefit fully replaces your wages.",
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
        "Select Yes if you told your employer that you are taking leave.",
    },
    employment_status: {
      required: "Enter your employment status.",
    },
    fineos_case_creation_issues:
      "We couldn’t find you in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, <mass-gov-form-link>follow these instructions</mass-gov-form-link> and we’ll set up your application through our Contact Center.",
    fineos_case_error:
      "There was a problem when trying to send your information to our system. Try submitting this information again.",
    first_name: {
      maxLength: "First name must be 50 characters or fewer.",
      required: "Enter a first name.",
    },
    has_concurrent_leave: {
      required:
        "Select Yes if you will use any other paid leave during your PFML leave.",
    },
    has_continuous_leave_periods: {
      required: "Select Yes if you are taking continuous leave.",
    },
    has_employer_benefits: {
      required:
        "Select Yes if you will you use any employer-sponsored benefits during your leave.",
    },
    has_intermittent_leave_periods: {
      required: "Select Yes if you are taking intermittent leave.",
    },
    has_mailing_address: {
      required: "Select Yes if you get your mail at this address.",
    },
    has_other_incomes: {
      required:
        "Select Yes if you will receive income from any other sources during your leave.",
    },
    has_previous_leaves_other_reason: {
      required:
        "Select Yes if you have taken any other leave since January 1, 2021 for a different qualifying reason.",
    },
    has_previous_leaves_same_reason: {
      required:
        "Select Yes if you have taken any other leave for the same qualifying reason.",
    },
    has_reduced_schedule_leave_periods: {
      required: "Select Yes if you are working a reduced schedule.",
    },
    has_state_id: {
      required:
        "Select Yes if you have a Massachusetts driver's license or ID card.",
    },
    hours_worked_per_week: {
      maximum: "The average hours you work each week must be less than 168.",
      minimum: "The average hours you work each week must be greater than 1.",
      required: "Enter how many hours you work on average each week.",
      type: "The average hours you work each week must be a number.",
    },
    last_name: {
      maxLength: "Last name must be 50 characters or fewer.",
      required: "Enter a last name.",
    },
    leave_details: {
      caring_leave_metadata: {
        family_member_date_of_birth: {
          format:
            "Your family member’s date of birth must include a valid month, day, and year.",
          future_birth_date:
            "Family member's date of birth must be less than 7 months from now.",
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
        maximum: "Date you notified your employer cannot be in the future.",
        minimum:
          "Year you notified your employer must be within the past two years.",
        required: "Enter the date you notified your employer.",
      },
      employer_notified: {
        required:
          "Select Yes if you told your employer that you are taking leave",
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
            "Sorry, our intermittent leave request service is a work in progress. Use our <intermittent-leave-guide>step-by-step guide to intermittent leave</intermittent-leave-guide> to complete your application. You can also complete your application by calling our Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
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
          "Select Yes if are you taking medical leave because you are pregnant or recently gave birth.",
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
    middle_name: {
      maxLength: "Middle name must be 50 characters or fewer.",
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
        checksum:
          "Enter a valid routing number. Check that you entered your routing number correctly. It is a 9-digit number located in the bottom left-hand corner of a check which uniquely identifies your bank.",
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
    previous_leaves_other_reason: {
      is_for_current_employer: {
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.isForCurrentEmployer_required)",
      },
      leave_end_date: {
        format:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_format)",
        invalid_date_range:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_invalidDateRange)",
        minimum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_required)",
      },
      leave_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveMinutes_required)",
      },
      leave_reason: {
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveReason_required)",
      },
      leave_start_date: {
        format:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_format)",
        minimum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_required)",
      },
      worked_per_week_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveDetails.errors.workedPerWeekMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.workedPerWeekMinutes_required)",
      },
    },
    previous_leaves_same_reason: {
      is_for_current_employer: {
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.isForCurrentEmployer_required)",
      },
      leave_end_date: {
        format:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_format)",
        invalid_date_range:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_invalidDateRange)",
        minimum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveEndDate_required)",
      },
      leave_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveMinutes_required)",
      },
      leave_start_date: {
        format:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_format)",
        minimum:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.leaveStartDate_required)",
      },
      worked_per_week_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveDetails.errors.workedPerWeekMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveDetails.errors.workedPerWeekMinutes_required)",
      },
    },
    residential_address: {
      city: {
        maxLength: "City must be 40 characters or fewer.",
        required: "Enter a city for your residential address.",
      },
      line_1: {
        maxLength: "Address must be 40 characters or fewer.",
        required: "Enter the street address for your residential address.",
      },
      line_2: {
        maxLength: "Address line 2 must be 40 characters or fewer.",
      },
      required: "Enter a residential address.",
      state: {
        maxLength: "State must be 40 characters or fewer.",
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
        "We already have an account set up for you. Please sign in with that account. If that doesn’t sound familiar to you, call the Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
      disallow_caring_leave_before_july:
        "Leave start dates for caring leave must be after June 30, 2021.",
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
        "We couldn’t find you in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, call the Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
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
  auth: {
    attemptBlocked_forgotPassword:
      "Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the contact center at $t(shared.contactCenterPhoneNumberNoBreak).",
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
    expiredVerificationCode:
      "Invalid verification code. Please request a new code.",
    incorrectEmailOrPassword: "Incorrect email or password",
    invalidParametersFallback: "Enter all required information",
    invalidParametersIncludingMaybePassword:
      "Check the requirements and try again. Ensure all required information is entered and the password meets the requirements.",
    invalidPhoneFormat: "Invalid phone number",
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
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
  caughtError_DocumentsLoadError: "$t(shared.documentsLoadError)",
  caughtError_DocumentsUploadError: "$t(shared.documentsUploadError)",
  caughtError_ForbiddenError:
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
  caughtError_NetworkError: "$t(shared.networkError)",
  caughtError_NotFoundError:
    "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
  caughtError_UserNotReceivedError:
    "Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak)",
  documents: {
    file: {
      required: "Upload at least one file to continue.",
    },
    fineos_client: "$t(shared.documentsUploadError)",
  },
  employers: {
    comment: {
      maxLength: "$t(shared.maxEmployerCommentLengthError)",
    },
    contains_v1_and_v2_eforms:
      "<h3>Call the contact center to review this application</h3><p>We can’t display this application for review online. To review this application, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p><strong>What you will need to know when you call the agent:</strong></p><ul><li>The employee’s name and application ID. You can find these on the Dashboard, or in the email we sent to tell you that you can review this application.</li><li>The error code for this error: <strong>V-12</strong>.</li></ul><strong>Why you are seeing this error:</strong> Your employee told us about some other leave and benefits they are receiving in addition to paid leave from PFML. This information was added to their application recently. In some cases, when an employee who submitted an application before July 15th then adds other leave and benefits information later, it can cause this error.<p>This is a rare error that will not happen with new applications.</p>",
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
      // TODO (EMPLOYER-1565): Remove this once the API no longer returns it
      invalid:
        "Enter your 9-digit Employer Identification Number in the correct format.",
      pattern:
        "Enter your 9-digit Employer Identification Number in the correct format.",
      require_contributing_employer:
        "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly and the associated business is contributing to Paid Family and Medical Leave.",
      require_employer:
        "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly.",
      required: "Enter your 9-digit Employer Identification Number.",
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
    relationship_inaccurate_reason: {
      maxLength: "$t(shared.maxEmployerCommentLengthError)",
    },
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
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak)",
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
  amountFrequencyLabel: "Frequency",
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
  certificationFormCare:
    "Certification of Your Family Member’s Serious Health Condition",
  certificationFormMedical: "Certification of Your Serious Health Condition",
  choiceHint_familyOrMedicalLeave: "For example, a paid parental leave policy",
  choiceHint_shortTermDisability: "Short-term or long-term disability",
  choiceNo: "No",
  choiceYes: "Yes",
  claimDurationTypeContinuous: "Continuous leave",
  claimDurationTypeIntermittent: "Intermittent leave",
  claimDurationTypeReducedSchedule: "Reduced leave schedule",
  claimsEmploymentInfoTitle: "Employment information",
  claimsLeaveDetailsTitle: "Leave details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsOtherLeaveTitle: "Other leave, benefits, and income",
  claimsPreviousLeaveDetails: {
    addButton: "Add another previous leave",
    errors: {
      isForCurrentEmployer_required:
        "Select Yes if your leave is from this employer.",
      leaveEndDate_format:
        "The date your leave ended must include a valid month, day, and year.",
      leaveEndDate_invalidDateRange:
        "The date your leave ends must be on or after the date your leave began.",
      leaveEndDate_minimum:
        "Only enter previous leaves taken on or after January 1, 2021.",
      leaveEndDate_required: "Enter the date your leave ended.",
      leaveMinutes_maximum:
        "The hours entered are more than the possible hours.",
      leaveMinutes_required:
        "Enter the hours you took off work for your leave.",
      leaveReason_required: "Select the qualifying reason for your leave.",
      leaveStartDate_format:
        "The date your leave began must include a valid month, day, and year.",
      leaveStartDate_minimum:
        "Only enter previous leaves taken on or after January 1, 2021.",
      leaveStartDate_required: "Enter the date your leave began.",
      workedPerWeekMinutes_maximum:
        "The hours entered are more than the possible hours.",
      workedPerWeekMinutes_required: "Enter the hours you normally worked.",
    },
    isForCurrentEmployerHint:
      "This is the same Employer Identification Number you entered earlier in your application. After you submit your application, this employer will be able to review it. We won’t share any leave you took from other employers.",
    isForCurrentEmployerLabel:
      "Did you take leave from this employer? EIN:$t(chars.nbsp){{employer_fein, ein}}",
    leaveEndDateLabel: "What was the last day of this leave?",
    leaveMinutesHint:
      "Add up all the hours you took off between the first and last day of this leave and enter the total. For example, if you took off 8 hours in one week and 12 hours in another, you should enter 20 hours.",
    leaveMinutesLabel: "What was the total number of hours you took off?",
    leaveStartDateLabel: "What was the first day of this leave?",
    limitMessage: "You can only add up to {{limit}} leaves",
    removeButton: "Remove this previous leave",
    sectionHint:
      "Enter details about each period of leave taken between {{previousLeaveStartDate}} and {{leaveStartDate}}. A leave period begins on the day you first went on leave and ends on the last day of leave. If you were on leave intermittently, your leave period begins on the first day you went on leave and ends on the very last day.",
    sectionLabel: "Tell us about your previous leave",
    workedPerWeekMinutesDetails:
      "If your weekly schedule was not consistent, enter the average number of hours you would have worked per week. For example, if your leave was across two different weeks, and your normal work schedule was 40 hours in one week and 20 hours in the next, you should enter 30 hours.",
    workedPerWeekMinutesDetailsLabel: "What if my schedule was not consistent?",
    workedPerWeekMinutesHint:
      "Enter the number of hours you would have worked each week, if you were not on leave.",
    workedPerWeekMinutesLabel:
      "How many hours would you normally have worked per week at the time you took this leave?",
  },
  claimsVerifyIdTitle: "Your identification",
  contactCenterAddress:
    "PO Box 838$t(chars.nbsp)Lawrence, MA$t(chars.nbsp)01842",
  contactCenterFaxNumber: "(617)$t(chars.nbsp)855$t(chars.nbhyphen)6180",
  contactCenterPhoneNumber: "(833) 344-7365",
  contactCenterPhoneNumberNoBreak:
    "(833)$t(chars.nbsp)344$t(chars.nbhyphen)7365",
  dateRangeDelimiter: "to",
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
    "An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
  documentsUploadError:
    "We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at $t(shared.contactCenterPhoneNumberNoBreak).",
  ein: {
    employer_verification_data_required:
      "Your account can’t be verified yet, because your organization has not made any paid leave contributions. Once this organization pays quarterly taxes, you can verify your account and review applications. <file-a-return-link>Learn more about filing returns and remitting contributions</file-a-return-link>.",
  },
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Temporary disability insurance",
  employerInstructions_addComment:
    "If something is incomplete, add a comment at the end of the page.",
  employerInstructions_followUpDate:
    "<strong>Review and respond by:</strong> {{date}} at 11:59 p.m. Eastern time",
  employerLeaveScheduleLeadHasDocs:
    "Download the attached documentation or contact us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> for details about the leave schedule.",
  employerLeaveScheduleLeadNoDocs:
    "Contact us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> for details about the leave schedule.",
  fileUpload_addAnotherFileButton: "Choose another file",
  fileUpload_addFirstFileButton: "Choose files",
  fileUpload_fileHeadingPrefix: "File",
  filesUploaded: "Number of files uploaded",
  genderGenderNotListed: "Gender not listed",
  genderMan: "Man",
  genderNonbinary: "Non-binary",
  genderPreferNotToAnswer: "Prefer not to answer",
  genderWoman: "Woman",
  hoursLabel: "Hours",
  leavePeriodCaringAlert:
    "You will need a completed <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> for this$t(chars.nbsp)section.",
  leavePeriodContinuousDatesLeadMedicalOrPregnancy:
    "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the continuous leave period start and end dates in the $t(shared.certificationFormMedical).",
  leavePeriodHasLeaveHintCare:
    "Your answer must match the $t(shared.certificationFormCare).",
  leavePeriodHasLeaveHintMedicalOrPregnancy:
    "Your answer must match the $t(shared.certificationFormMedical).",
  leavePeriodHasLeaveHintUpdateMedicalCertForm:
    "Your answer must match the corresponding checkbox of Question 14 in the $t(shared.certificationFormMedical).",
  leavePeriodIntermittentDatesLeadMedicalOrPregnancy:
    "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the intermittent leave start and end dates in the $t(shared.certificationFormMedical).",
  leavePeriodMedicalAlert:
    "You will need a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link> for this$t(chars.nbsp)section.",
  leavePeriodReducedDatesLeadMedicalOrPregnancy:
    "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the reduced leave start and end dates in the $t(shared.certificationFormMedical).",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Bond with a child",
  leaveReasonCare: "Care for a family member",
  leaveReasonMedical: "Medical leave",
  leaveReasonPregnancy: "Medical leave for pregnancy or birth",
  leaveReasonServiceMemberFamily: "Military family",
  maxEmployerCommentLengthError:
    "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
  maximumReducedLeaveMinutes:
    "Hours you will take off cannot exceed your work schedule.",
  minimumReducedLeaveMinutes:
    "Reduced leave schedule hours must be 0 or greater.",
  minutesLabel: "Minutes",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak)",
  noneReported: "None reported",
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
  reducedLeaveScheduleLeadCertGuidanceMedicalOrPregnancy:
    "The total number of hours you enter must match the reduced leave schedule section in the $t(shared.certificationFormMedical).",
  resendVerificationCodeLink: "Resend the code",
  siteDescription:
    "Apply for this Commonwealth-offered benefit here, or log in to review your applications.",
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
      "<p>You can apply online if you’re currently employed in Massachusetts.</p><p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    alertHeading: "You can now apply for paid family and medical leave.",
    areAnEmployer:
      "<strong>Are you a Massachusetts employer?</strong> <employer-create-account-link>Create an employer account</employer-create-account-link> to manage leave for your team.",
    backButton: "Back to Mass.gov",
    createAccountButton: "Create account",
    createEmployerAccount:
      "<strong>Are you a Massachusetts employer?</strong> Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to create an employer account.",
    employerRedirect:
      "Need to create an employer account? <employer-create-account-link>Register to manage leave for your team.</employer-create-account-link>",
    haveAnAccountFooterLabel: "Have an account?",
    logInFooterLink: "Log in",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create a worker account to apply for paid leave",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authForgotPassword: {
    backToLoginLink: "$t(shared.backToLoginLink)",
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead: "If an account exists for the email you provide, we will email a 6-digit verification code to it.",
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
    lead: "If an account exists for the email you provide, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    lead_email:
      "If an account exists for {{emailAddress}}, we emailed a 6 digit verification code to it. Enter the code below to confirm your email and reset your password.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    submitButton: "Set new password",
    title: "Create a new password",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authVerifyAccount: {
    backToLoginLink: "$t(shared.backToLoginLink)",
    codeLabel: "$t(shared.verificationCodeLabel)",
    codeResent:
      "We sent a new 6-digit verification code to your email address. Enter the new code to verify your email.",
    codeResentHeading: "New verification code sent",
    confirmButton: "Submit",
    lead: "We sent a 6-digit verification code to your email address. Enter the code to verify your email.",
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
    hint: "We will use this as your residential address for any previous applications you have submitted. If you are part of an Address Confidentiality Program, please provide your substitute address.",
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
    lead: "<p>This paid leave applies to parents of children who have joined their family in the past 12 months via:</p><ul><li>Birth</li><li>Foster placement</li><li>Adoption</li></ul>",
    submitApplicationButton: "$t(shared.submitApplicationButton)",
    title: "Confirm that you are an eligible parent",
    truthAttestation:
      "I agree that I am a new parent by one of the routes listed and can provide certification to support this relationship.",
  },
  claimsCaringLeaveAttestation: {
    lead: "This paid leave applies to caregivers with an <caregiver-relationship-link>eligible family relationship</caregiver-relationship-link>.",
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
    // TODO (CP-2354) Remove CC guidance for claims with Part 1 submitted without reductions data
    otherLeaveSubmittedDetailsBody:
      "<ul><li>You have already taken leave to care for a family member since July 1, 2021</li><li>You have already taken leave since January 1, 2021 <when-can-i-use-pfml>for any other reason that qualifies for PFML</when-can-i-use-pfml></li><li>You plan to use any accrued paid leave or any other benefits from your employer during your paid leave from PFML (for example: your employer’s parental leave program or paid sick time)</li><li>You expect to get income from any other sources during your leave (for example: disability insurance, retirement benefits, or another job)</li></ul>",
    otherLeaveSubmittedDetailsLabel: "What do I need to report?",
    otherLeaveSubmittedIntro:
      "<p>If you have any other leaves, benefits, or income to report, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    partOneSubmittedDescription:
      "Your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Now, you can work on Parts 2 and 3, and submit your application.",
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
      "<p>You need to provide your completed <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link>.</p><p>Your certification documents will be shared with your employer as part of your leave application.</p>",
    stepHTMLDescription_employerInformation:
      "You will need to know:<ul><li>Your employer’s 9 digit federal employer identification number (FEIN or EIN). <br><strong>Where to find this: </strong>on your W$t(chars.nbhyphen)2 or 1099, or ask your employer’s finance department.</li><li>The date you told your employer you were taking leave.</li></ul><p>If you are taking leave from multiple employers, you must create separate applications for each job.</p>",
    stepHTMLDescription_leaveDetails:
      "<p>If you’re not sure what kind of leave to apply for, <which-paid-leave-link>learn more about Paid Family and Medical Leave</which-paid-leave-link>.</p><p><strong>Are you taking medical leave for your own serious health condition?</strong></p><p>You need to have a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link>. Use your health care provider’s answers on the certification form to fill out some parts of the application.</p><p>If you give birth and plan to take both pregnancy-related medical leave and family leave to bond with your newborn, you should apply for medical leave first. Family leave to bond with your child can be easily added to your claim by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p><strong>Are you taking leave to bond with a child?</strong></p><p>You need to know the child’s date of birth, due date, or the date they arrived in your home for adoption or foster care.</p><p>You also need to know when you want your leave to begin and end.</p><p><strong>Are you taking leave to care for a family member?</strong></p><p>You need to have the <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> completed by their health care provider. You will need to use the health care provider’s answers on the certification form to fill out some parts of the application.</p><p>You also need to be sure of the <caregiver-relationship-link>eligibility of your relationship</caregiver-relationship-link>.</p>",
    stepHTMLDescription_medical:
      "<p>You need to provide your completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link>.</p><p>Your certification documents will be shared with your employer as part of your leave application.</p>",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul><li>If you will use any benefits from your employer because you are taking leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any leave you’ve taken since January 1, 2021 for a condition that is covered by Paid Family and Medical Leave.</li></ul>",
    stepHTMLDescription_payment:
      "<p>Tell us how you want to receive payment.</p><p>If you want to receive payment by direct deposit, you will need to provide your bank account information, including a routing number and account number.</p>",
    stepHTMLDescription_reviewAndConfirm:
      "<p>Once you confirm your leave information, we’ll notify your employer. Your job will be protected. To complete your application, you will need to finish the following three steps and submit.</p><p>If you need to edit your information in Part 1 after completing this step, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    stepHTMLDescription_uploadId:
      "<p>Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same$t(chars.nbsp)ID.</p><p>For other IDs, follow the instructions for acceptable proof of identity on the upload page.</p>",
    stepHTMLDescription_verifyId:
      "<p>You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card.</p><p>You will need to provide:</p><ul><li>Your name as it appears on your ID.</li><li>Your driver’s license number or Mass ID number, if you have one.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListDescription_1:
      "Your progress is automatically saved as you complete the application. You can edit any information you enter in Part 1 until step 5 is completed.",
    stepListDescription_1_submitted:
      "If you need to edit your information in Part 1, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_2:
      "Entering payment information here leads to faster processing, but you can also call$t(chars.nbsp)<contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    stepListDescription_2_submitted:
      "If you need to edit your information in Part 2, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
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
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hintWhatKindBody:
      "<p>This includes any paid vacation time, sick time, and personal time. It should be reported if it’s taken during your leave period, whether it’s during the 7-day waiting period or after. Reminder: you can use accrued paid leave during the 7-day waiting period with no impact to your PFML benefit.</p>",
    hintWhatKindHeading: "What kinds of accrued paid leave to report",
    hintWhenToReportBody:
      "<p>If your PFML leave includes taking time off work completely for a period of time (continuous leave), you need to report any accrued paid leave you plan to take during that continuous leave. Select Yes to report this leave.</p><p>If your PFML leave includes working fewer hours than normal (a reduced leave schedule) or taking time off work in uneven or unpredictable blocks of time (intermittent leave), you need to report leave if ONE of the following two statements is true:</p><ul><li>You are planning to use this accrued paid leave on days when you are also taking PFML leave.</li><li>You are planning to use this accrued paid leave for a PFML qualifying reason, even if it’s not the same reason you are applying for now.</li></ul>",
    hintWhenToReportDetailsBody:
      "<ul><li>You had a serious health condition, including illness, injury, or pregnancy.</li><li>If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care.</li><li>You bonded with your child after birth or placement.</li><li>You needed to manage family affairs while a family member is on active duty in the armed forces.</li><li>You needed to care for a family member who serves in the armed forces.</li><li>You needed to care for a family member with a serious health condition.</li></ul>",
    hintWhenToReportDetailsLabel: "What are the qualifying reasons?",
    hintWhenToReportHeading: "When you need to report it",
    sectionLabel:
      "Will you use any employer-sponsored accrued paid leave during your paid leave from PFML?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsConcurrentLeavesDetails: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hintHeader:
      "This is the same Employer Identification Number you entered earlier in your application. After you submit your application, this employer will be able to review it. We won’t share any leave you plan to take from other employers.",
    leaveEndDateLabel: "What is the last day of this leave?",
    leaveStartDateLabel: "What is the first day of this leave?",
    sectionLabel:
      "Will you use accrued paid leave from this employer? EIN: {{employer_fein, ein}}",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsConcurrentLeavesIntro: {
    intro:
      "<p>Next, we need to know about paid leave from your employer that you plan to use between {{startDate}} and {{endDate}}. This includes paid vacation time, sick time, personal time, and other paid time off provided by your employer. It does not include family or medical leave provided by your employer, or through a short- or long-term disability program. We’ll ask about that later.</p><p>When your PFML leave begins, there is a 7-day waiting period before PFML payments start. During this 7-day waiting period, you can use paid time off from your employer with no impact to your PFML benefit.</p><p>After the 7-day waiting period, you cannot use both paid leave from your employer and paid leave from PFML on the same days. In some cases, using accrued paid leave after the 7-day waiting period has ended can cause your PFML benefits to stop. You will need to re-apply to receive PFML benefits again. To avoid this, use accrued paid leave only at the start or end of your PFML leave.</p>",
    sectionLabel:
      "Tell us about the accrued paid leave you'll use during your paid leave from PFML.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsDateOfBirth: {
    sectionLabel: "What’s your date of birth?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsEmployerBenefits: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hintBody:
      "<p>This does not include PFML benefits. You only have to report benefits from the employer with this EIN: {{employer_fein}}. This is the same Employer Identification Number you entered earlier in your application.</p><p>If you won’t use these benefits from this employer, select No.</p>",
    hintHeader: "The employer-sponsored benefits you must report are:",
    hintList: [
      "Temporary disability insurance, for either short-term or long-term disability",
      "Permanent disability insurance",
      "Family or medical leave benefits, such as a parental leave program",
    ],
    sectionLabel:
      "Will you use any employer-sponsored benefits from this employer during your paid leave from PFML?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsEmployerBenefitsDetails: {
    addButton: "Add another benefit",
    amountFrequencyLabel: "$t(shared.amountFrequencyLabel)",
    amountFrequency_daily: "$t(shared.amountFrequency_daily)",
    amountFrequency_inTotal: "$t(shared.amountFrequency_inTotal)",
    amountFrequency_monthly: "$t(shared.amountFrequency_monthly)",
    amountFrequency_unknown: "$t(shared.amountFrequency_unknown)",
    amountFrequency_weekly: "$t(shared.amountFrequency_weekly)",
    amountLabel: "Amount",
    amountLegend: "How much will you receive?",
    cardHeadingPrefix: "$t(shared.employerBenefitEntryPrefix)",
    choiceHint_familyOrMedicalLeave:
      "$t(shared.choiceHint_familyOrMedicalLeave)",
    choiceHint_paidLeave:
      "For example, vacation time, sick leave, or personal time",
    choiceHint_shortTermDisability: "$t(shared.choiceHint_shortTermDisability)",
    choiceLabel_familyOrMedicalLeave:
      "$t(shared.employerBenefitType_familyOrMedicalLeave)",
    choiceLabel_no: "$t(shared.choiceNo)",
    choiceLabel_paidLeave: "$t(shared.employerBenefitType_paidLeave)",
    choiceLabel_permanentDisability:
      "$t(shared.employerBenefitType_permanentDisability)",
    choiceLabel_shortTermDisability:
      "$t(shared.employerBenefitType_shortTermDisability)",
    choiceLabel_yes: "$t(shared.choiceYes)",
    endDateLabel:
      "What is the last day of leave from work that this benefit will pay you for?",
    isFullSalaryContinuousLabel:
      "Does this employer-sponsored benefit fully replace your wages?",
    limitMessage: "You can only add up to {{limit}} benefits",
    removeButton: "Remove benefit",
    sectionLabel:
      "Tell us about employer-sponsored benefits you will use during your leave dates for paid leave from PFML.",
    startDateLabel:
      "What is the first day of leave from work that this benefit will pay you for?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeLabel: "What kind of employer-sponsored benefit is it?",
  },
  claimsEmployerBenefitsIntro: {
    intro:
      "<p>Next, we need to know about any other employer-sponsored benefits you'll use or other sources of income you'll receive during your PFML paid leave period. We can determine your PFML benefit amount once we have this information.</p><p>An employer-sponsored benefit is a policy provided by your employer that provides you income while you can’t work. This includes temporary disability insurance, permanent disability insurance, and a family or medical leave policy.</p>",
    sectionLabel:
      "Tell us about other benefits and income you will use during your paid leave from PFML.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsEmploymentStatus: {
    alertBody:
      "<p>If you’re self-employed or unemployed, apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>You can apply online if you’re currently employed in Massachusetts.</p>",
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
    detailsBody:
      "<p>You can apply to care for someone who served in <in-loco-parentis-link>loco parentis</in-loco-parentis-link> (acted as a parent) for you. In that case, choose “I am caring for my parent.”</p><p>If you served in loco parentis for the family member you’re caring for, choose “I am caring for my child.”</p><p>If none of the options listed below describe your relationship with the person you're caring for, you are not eligible to take paid family leave. If you’d still like to submit an application or if you have questions about whether your relationship qualifies, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    detailsLabel:
      "What if I don’t see my relationship with the family member I’m caring for on this list?",
    sectionHint:
      "<p>Learn more about <caregiver-relationship-link>which relationships are covered</caregiver-relationship-link>.</p>",
    sectionLabel:
      "What is your relationship with the family member you are caring for?",
  },
  claimsGender: {
    choiceGenderNotListed: "$t(shared.genderGenderNotListed)",
    choiceMan: "$t(shared.genderMan)",
    choiceNonbinary: "$t(shared.genderNonbinary)",
    choicePreferNotToAnswer: "$t(shared.genderPreferNotToAnswer)",
    choiceWoman: "$t(shared.genderWoman)",
    genderIdLabel: "Gender selection",
    sectionLabel: "What is your gender identity?",
    sectionLabelHint:
      "This data helps us understand who is accessing our program to ensure it is built for everyone.",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsIntermittentFrequency: {
    durationBasisChoice_days: "At least one day",
    durationBasisChoice_hours: "Less than one full work day",
    durationBasisLabel: "How long will an absence typically last?",
    durationLabel_days: "How many days of work will you miss per absence?",
    durationLabel_hours: "How many hours of work will you miss per absence?",
    frequencyBasisChoice_irregular: "Irregular over the next 6 months",
    frequencyBasisChoice_months: "Once or more per month",
    frequencyBasisChoice_weeks: "Once or more per week",
    frequencyBasisLabel:
      "How often might you need to be absent from work (frequency interval)?",
    frequencyHint_care:
      "Your answers must match the intermittent leave section in the $t(shared.certificationFormCare).",
    frequencyHint_medical:
      "Your answers must match the intermittent leave section in the $t(shared.certificationFormMedical).",
    frequencyHint_pregnancy:
      "Your answers must match the intermittent leave section in the $t(shared.certificationFormMedical).",
    frequencyHint_updateMedicalCertForm:
      "Your answers must match Questions 21 and 22 in the $t(shared.certificationFormMedical).",
    frequencyLabel_irregular:
      "Estimate how many absences over the next 6 months.",
    frequencyLabel_months: "Estimate how many absences per month.",
    frequencyLabel_weeks: "Estimate how many absences per week.",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    needDocumentAlert_pregnancy: "$t(shared.leavePeriodMedicalAlert)",
    sectionLabel:
      "Tell us the estimated frequency and duration of your intermittent$t(chars.nbsp)leave.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodContinuous: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the continuous leave period start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodContinuousDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodContinuousDatesLeadMedicalOrPregnancy)",
    datesLead_updateMedicalCertForm:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 16 in the $t(shared.certificationFormMedical).",
    datesSectionLabel:
      "Enter the start and end dates for your continuous leave.",
    endDateLabel: "Last day of leave",
    hasLeaveHint_care: "$t(shared.leavePeriodHasLeaveHintCare)",
    hasLeaveHint_medical:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_pregnancy:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_updateMedicalCertForm:
      "$t(shared.leavePeriodHasLeaveHintUpdateMedicalCertForm)",
    hasLeaveLabel:
      "Do you need to take off work completely for a period of time (continuous leave)?",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    needDocumentAlert_pregnancy: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodIntermittent: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the intermittent leave start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodIntermittentDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodIntermittentDatesLeadMedicalOrPregnancy)",
    datesLead_updateMedicalCertForm:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 20 in the $t(shared.certificationFormMedical).",
    datesSectionLabel:
      "Enter the start and end dates for your intermittent leave.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical: "Last day of leave",
    hasLeaveHint_bonding:
      "For example, you need to take time off for: <ul><li>Court dates for your foster child</li><li>Social worker visits</li><li>Gaps in your childcare</li></ul>",
    hasLeaveHint_care: " $t(shared.leavePeriodHasLeaveHintCare)",
    hasLeaveHint_medical:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_pregnancy:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_updateMedicalCertForm:
      "$t(shared.leavePeriodHasLeaveHintUpdateMedicalCertForm)",
    hasLeaveLabel:
      "Do you need to take off work in uneven blocks of time (<scheduling-leave-guide-link>intermittent leave</scheduling-leave-guide-link>)?",
    hybridLeaveWarning:
      "You have to create a separate application for intermittent leave.",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    needDocumentAlert_pregnancy: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeavePeriodReducedSchedule: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    datesLead_bonding:
      "If you have already taken some or all of your family leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your paid leave must end before the child’s first birthday or the one year anniversary of when they arrived in your home (for foster care and adoption).",
    datesLead_care:
      "If you have already taken some or all of your leave in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match the reduced leave start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodReducedDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodReducedDatesLeadMedicalOrPregnancy)",
    datesLead_updateMedicalCertForm:
      "If you have already taken leave for this condition in 2021, tell us the first day you missed work this year, and the last day you expect to be on leave.<br /><br />Your answer must match Question 18 in the $t(shared.certificationFormMedical).",
    datesSectionLabel:
      "Enter the start and end dates for your reduced leave schedule.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical: "Last day of leave",
    hasLeaveHint_care: "$t(shared.leavePeriodHasLeaveHintCare)",
    hasLeaveHint_medical:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_pregnancy:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_updateMedicalCertForm:
      "$t(shared.leavePeriodHasLeaveHintUpdateMedicalCertForm)",
    hasLeaveLabel:
      "Do you need to work fewer hours than usual for a period of time (<scheduling-leave-guide-link>reduced leave schedule</scheduling-leave-guide-link>)?",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    needDocumentAlert_pregnancy: "$t(shared.leavePeriodMedicalAlert)",
    startDateLabel: "First day of leave",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsLeaveReason: {
    activeDutyFamilyLeaveLabel:
      "I need to manage family affairs while a family member is on active duty in the armed forces.",
    alertBody:
      "<p>To apply for the following paid benefits:</p><ul><li>Paid family leave to care for a family member who serves in the armed forces</li><li>Paid family leave to manage family affairs when a family member is on active duty in the armed forces</li></ul><p>Call the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
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
    caringLeaveLabel: "I need to care for my family member.",
    leaveReasonChangedAlertBody:
      "Earlier you reported taking previous leave for the same reason you are applying now, but you are about to change that reason.<br/><br/>Save and continue to change your leave reason, then review the previous leave you reported to make sure the reason you took that leave is still accurate.",
    leaveReasonChangedAlertTitle: "Review your previous leave",
    medicalLeaveLabel: "I can’t work due to my illness, injury, or pregnancy.",
    sectionHint: "You can only request one leave at a time.",
    sectionLabel: "Why do you need to take leave?",
    serviceMemberFamilyLeaveLabel:
      "I need to care for a family member who serves in the armed forces.",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsName: {
    firstNameLabel: "First name",
    lastNameLabel: "Last name",
    lead: "Fill out your name as it appears on official documents like your driver’s license or W$t(chars.nbhyphen)2.",
    middleNameLabel: "Middle name",
    sectionLabel: "What’s your name?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsNotifiedEmployer: {
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
    choiceNoHint:
      "I won't receive other income, or I've applied but it hasn't been approved.",
    choiceYes: "$t(shared.choiceYes)",
    hintAppliedButNotApprovedDetailsBody:
      "You only need to report sources of income that you know you will receive. If you have applied but you haven’t been approved yet, you don’t need to report that.<br/><br/>If you won’t receive income from any other sources on this list, select No.<br/><br/>If you are approved later, you will need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    hintAppliedButNotApprovedDetailsLabel:
      "What if I’ve applied for other income but I haven’t been approved yet?",
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
    amountFrequencyLabel: "$t(shared.amountFrequencyLabel)",
    amountFrequency_daily: "$t(shared.amountFrequency_daily)",
    amountFrequency_inTotal: "$t(shared.amountFrequency_inTotal)",
    amountFrequency_monthly: "$t(shared.amountFrequency_monthly)",
    amountFrequency_weekly: "$t(shared.amountFrequency_weekly)",
    amountLabel: "Amount",
    amountLegend: "How much will you receive?",
    cardHeadingPrefix: "$t(shared.otherIncomeEntryPrefix)",
    endDateLabel:
      "What is the last day of your leave that this income will pay you for?",
    limitMessage: "You can only add up to {{limit}} incomes",
    removeButton: "Remove income",
    sectionLabel:
      "Tell us about your other sources of income during your leave dates for paid leave from PFML.",
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
      "<p>Once you submit Part 2, your payment information will be viewable by our Contact Center staff. To make edits to Part 2, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>Next, you’ll work on Part 3, and submit your application.</p>",
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
    lead: "If we need to contact you, we will reach out by phone or mail. We will also use this number for any previous applications you have submitted.",
    phoneNumberHint:
      "Don’t have a personal phone number? Enter a number where we might be able to reach you (for example, a work phone number, or a friend’s phone number).",
    phoneNumberLabel: "Phone number",
    phoneTypeLabel: "Number type",
    sectionLabel: "What’s your phone number?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsPreviousLeavesIntro: {
    intro:
      "<p>In this section, we need to know about some other leave you may have taken between January 1, 2021 and {{startDate}}:</p><ul><li>Any previous leave for the same reason that you are applying for paid leave now</li><li>Any previous leave for a different reason that also qualifies under PFML</li></ul>",
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
      "You needed to care for a family member with a serious health condition and your leave began on or after July 1, 2021.",
    ],
    sectionLabel:
      "Did you take leave between January 1, 2021 and {{leaveStartDate}} for a different qualifying reason?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesOtherReasonDetails: {
    addButton: "$t(shared.claimsPreviousLeaveDetails.addButton)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hoursLabel: "$t(shared.hoursLabel)",
    isForCurrentEmployerHint:
      "$t(shared.claimsPreviousLeaveDetails.isForCurrentEmployerHint)",
    isForCurrentEmployerLabel:
      "$t(shared.claimsPreviousLeaveDetails.isForCurrentEmployerLabel)",
    leaveEndDateLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveEndDateLabel)",
    leaveMinutesHint: "$t(shared.claimsPreviousLeaveDetails.leaveMinutesHint)",
    leaveMinutesLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveMinutesLabel)",
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
    leaveStartDateLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveStartDateLabel)",
    limitMessage: "$t(shared.claimsPreviousLeaveDetails.limitMessage)",
    minutesLabel: "$t(shared.minutesLabel)",
    previousLeaveEntryPrefix: "$t(shared.previousLeaveEntryPrefix)",
    removeButton: "$t(shared.claimsPreviousLeaveDetails.removeButton)",
    sectionHint: "$t(shared.claimsPreviousLeaveDetails.sectionHint)",
    sectionLabel: "$t(shared.claimsPreviousLeaveDetails.sectionLabel)",
    title: "$t(shared.claimsOtherLeaveTitle)",
    workedPerWeekMinutesDetails:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesDetails)",
    workedPerWeekMinutesDetailsLabel:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesDetailsLabel)",
    workedPerWeekMinutesHint:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesHint)",
    workedPerWeekMinutesLabel:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesLabel)",
  },
  claimsPreviousLeavesSameReason: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    sectionHint:
      "Select No if your current paid leave from PFML began on July 1, 2021.",
    sectionLabel:
      "Did you take any other leave between {{previousLeaveStartDate}} and {{leaveStartDate}} for the same reason as you are applying for paid leave now?",
    sectionLabel_caring:
      "Did you take any other leave between {{previousLeaveStartDate}} and the first day of the leave you are applying for, for the same reason as you are applying?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesSameReasonDetails: {
    addButton: "$t(shared.claimsPreviousLeaveDetails.addButton)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hoursLabel: "$t(shared.hoursLabel)",
    isForCurrentEmployerHint:
      "$t(shared.claimsPreviousLeaveDetails.isForCurrentEmployerHint)",
    isForCurrentEmployerLabel:
      "$t(shared.claimsPreviousLeaveDetails.isForCurrentEmployerLabel)",
    leaveEndDateLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveEndDateLabel)",
    leaveMinutesHint: "$t(shared.claimsPreviousLeaveDetails.leaveMinutesHint)",
    leaveMinutesLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveMinutesLabel)",
    leaveStartDateLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveStartDateLabel)",
    limitMessage: "$t(shared.claimsPreviousLeaveDetails.limitMessage)",
    minutesLabel: "$t(shared.minutesLabel)",
    previousLeaveEntryPrefix: "$t(shared.previousLeaveEntryPrefix)",
    removeButton: "$t(shared.claimsPreviousLeaveDetails.removeButton)",
    sectionHint: "$t(shared.claimsPreviousLeaveDetails.sectionHint)",
    sectionLabel: "$t(shared.claimsPreviousLeaveDetails.sectionLabel)",
    title: "$t(shared.claimsOtherLeaveTitle)",
    workedPerWeekMinutesDetails:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesDetails)",
    workedPerWeekMinutesDetailsLabel:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesDetailsLabel)",
    workedPerWeekMinutesHint:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesHint)",
    workedPerWeekMinutesLabel:
      "$t(shared.claimsPreviousLeaveDetails.workedPerWeekMinutesLabel)",
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
    lead: "Enter 0 for days you won’t work a reduced schedule.",
    leadCertGuidance_care:
      "The total number of hours you enter must match the reduced leave schedule section in the $t(shared.certificationFormCare).",
    leadCertGuidance_medical:
      "$t(shared.reducedLeaveScheduleLeadCertGuidanceMedicalOrPregnancy)",
    leadCertGuidance_pregnancy:
      "$t(shared.reducedLeaveScheduleLeadCertGuidanceMedicalOrPregnancy)",
    leadCertGuidance_updateMedicalCertForm:
      "The total number of hours you enter must match Question 19 in the $t(shared.certificationFormMedical).",
    minutesLabel: "$t(shared.minutesLabel)",
    needDocumentAlert_care: "$t(shared.leavePeriodCaringAlert)",
    needDocumentAlert_medical: "$t(shared.leavePeriodMedicalAlert)",
    needDocumentAlert_pregnancy: "$t(shared.leavePeriodMedicalAlert)",
    sectionLabel:
      "How many hours will you take off while you are on a reduced leave schedule?",
    title: "$t(shared.claimsLeaveDetailsTitle)",
    workPatternVariableTime: "$t(shared.displayTime) per week",
    workPatternVariableTime_noMinutes:
      "$t(shared.displayTime_noMinutes) per week",
    workScheduleToggle: "View your work schedule",
  },
  claimsReview: {
    achTypeLabel: "Account type",
    achType_checking: "$t(shared.achTypeChecking)",
    achType_savings: "$t(shared.achTypeSavings)",
    amountPerFrequency_daily: "$t(shared.amountPerFrequency_daily)",
    amountPerFrequency_inTotal: "$t(shared.amountPerFrequency_inTotal)",
    amountPerFrequency_monthly: "$t(shared.amountPerFrequency_monthly)",
    amountPerFrequency_unknown: "",
    amountPerFrequency_weekly: "$t(shared.amountPerFrequency_weekly)",
    childBirthDateLabel: "Child’s date of birth",
    childPlacementDateLabel: "Child’s placement date",
    concurrentLeaveHasConcurrentLeaveLabel: "Concurrent leave?",
    concurrentLeaveLabel: "Accrued paid leave",
    documentsLoadError: "$t(shared.documentsLoadError)",
    editLink: "Edit",
    employerBenefitEntryLabel:
      "$t(shared.employerBenefitEntryPrefix) {{count}}",
    employerBenefitIsFullSalaryContinuous: "Full wage replacement",
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
    familyMemberRelationship_inlaw: "Parent of spouse or domestic partner",
    familyMemberRelationship_parent: "Parent",
    familyMemberRelationship_serviceMember: "Service Member",
    familyMemberRelationship_sibling: "Sibling",
    familyMemberRelationship_spouse: "Spouse or domestic partner",
    genderValue_genderNotListed: "$t(shared.genderGenderNotListed)",
    genderValue_man: "$t(shared.genderMan)",
    genderValue_nonbinary: "$t(shared.genderNonbinary)",
    genderValue_preferNotToAnswer: "$t(shared.genderPreferNotToAnswer)",
    genderValue_woman: "$t(shared.genderWoman)",
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
    isForCurrentEmployer_false: "From a different employer",
    isForCurrentEmployer_true: "From this employer",
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
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    mailingAddressLabel: "Mailing address",
    missingRequiredFieldError:
      "We’ve added some new questions since you last updated your application. Return to the <checklist-link>checklist</checklist-link> to make sure you’ve completed every step.",
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
    otherLeaveChoiceYes: "$t(shared.choiceYes)",
    otherLeaveDollarAmount: "{{amount, currency}}",
    partDescription_1:
      "If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>",
    partHeadingPrefix: "Part {{number}}",
    partHeading_1_final:
      "Review: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_1_part1:
      "Review and confirm: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_2: "Review: Your payment information",
    partHeading_3: "Review: Upload document",
    partOneNextSteps:
      "<p>Once you review and submit Part 1, your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>We’ll also notify your employer that you’ve started an application for paid family and medical leave.</p><p>Next, you’ll be able to work on Parts 2 and 3, and submit your application.</p>",
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
    previousLeaveHasPreviousLeavesLabel: "Previous leave?",
    previousLeaveLabel: "Previous paid or unpaid leave?",
    previousLeaveLeaveMinutes: "$t(shared.displayTime)",
    previousLeaveLeaveMinutesLabel: "Total hours of leave taken: ",
    previousLeaveLeaveMinutes_noMinutes: "$t(shared.displayTime_noMinutes)",
    previousLeaveReason_activeDutyFamily:
      "Leave was for managing family affairs while a family member was on active duty in the armed forces",
    previousLeaveReason_bonding:
      "Leave was for bonding with a child after birth or placement",
    previousLeaveReason_care: "Leave was for caring for a family member",
    previousLeaveReason_medical: "Leave was for an illness or injury",
    previousLeaveReason_pregnancy: "Leave was for a pregnancy",
    previousLeaveReason_serviceMemberFamily:
      "Leave was for caring for a family member who serves in the armed forces",
    previousLeaveType_otherReason: "Leave for a different qualifying reason",
    previousLeaveType_sameReason: "Leave for the same qualifying reason",
    previousLeaveWorkedPerWeekMinutes: "$t(shared.displayTime)",
    previousLeaveWorkedPerWeekMinutesLabel: "Hours worked at time of leave: ",
    previousLeaveWorkedPerWeekMinutes_noMinutes:
      "$t(shared.displayTime_noMinutes)",
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
    userGenderLabel: "Gender Identity",
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
    lead: "We’ll confirm your hours with your employer after you submit your application. Learn more about <calculate-hours-link>how we use this number</calculate-hours-link> and how to figure out your average.",
    minutesLabel: "$t(shared.minutesLabel)",
    title: "$t(shared.claimsEmploymentInfoTitle)",
  },
  claimsSsn: {
    lead: "Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number (ITIN).",
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
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of placement, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child arrived in your home earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    adjudicationProcess_bondingNewbornFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of birth, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child was born earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    adjudicationProcess_caringLeave:
      "<ul><li>Your employer has 10 business days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision. Your employer will also get a copy of the decision.</li><li>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started. If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts. After that, you will receive your payments every week.</li><li>If you need to end your leave early, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li></ul>",
    adjudicationProcess_medicalPregnantFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>When your leave begins, call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to tell us. Then we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li></ul>",
    claimantApplicationId:
      "Your application ID is <strong>{{absence_id}}</strong>",
    exitLink: "Return to applications",
    familyLeaveToBond:
      "You can take up to 12 weeks of paid family leave to bond with your child after your medical leave ends. Family leave to bond with your child can be <medical-bonding-link>easily added to your claim</medical-bonding-link> by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    familyLeaveToBondHeading: "You may also be eligible for paid family leave",
    medicalLeaveAfterBirth:
      "You can take up to 20 weeks of paid medical leave if you’re unable to work during your pregnancy and to recover from childbirth. Your health care provider determines how much medical leave you will need. Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if you need <medical-bonding-link>medical leave after giving birth</medical-bonding-link>.",
    medicalLeaveAfterBirthHeading:
      "If you gave birth, you may also be eligible for paid medical leave",
    proofRequired_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to upload, mail, or fax a document that shows your child’s placement date.",
    proofRequired_bondingNewbornFuture:
      "After your child is born, you will need to upload, mail, or fax a document that shows your child’s date of birth.",
    proofRequired_medicalPregnantFuture:
      "You must call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> once your medical leave begins to confirm that your leave has begun. We can’t approve your application until we hear from$t(chars.nbsp)you.",
    reportReductionsHeading: "We may need more information from you",
    reportReductionsMessage:
      "<p>Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if any of these are true:</p><ul><li>You have already taken leave to care for a family member since July 1, 2021</li><li>You have already taken leave since January 1, 2021 for <when-can-i-use-pfml>any other reason that qualifies for PFML</when-can-i-use-pfml></li><li>You plan to use any accrued paid leave or any other benefits from your employer during your paid leave from PFML (for example: your employer’s parental leave program or paid sick time)</li><li>You expect to get income from any other sources during your leave (for example: disability insurance, retirement benefits, or another job)</li></ul>",
    reportReductionsProcess:
      "<p>Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if you’ll receive:</p><ul><li>Any <reductions-employer-benefits-link>benefits from your employer</reductions-employer-benefits-link> that you’ll be using in addition to Massachusetts paid leave (for example, maternity leave, or paid sick time)</li><li>Income from <reductions-overview-link>any other sources</reductions-overview-link> during your leave</li></ul>",
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
      "You need to upload a completed <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> to prove that you need to take leave to care for a family member with a serious medical condition.",
    lead_medical:
      "You need to upload a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link> to prove that you need to take medical leave.",
    sectionLabel: "Upload your certification form",
    sectionLabel_bonding: "Upload your documentation",
    title: "Upload certification",
  },
  claimsUploadDocsOptions: {
    certLabel_bonding_adopt_foster: "Proof of placement",
    certLabel_bonding_newborn: "Proof of birth",
    certLabel_care: "$t(shared.certificationFormCare)",
    certLabel_medical: "$t(shared.certificationFormMedical)",
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
  convertToEmployer: {
    alertDescription:
      'Converting your account from "employee" to "employer" is irreversible and will not be possible if any claims have been created, are in-progress, or are completed.',
    alertHeading: "This action is irreversible!",
    einHint:
      "Your Employer Identification Number is a <ein-link>9-digit number</ein-link> assigned by the Internal Revenue Service. It is listed on tax returns and your payroll department should have this information.",
    einLabel: "Employer ID number (EIN)",
    submit: "Convert account",
    title: "Convert to employer account",
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
    leadMultipleCompanies:
      "If you manage leave for multiple companies, please create an account for one using the form below. You’ll be able to add more companies to your account in the portal.",
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
    lead: "Please verify your email address. If an account exists for the email you provide, you’ll receive a 6-digit verification code. After that, you’ll be prompted to create a new password.",
    submitButton: "Submit",
    title: "Finish setting up your account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  employersCannotVerify: {
    body: "We can't verify this account because this organization hasn't submitted contributions through MassTaxConnect. Call the Department of Revenue at <dor-phone-link>$t(shared.departmentOfRevenuePhoneNumber)</dor-phone-link> to make arrangements to submit contributions. Once you do that, you'll be able to review leave applications on the next business day. Learn more about <learn-more-link>verifying your account</learn-more-link> on Mass.gov.",
    companyNameLabel: "<strong>Organization:</strong> {{employerDba}}",
    employerIdNumberLabel:
      "<strong>Employer ID number (EIN):</strong> {{employerFein}}",
    title: "We can't verify this organization",
  },
  employersClaimsConfirmation: {
    applicationIdLabel: "<strong>Application ID:</strong> {{absenceId}}",
    instructions:
      "<p>Thanks for letting us know that you’re not the right person to review this.</p><ul><li>Please check with your human resources team and your colleagues to see who should respond.</li><li>If the right person at your company already has an employer account, they received the same email you did and can respond directly.</li><li>Otherwise, please ask them to call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li></ul>",
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
      "Please review the details of this application carefully. If anything is incorrect or incomplete, you can add an amendment or include specific comments at the end. Changes are not saved until you submit your review.",
    instructionsFollowUpDate: "$t(shared.employerInstructions_followUpDate)",
    organizationNameLabel: "Organization",
    otherLeavesBody:
      "<p>Please review the leaves and benefits listed in the tables below. If everything looks correct, then there’s no action needed. If something looks incorrect or incomplete, you can:</p><ul><li>Amend reported leaves and benefits.</li><li>Add a leave or benefit that your employee used or will use.</li></ul><p>If you need to remove a leave or benefit, use the comment box at the end of this page.</p>",
    otherLeavesBodyV1:
      "<p>Please review the benefits listed below. If everything looks correct, then there’s no action needed. If something looks incorrect or incomplete, you can amend it. If you need to remove or add a benefit, use the comment box at the end of this page.</p>",
    otherLeavesSummaryBoxBody:
      "<ul><li>Previous leave for a qualifying reason that they took before their paid leave from PFML</li><li>Accrued paid leave they plan to use during their paid leave from PFML</li><li>Employer-sponsored benefits they plan to use during their paid leave from PFML</li></ul>",
    otherLeavesSummaryBoxTitle: "Employees are asked to report:",
    otherLeavesTitle: "Other leaves and benefits",
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
    leaveReasonValue_care: "$t(shared.leaveReasonCare)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
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
    betaHeader: "We're making it easier to manage paid leave applications",
    betaMessage:
      "Our dashboard is in beta. You can now see all the applications you need to review using our new dashboard. Over the next few months, we'll be adding more features to the dashboard so you can easily find and manage paid leave applications. You can <user-feedback-link>use our feedback form</user-feedback-link> to tell us what you think of our new features.",
    filterNavLabel: "Filters:",
    filterOrgsLabel: "Organizations",
    filterRemove: "Remove filter:",
    filterStatusChoice_Approved: "$t(shared.absenceCaseStatus_approved)",
    filterStatusChoice_Closed: "$t(shared.absenceCaseStatus_closed)",
    filterStatusChoice_Declined: "$t(shared.absenceCaseStatus_denied)",
    filterStatusChoice_Pending: "--",
    filterStatusLabel: "Status",
    filtersApply: "Apply filters",
    filtersReset: "Reset all filters",
    filtersShowWithCount: "Show filters ({{count}})",
    filtersToggle: "Show filters",
    filtersToggle_expanded: "Hide filters",
    instructions:
      "Applications will not have a status until the Department has made a decision. Applications that don't have a status may require action from you.",
    noClaimResults: "No applications on file",
    searchLabel: "Search for employee name or application ID",
    searchSubmit: "Search",
    sortChoice_employee_az: "Last name – A to Z",
    sortChoice_employee_za: "Last name – Z to A",
    sortChoice_newest: "Newest applications",
    sortChoice_oldest: "Oldest applications",
    sortLabel: "Sort",
    startDateTooltip: "When an employee started a new leave application",
    statusDescription_approved:
      "<strong>Approved:</strong> DFML has approved this leave request.",
    statusDescription_closed:
      "<strong>Closed:</strong> The leave has passed or no action can be taken.",
    statusDescription_denied:
      "<strong>Denied:</strong> DFML has denied this leave request.",
    statusDescription_noAction:
      "<strong>No action required:</strong> This leave request is awaiting a decision from DFML.",
    statusDescription_none:
      "<strong>“--” or no status:</strong> This leave request may require action from you; otherwise, it is awaiting a decision from DFML.",
    statusDescription_reviewBy:
      "<strong>Review by:</strong> Review this application by this date to provide DFML with your input.",
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
    convertDescription: "Your account type is now converted.",
    convertHeading: "Success",
    einTableHeader: "Employer ID number (EIN)",
    nearFutureAvailability:
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
      "Log into <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> or contact your payroll department to complete these steps:<ol><li>On the <strong>Summary</strong> page, scroll down to the <strong>Paid Family and Medical Leave</strong> section on the left. In the <strong>Account</strong> portion, select <strong>Returns</strong>.</li><li>Choose <strong>the last period</strong> for which a return has been <strong>received</strong>. For example, if you remitted your contributions for 3-31-2021, and the return has been processed and designated as ‘received’, you can use the amount from that period to verify your account. If you have not yet remitted your contributions or it is still being processed, use the amount from the most recent period for which you filed that has been processed.</li><li>Go into the return. Click <strong>View or Amend Return</strong>. Then select <strong>Next</strong> at the bottom. Look to <strong>line 6</strong> and you will find the <strong>Total Contributions Due</strong>.</li><li>Copy the <strong>Total Contributions Due</strong> amount for verification.</li></ol>If you have any questions about your paid leave contributions, please contact the Department of Revenue at <dor-phone-link><strong>$t(shared.departmentOfRevenuePhoneNumber)</strong></dor-phone-link> from 9am-4pm ET.",
    employerIdNumberLabel: "<strong>Employer ID number (EIN):</strong> {{ein}}",
    haveAnAccount: "Have an account? <log-in-link>Log in</log-in-link>",
    lead: "We need more information to verify your identity. We require every employer to verify recent <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> data when creating an account. This helps protect your employees and your company information.",
    submitButton: "Submit",
    title: "Verify your paid leave contributions from MassTaxConnect",
    withholdingAmountHint: "Include the full amount with dollars and cents.",
    withholdingAmountLabel: "Paid leave contributions from {{date}}",
  },
  employersWelcome: {
    caringLeaveInfoAlertBody:
      "Employees can now take <about-caring-leave-link>paid leave to care for a family member with a serious health condition</about-caring-leave-link>. If your employee applies for this kind of leave, you’ll notice different documents available for your review.",
    checkEmailBody:
      "When an employee applies for leave, you’ll receive email updates about their application status and any steps you need to take. We’ll include everyone who has an employer account with your company in case you’re out of the office.",
    checkEmailTitle: "Check your email regularly",
    learnMoreLinks:
      "<ul><li><mass-employer-role-link>Your role as a Massachusetts employer</mass-employer-role-link></li><li><reimbursements-link>Employer reimbursements</reimbursements-link></li></ul>",
    learnMoreTitle: "Learn more",
    otherLeaveInfoAlertBody:
      "The Department of Family and Medical Leave has updated the Review page. Employees can now report other leaves and benefits in their paid leave application. If your employee reported other leaves or benefits, you can review the information provided, and add any that they missed.",
    respondBody:
      "When an application is submitted, you have 10 business days to open the direct link from your email and review it online. You can comment on the application, approve or deny it, and report fraud if needed. Reviewing takes about 10 minutes. If we don’t hear from anyone at your company before the deadline, we’ll process the application solely based on the information the employee provided.",
    respondTitle: "Respond to applications within 10 business days",
    settingsLink: "Your organizations",
    settingsTitle: "Settings",
    verificationAlertBody:
      "We require every employer to verify paid leave contributions when creating an account. You need to <your-organizations-link>complete this process</your-organizations-link> to review applications from your team.",
    verificationAlertTitle: "Verify your account to continue",
    viewApplicationsBody:
      "When you log into your account you can now use the <dashboard-link>dashboard</dashboard-link> to see all the applications submitted by employees from your organization.",
    viewApplicationsTitle: "View all applications",
    viewFormsBody:
      "You’ll get an email about our application decision with a direct link to download the letter your employee received. For medical leave, you can download the <healthcare-provider-form-link>$t(shared.certificationFormMedical) form</healthcare-provider-form-link> during the review process. For leave to care for a family member you can download the <caregiver-certification-form-link>Certification to Care for a Family Member</caregiver-certification-form-link> during the review process. ",
    viewFormsTitle: "View forms and notices online",
    welcomeBody:
      "Thanks for joining the paid leave program. Massachusetts workers can now apply for paid family and medical leave.",
    welcomeTitle: "Welcome",
  },
  getReady: {
    alertHeading: "Only some people can apply online for now",
    alertOnline:
      "<p>If you are currently employed in Massachusetts but not self-employed, you can apply online or by phone for the following types of paid leave:</p><ul><li>Medical leave due to your own illness, injury, or pregnancy</li><li>Family leave to bond with your child after birth, adoption, or foster placement — whether you are applying before or after the child arrives</li><li>Family leave to care for a family member with a serious medical condition</li></ul>",
    alertOnlineHeading: "Apply online",
    alertPhone:
      "<p>Apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if <strong>any</strong> of the following are true:</p><ul><li>You are self-employed or unemployed and you are applying for paid leave</li><li>You need paid family leave to care for a family member who serves in the armed forces</li><li>You need paid family leave to manage family affairs when a family member is on active duty in the armed forces</li></ul>",
    alertPhoneHeading: "Apply by phone",
    applicationsLink: "View all applications",
    createClaimButton: "Create an application",
    stepOne:
      "<p>If you can, tell your employer at least 30 days before your leave begins. If you need to take leave right away, tell your employer as soon as possible.</p><p>Once you tell your employer, you have the right to apply and your job is protected. Make a note of when you notified your employer. You will need to provide this date in your leave application.</p>",
    stepOneHeading: "1. Tell your employer that you need to take paid leave",
    stepThree:
      "<p>Applying takes around 15 minutes. Your information will save as you go, so you can finish your application later if you need to.</p><p>If you give birth and plan to take both pregnancy-related medical leave and family leave to bond with your newborn, you should apply for medical leave first. Family leave to bond with your child can be <medical-bonding-link>easily added to your claim</medical-bonding-link> by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>You need to create multiple leave applications if you are:</p><ul><li>Taking leave from multiple employers.</li><li>Taking time off in uneven blocks of time (intermittent leave), <strong>and</strong> taking time off completely or on a reduced schedule. You’ll need a separate application for the intermittent leave.</li></ul><p>PFML benefits are subject to reporting for tax purposes and may be subject to taxation. Withholding is not currently supported through the PFML program. Learn more about the <tax-liability-link>possible tax implications</tax-liability-link> of your paid leave benefits.</p>",
    stepThreeHeading: "3. Apply",
    stepTwoBondingLeaveBody:
      "<p>For family leave to bond with your child after birth, foster placement, or adoption you need a document that confirms your child’s date of birth or placement.</p><p>You can apply before your child is born or arrives in your home. You will need to provide proof of birth or placement for your application to be approved.</p>",
    stepTwoBondingLeaveSubhead: "To bond with a child",
    stepTwoCaringLeaveBody:
      "<p>The health care provider of the person you're caring for must complete the <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link>.</p>",
    stepTwoCaringLeaveSubhead:
      "To care for a family member with a serious health condition",
    stepTwoFamilyLeaveSubhead: "Family leave",
    stepTwoHeading: "2. Get documentation that supports your leave request",
    stepTwoMedicalLeaveBody:
      "<p>Your health care provider must complete the <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link>.</p>",
    stepTwoMedicalLeaveSubhead:
      "Medical leave for your own serious health condition",
    stepTwoWhichPaidLeaveBody:
      "<p>If you’re not sure what kind of leave to apply for, <which-paid-leave-link>learn more about Paid Family and Medical Leave</which-paid-leave-link>.</p>",
    title: "Get ready to apply",
  },
  index: {
    claimantCardBody: "Apply for Paid Family and Medical Leave.",
    claimantCreateAccountButton: "Create a worker account",
    claimantHeading: "Workers",
    createAccountHeading: "Choose an account type",
    createAccountHint:
      "You can create an account as a worker or as an employer.",
    employerCardBody: "Manage leave for your team.",
    employerCreateAccountButton: "Create an employer account",
    employerHeading: "Employers",
    seoTitle:
      "Create or Log into your account for Massachusetts Paid Family and Medical Leave",
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
      "We’ll keep your information private as required by law. As a part of the application process, we may check the information you give with other state agencies. We may share information related to your application with your employer, employer’s affiliates, health care provider(s), and contracted private partners.",
    dataUsageHeading: "How we use your data",
    fullUserAgreementBody:
      "To find out more about how the Commonwealth might use the information you share with the Department of Family and Medical Leave, please read the <informed-consent-link>DFML Informed Consent Agreement</informed-consent-link> and the <privacy-policy-link>Privacy Policy for Mass.gov</privacy-policy-link>.",
    fullUserAgreementHeading: "Read the full user agreements",
    intro:
      "The information you provide on this website will be used to administer the Paid Family and Medical Leave program. To continue using this website, you must agree to the terms of the user agreements updated as of June$t(chars.nbsp)25,$t(chars.nbsp)2021.",
    title: "How this website uses your information",
  },
};

const components = {
  absenceCaseStatusTag: {
    status_approved: "$t(shared.absenceCaseStatus_approved)",
    status_closed: "$t(shared.absenceCaseStatus_closed)",
    status_completed: "$t(shared.absenceCaseStatus_closed)",
    status_declined: "$t(shared.absenceCaseStatus_denied)",
    status_noAction: "No action required",
    status_openRequirements: "Review by {{followupDate}}",
  },
  amendButton: {
    amend: "Amend",
  },
  amendmentForm: {
    cancel: "Cancel amendment",
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
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    noticesDownload:
      "When you click the notice link, the file will download to your device.",
    noticesFallback:
      "Once we’ve made a decision, you can download the decision notice here. You’ll also get an email notification.",
    noticesHeading: "Download your notices",
    reductionsInstructions:
      "<p>If your plans for other benefits or income during your paid leave have changed, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Report changes to:</p><ul><li>Benefits from your employer that you plan to use in addition to paid leave from PFML. For example, if you are taking a different amount of sick days than you first planned, or if you are taking employer-sponsored parental leave on a different schedule than you expected, report this change.</li><li>Income from other sources during your leave. For example, if you got approved for a disability benefit after you submitted your application, report this change.</li></ul>",
    reductionsInstructions_missingData:
      "<p>If you have other leave, benefits, and income to report, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Report any of these situations:</p><ul><li>You have already taken leave to care for a family member since July 1, 2021</li><li>You have already taken leave since January 1, 2021 for <when-can-i-use-pfml>any other reason that qualifies for PFML</when-can-i-use-pfml></li><li>You plan to use any accrued paid leave or any other benefits from your employer during your paid leave from PFML (for example: your employer’s parental leave program or paid sick time)</li><li>You expect to get income from any other sources during your leave (for example: disability insurance, retirement benefits, or another job)</li></ul>",
    reductionsInstructions_old:
      "<p>If you’ll receive <reductions-overview-link>other benefits or income</reductions-overview-link>, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. This includes:</p><ul><li>Any benefits from your employer that you’ll be using in addition to Massachusetts paid leave (for example, maternity leave, or paid sick time)</li><li>Income from any other sources during your leave</li></ul>",
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
  downloadableDocument: {
    createdAtDate: "Posted {{date}}",
    noticeName: "Other notice $t(shared.pdfNoticeSuffix)", // it should fallback to this if we receive an unexpected or undefined enum
    noticeName_approvalNotice: "Approval notice $t(shared.pdfNoticeSuffix)",
    noticeName_denialNotice: "Denial notice $t(shared.pdfNoticeSuffix)",
    noticeName_requestForInfoNotice:
      "Request for more information $t(shared.pdfNoticeSuffix)",
  },
  dropdown: {
    emptyChoiceLabel: "- Select an answer -",
  },
  employersAmendableConcurrentLeave: {
    destroyButtonLabel_add: "Cancel addition",
    destroyButtonLabel_amend: "Cancel amendment",
    heading_add: "Add an accrued paid leave",
    heading_amend: "Amend accrued paid leave",
    leaveEndDateLabel: "When did the leave end?",
    leaveStartDateLabel: "When did the leave begin?",
    subtitle_add:
      "This addition will get saved when you submit your review at the end of this page.",
    subtitle_amend:
      "This amendment will get saved when you submit your review. To remove this leave, include a comment at the end of the page.",
  },
  employersAmendableEmployerBenefit: {
    amountFrequencyLabel: "$t(shared.amountFrequencyLabel)",
    benefitAmountDollarsLabel: "Amount",
    benefitEndDateLabel:
      "What is the last day of leave from work that this benefit will pay your employee for?",
    benefitStartDateLabel:
      "What is the first day of leave from work that this benefit will pay your employee for?",
    benefitTypeLabel: "What kind of employer-sponsored benefit is it?",
    cancelAddition: "Cancel addition",
    choiceHint_benefitAmountDollars: "How much will your employee receive?",
    choiceHint_familyOrMedicalLeave:
      "$t(shared.choiceHint_familyOrMedicalLeave)",
    choiceHint_shortTermDisability: "$t(shared.choiceHint_shortTermDisability)",
    choiceLabel_familyOrMedicalLeave:
      "$t(shared.employerBenefitType_familyOrMedicalLeave)",
    choiceLabel_permanentDisability:
      "$t(shared.employerBenefitType_permanentDisability)",
    choiceLabel_shortTermDisability:
      "$t(shared.employerBenefitType_shortTermDisability)",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    destroyButtonLabel_add: "Cancel addition",
    destroyButtonLabel_amend: "Cancel amendment",
    employeeAmountReceivedLabel: "How much will your employee receive?",
    heading_add: "Add an employer-sponsored benefit",
    heading_amend: "Amend employer-sponsored benefit",
    hint: "This addition will get saved when you submit your review at the end of this page.",
    isFullSalaryContinuousHint:
      "This means that for the period of time your employee receives this benefit, it will pay them the same amount of money as their wages from while they're not on leave. If this benefit will pay them any other amount, select No.",
    isFullSalaryContinuousLabel:
      "Does this employer-sponsored benefit fully replace your employee's wages?",
    subtitle_add:
      "This addition will get saved when you submit your review at the end of the page.",
    subtitle_amend:
      "This amendment will get saved when you submit your review. To remove this benefit, include a comment at the end of the page.",
    title: "Add an employer-sponsored benefit",
  },
  employersAmendablePreviousLeave: {
    addButton_first: "Add a previous leave",
    addButton_subsequent: "Add another previous leave",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    destroyButtonLabel_add: "Cancel addition",
    destroyButtonLabel_amend: "Cancel amendment",
    heading_add: "Add a previous leave",
    heading_amend: "Amend previous leave",
    isForSameReasonAsLeaveReasonLabel:
      "Was this leave for the same reason as their paid leave request?",
    leaveEndDateLabel: "When did the employee's leave end?",
    leaveReasonLabel: "Why did this employee need to take leave?",
    // these are similar to, but NOT exactly the same as claimsPreviousLeavesOtherReasonDetails
    leaveReasonValue_activeDutyFamily:
      "Managing family affairs while a family member was on active duty in the armed forces",
    leaveReasonValue_bonding:
      "Bonding with their child after birth or placement",
    leaveReasonValue_care: "Caring for a family member",
    leaveReasonValue_medical: "An illness or injury",
    leaveReasonValue_pregnancy: "Pregnancy",
    leaveReasonValue_serviceMemberFamily:
      "Caring for a family member who served in the armed forces",
    leaveReason_family: "Family leave",
    leaveReason_medical: "$t(shared.leaveReasonMedical)",
    leaveStartDateLabel: "When did the employee's leave start?",
    subtitle_add:
      "This addition will get saved when you submit your review at the end of this page.",
    subtitle_amend:
      "This amendment will get saved when you submit your review. To remove this leave, include a comment at the end of the page.",
  },
  employersConcurrentLeave: {
    addButton: "Add an accrued paid leave",
    dateRangeLabel: "Date range",
    explanation:
      "Your employee has told us about the following accrued paid leave they plan to use concurrent with their paid leave from PFML. This includes paid vacation time, sick time, personal time, and other paid time off. It does not include a family or medical leave policy or a disability program. There’s a 7-day unpaid waiting period, and employees are allowed to use accrued paid leave to overlap that period.",
    header: "Concurrent accrued paid leave",
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
    addButton_first: "Add an employer-sponsored benefit",
    addButton_subsequent: "Add another employer-sponsored benefit",
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
    caption_v1:
      "Your employee is planning to use these benefits. Employer sponsored benefits include temporary disability insurance, permanent disability insurance, paid time off (PTO) or accrued paid leave, and family or medical leave benefits such as a parental leave program. <reductions-overview-link>Learn more about how these affect payments.</reductions-overview-link>",
    caption_v2:
      "Your employee is planning to use these benefits during their paid leave under PFML. Employer sponsored benefits include temporary disability insurance, permanent disability insurance, and family or medical leave benefits such as a parental leave program. For paid time off (PTO) and other accrued paid leave your employee will use, review “Concurrent accrued paid leave” above. <reductions-overview-link>Learn more about how these affect payments.</reductions-overview-link>",
    dateRangeLabel: "Date range",
    detailsLabel: "Details",
    fullSalaryContinuous: "Full salary continuous",
    header: "Employer-sponsored benefits",
    noAmountReported: "No amount reported",
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
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    commentSolicitation: "Please tell us more.",
    commentSolicitation_employeeNotice:
      "Please tell us when your employee notified you about their leave.",
    commentSolicitation_employerDecision:
      "Please tell us why you denied this leave request.",
    commentSolicitation_fraud:
      "Please tell us why you believe this is fraudulent.",
    instructionsLabel: "Do you have any additional comments or concerns?",
  },
  employersFraudReport: {
    alertBody:
      "We take allegations about fraud seriously. Selecting this will begin further investigation. Please only select if you are convinced this is fraudulent. If you have questions, feel free to call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> from 8am‑5pm ET.",
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
    lead_hasDocs: "$t(shared.employerLeaveScheduleLeadHasDocs)",
    lead_noDocs: "$t(shared.employerLeaveScheduleLeadNoDocs)",
  },
  employersLeaveDetails: {
    applicationIdLabel: "Application ID",
    choiceNo: "No (comment required)",
    choiceUnknown: "I don't know",
    choiceYes: "Yes",
    commentHeading: "Tell us why you think this relationship is inaccurate.",
    documentName: "Your employee's certification document",
    documentationLabel: "Documentation",
    familyMemberRelationshipHint:
      "This employee has attested the family member relationship is <eligible-relationship-link>a covered relationship</eligible-relationship-link>. If something on the form seems incorrect, add a comment at the end of the page.",
    familyMemberRelationshipLabel:
      "Do you believe the listed relationship is described accurately? (Optional)",
    header: "Leave details",
    inaccurateRelationshipAlertHeading:
      "The employee will be denied paid leave.",
    inaccurateRelationshipAlertLead:
      "We take allegations about false relationships seriously. Choosing No may trigger a denial of the employee's application for paid leave. The employee has the right to appeal if their application is denied.",
    leaveDurationLabel: "Leave duration",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_care: "$t(shared.leaveReasonCare)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonPregnancy)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveTypeLabel: "Leave type",
    recordkeepingInstructions:
      "To meet <mass-employer-role-link>federal laws and regulations</mass-employer-role-link>, you must keep medical records separate and confidential from any personnel files.",
    recordkeepingInstructions_caringLeave:
      "<p>To meet <mass-employer-role-link>federal laws and regulations</mass-employer-role-link>, you must keep medical records separate and confidential from any personnel files.</p><p>View the family relationship on page 3.</p>",
    unknownRelationshipAlertLead:
      "If you have not confirmed the accuracy of the family relationship the employee has attested to, please note that the Department of Family and Medical leave will adjudicate the claim based on the attestation the employee made when submitting their application.",
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
    header: "Leave schedule",
    lead_hasDocs: "$t(shared.employerLeaveScheduleLeadHasDocs)",
    lead_noDocs: "$t(shared.employerLeaveScheduleLeadNoDocs)",
    leaveFrequencyLabel: "Leave frequency",
    reducedHoursPerWeek: "Reduced by {{numOfHours}} hours per week",
  },
  employersNavigationTabs: {
    dashboard: "Dashboard",
    welcome: "Welcome",
  },
  employersPreviousLeaves: {
    addButton: "$t(shared.claimsPreviousLeaveDetails.addButton)",
    dateRangeLabel: "Date range",
    explanation:
      "Your employee has listed leave they have taken for a qualified reason. Only leave since January 1, 2021 is included. This includes both paid leave, such as paid vacation or sick days, and unpaid leave, such as FMLA leave. When possible, verify that a previous leave was for a reason that qualifies for paid leave under PFML.",
    header: "Previous leave",
    leaveTypeLabel: "Leave type",
    qualifyingReasonContent:
      "An employee or contractor can take paid or unpaid leave to:",
    qualifyingReasonDetailsLabel: "$t(shared.qualifyingReasonDetailsLabel)",
    qualifyingReason_activeDuty:
      "Manage family affairs when a family member is on active duty in the armed forces",
    qualifyingReason_bondWithChild:
      "Bond with a child after birth or placement",
    qualifyingReason_careForFamilyMedical:
      "Care for a family member with a <mass-benefits-guide-serious-health-condition-link>serious health condition</mass-benefits-guide-serious-health-condition-link> since July 1, 2021",
    qualifyingReason_careForFamilyMilitary:
      "Care for a family member who serves in the armed forces",
    qualifyingReason_manageHealth:
      "Manage a <mass-benefits-guide-serious-health-condition-link>serious health condition</mass-benefits-guide-serious-health-condition-link>, including illness, injury, or pregnancy",
  },
  employersSupportingWorkDetails: {
    header: "Supporting work details",
    heading_amend: "Amend weekly hours worked",
    leavePeriodDurationHint:
      "If their schedule varies, tell us the average number of hours worked over the past 52 weeks.",
    leavePeriodDurationLabel:
      "On average, how many hours does the employee work each week?",
    subtitle_amend:
      "This amendment will get saved when you submit your review.",
    weeklyHoursWorkedLabel: "Weekly hours worked",
  },
  errorBoundary: {
    message:
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.contactCenterPhoneNumberNoBreak)",
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
    dataSharingAgreement: "Data Sharing Agreement",
    description:
      "Paid Family and Medical Leave is a state-offered benefit for anyone who works in Massachusetts and is eligible to take up to 26 weeks of paid leave for medical or family reasons.",
    logoTitleDFML: "Go to DFML homepage",
    logoTitlePFML: "Go to PFML homepage",
    orgAddress: "PO Box 838 Lawrence, MA 01842",
    orgName: "Department of Family and Medical Leave (DFML)",
    orgPhoneNumber: "$t(shared.contactCenterPhoneNumber)",
    privacyPolicy: "Privacy$t(chars.nbsp)Policy",
    title: "Paid Family and Medical Leave (PFML)",
  },
  form: {
    continueButton: "Save and continue",
    dateInputDayLabel: "Day",
    dateInputExample: "MM / DD / YYYY",
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
    lead: "This page is currently unavailable while the site is undergoing maintenance. Please check back$t(chars.nbsp)shortly.",
    scheduled:
      "We are performing scheduled maintenance to improve functionality and our overall service. Paid leave applications will be back online on <strong>{{scheduledRemovalDayAndTime}}</strong>.<br/><br/>When we are back, you will be able to access your existing applications or create a new one. Employers will be able to respond to information requests. We appreciate your understanding and patience. To get ready, review <what-to-expect-link>what to expect when you apply for paid family and medical leave benefits</what-to-expect-link>.",
    title: "We’re undergoing maintenance",
  },
  newTag: "New",
  pagination: {
    nextLabel: "Next",
    previousLabel: "Previous",
    summary:
      "Viewing {{firstRecordNumber}} to {{lastRecordNumber}} of {{totalRecords}} results",
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
