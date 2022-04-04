/**
 *
 * @file US English language file for i18next-based i18n.
 * @see docs/internationalization.md
 *
 */

interface I18nContentGroup {
  [contentKey: string]: string;
}

// When editing this file, be mindful that many of its strings use non-breaking
// hyphen and non-breaking space characters.
// https://alignedonline.com/non%E2%80%91breaking-spaces
const chars: { [key: string]: string } = {
  // Non-breaking hyphen characters are used in phone and fax numbers to avoid
  // the numbers awkwardly wrapping to multiple lines.
  nbhyphen: "‑",
  // Non-breaking space characters are used to keep cardinal adjectives on the
  // same line as the nouns they describe or between the last two words of a
  // sentence to prevent line breaks that would cause orphaned words.
  nbsp: " ",
};

// Our other i18n keys are limited to three levels, but errors is an exception
// since the format of these mirror the field path, which could possibly be more
// than three levels deep (e.g `errors.claim.leave_details.start_date.required`).
const errors = {
  applicationImports: {
    absence_case_id: {
      duplicate: "You already have access.",
      exists:
        "This application cannot be added. You will need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to work on your application or get status updates.",
      required: "Application ID is required.",
    },
    conflicting: "$t(shared.applicationImportError_noMatch)",
    employment_status: {
      invalid: "$t(shared.applicationImportError_unsupported)",
    },
    incorrect: "$t(shared.applicationImportError_noMatch)",
    leave_details: {
      reason: {
        invalid: "$t(shared.applicationImportError_unsupported)",
      },
    },
    mfa_delivery_preference: {
      required: "Your login is not verified.",
    },
    tax_identifier: {
      required: "Social Security Number is required.",
      pattern: "Your Social Security Number or ITIN must be 9 digits.",
    },
  },
  applications: {
    claim: {
      exists:
        "You have already submitted this portion of your application. If you need to edit your information, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    },
    concurrent_leave: {
      is_for_current_employer: {
        required: "Select Yes if your leave is from this employer.",
      },
      leave_end_date: {
        conflicting:
          "$t(shared.disallow_overlapping_waiting_period_and_concurrent_leave_end_date)",
        format:
          "The date your leave ends must include a valid month, day, and year.",
        invalid_date_range:
          "The date your leave ends must be on or after the date your leave begins.",
        minimum: "Enter a date after December 31, 2020.",
        required: "Enter the date this leave ends.",
      },
      leave_start_date: {
        conflicting:
          "$t(shared.disallow_overlapping_waiting_period_and_concurrent_leave_start_date)",
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
        minimum:
          "The benefit amount you will receive must be greater than 0. If you don’t know how much you will receive, go back and answer “No” to the previous question.",
        required: "Enter the amount you will receive.",
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
        "We couldn’t find the employer you entered in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Common reasons for this error include that your employer is statutorily exempt, non-compliant, or hasn’t filed wage information yet.",
      require_non_exempt_employer:
        "Our records show the employer you entered has a private plan. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, ask your employer about their private plan. If this is incorrect, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
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
        "Select Yes if you have taken previous leave that you must report.",
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
    is_withholding_tax: {
      duplicate:
        "You have already submitted your tax withholding preference. If you need to edit your preference, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
      required: "Select your tax withholding preference.",
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
            "Sorry, our intermittent leave request service is a work in progress. Use our <intermittent-leave-guide>step-by-step guide to intermittent leave</intermittent-leave-guide> to complete your application. You can also complete your application by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
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
        minimum:
          "The income amount you will receive must be greater than 0. If you don’t know how much you will receive, go back and answer “No” to the previous question.",
        required: "Enter the amount you will receive.",
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
        exists:
          "You have already submitted your payment preference. If you need to edit your preference, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
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
          "$t(shared.claimsPreviousLeaveErrors.isForCurrentEmployer_required)",
      },
      leave_end_date: {
        format: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_format)",
        invalid_date_range:
          "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_invalidDateRange)",
        minimum: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_minimum)",
        required: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_required)",
      },
      leave_minutes: {
        maximum: "$t(shared.claimsPreviousLeaveErrors.leaveMinutes_maximum)",
        required: "$t(shared.claimsPreviousLeaveErrors.leaveMinutes_required)",
      },
      leave_reason: {
        required: "$t(shared.claimsPreviousLeaveErrors.leaveReason_required)",
      },
      leave_start_date: {
        format: "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_format)",
        minimum: "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_required)",
      },
      worked_per_week_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveErrors.workedPerWeekMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveErrors.workedPerWeekMinutes_required)",
      },
    },
    previous_leaves_same_reason: {
      is_for_current_employer: {
        required:
          "$t(shared.claimsPreviousLeaveErrors.isForCurrentEmployer_required)",
      },
      leave_end_date: {
        format: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_format)",
        invalid_date_range:
          "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_invalidDateRange)",
        minimum: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_minimum)",
        required: "$t(shared.claimsPreviousLeaveErrors.leaveEndDate_required)",
      },
      leave_minutes: {
        maximum: "$t(shared.claimsPreviousLeaveErrors.leaveMinutes_maximum)",
        required: "$t(shared.claimsPreviousLeaveErrors.leaveMinutes_required)",
      },
      leave_start_date: {
        format: "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_format)",
        minimum: "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_minimum)",
        required:
          "$t(shared.claimsPreviousLeaveErrors.leaveStartDate_required)",
      },
      worked_per_week_minutes: {
        maximum:
          "$t(shared.claimsPreviousLeaveErrors.workedPerWeekMinutes_maximum)",
        required:
          "$t(shared.claimsPreviousLeaveErrors.workedPerWeekMinutes_required)",
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
        "We already have an account set up for you. Please sign in with that account. If that doesn’t sound familiar to you, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
      disallow_caring_leave_before_july:
        "Leave start dates must be after June 30, 2021.",
      disallow_hybrid_intermittent_leave:
        "You cannot request intermittent leave in the same application as your continuous or reduced schedule leave. Create a separate application for your <intermittent-leave-guide>intermittent leave</intermittent-leave-guide> dates.",
      disallow_overlapping_leave_period_with_previous_leave:
        "Your previous leave dates cannot overlap with the PFML leave dates you are applying for. Check that you’ve entered the correct start and end dates for your leave details and previous leave.",
      disallow_overlapping_leave_periods:
        "Your reduced leave schedule cannot overlap with your continuous or intermittent leave. Check whether you’ve entered the correct start and end dates for each leave period.",
      disallow_overlapping_waiting_period_and_concurrent_leave_end_date:
        "$t(shared.disallow_overlapping_waiting_period_and_concurrent_leave_end_date)",
      disallow_overlapping_waiting_period_and_concurrent_leave_start_date:
        "$t(shared.disallow_overlapping_waiting_period_and_concurrent_leave_start_date)",
      disallow_submit_over_60_days_before_start_date:
        "The date your leave begins is more than 60 days in the future. Submit your application within 60 days of your leave start date.",
      max_ssn_fein_update_attempts:
        "You’ve exceeded the number of allowed attempts to enter your SSN and EIN. Please call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
      min_leave_periods:
        "You must choose at least one kind of leave (<scheduling-leave-guide>continuous, reduced schedule, or intermittent</scheduling-leave-guide>).",
      min_reduced_leave_minutes:
        "The total time entered for your hours off must be greater than 0.",
      require_employee:
        "We couldn’t find a match between your Social Security Number and the employer you entered in our system. Check that you entered your Social Security Number and your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to provide proof of wages.",
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
      "Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    attemptBlocked_login:
      "Your log in attempt was blocked due to suspicious activity. You will need to reset your password to continue. We’ve also sent you an email to confirm your identity.",
    attemptsLimitExceeded_forgotPassword:
      "Your account is temporarily locked because of too many forget password requests. Wait 15 minutes before trying again.",
    attemptsLimitExceeded_login:
      "Your account is temporarily locked because of too many failed login attempts. Wait 15 minutes before trying again.",
    attemptsLimitExceeded_updatePhone:
      "We couldn't add your phone number because you've exceeded the number of allowed attempts. You can try again later.",
    code: {
      attemptsExceeded:
        "Your account is temporarily locked because of too many failed verification attempts. Wait 15 minutes before trying again.",
      attemptsExceeded_confirmPhone:
        "We can't confirm your phone number because of too many failed verification attempts. Wait 15 minutes before trying again.",
      deliveryFailure:
        "We encountered an error while sending the verification code. Try again.",
      expired: "Your verification code has expired or has already been used.",
      invalidMFACode:
        "The security code you entered is invalid. Make sure the code matches the security code we texted to you.",
      mismatchException:
        "Invalid verification code. Make sure the code matches the code emailed to you.",
      pattern:
        "Enter the 6-digit code sent to your email and ensure it does not include any punctuation.",
      required: "Enter the 6-digit code sent to your email",
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
    "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
  caughtError_DocumentsLoadError: "$t(shared.documentsLoadError)",
  caughtError_DocumentsUploadError: "$t(shared.documentsUploadError)",
  caughtError_ForbiddenError:
    "Sorry, an authorization error was encountered. Please log out and then log in to try again.",
  caughtError_NetworkError: "$t(shared.networkError)",
  caughtError_NotFoundError:
    "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
  claimStatus: {
    fineos_claim_withdrawn:
      "Application <strong>{{absenceId}}</strong> has been withdrawn and is no longer being processed.  If you believe this application has been withdrawn in error, check if any additional applications in your account cover the same leave period.  If you have additional questions, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
  },
  documents: {
    file: {
      clientSideError_size:
        "We could not upload: {{disallowedFileNames}}. Files must be smaller than {{ sizeLimit }} MB.<br />You may fax or mail color copies of your documents if you prefer. <mail-fax-instructions>Follow the fax and mail instructions</mail-fax-instructions>.",
      clientSideError_sizeAndType:
        "We could not upload: {{disallowedFileNames}}. Choose a PDF or an image file (.jpg, .jpeg, .png) that is smaller than {{ sizeLimit }} MB.<br />You may fax or mail color copies of your documents if you prefer. <mail-fax-instructions>Follow the fax and mail instructions</mail-fax-instructions>.",
      clientSideError_type:
        "We could not upload: {{disallowedFileNames}}. Choose a PDF or an image file (.jpg, .jpeg, .png).<br />You may fax or mail color copies of your documents if you prefer. <mail-fax-instructions>Follow the fax and mail instructions</mail-fax-instructions>.",
      file_size:
        "We could not upload all files. Files must be smaller than {{ fileSizeMaxMB }} MB.<br />You may fax or mail color copies of your documents if you prefer. <mail-fax-instructions>Follow the fax and mail instructions</mail-fax-instructions>.",
      required: "Upload at least one file to continue.",
    },
    fineos_client: "$t(shared.documentsUploadError)",
    rules: {
      document_requirement_already_satisfied:
        "You have already satisfied the requirements for this document. If you would like to update the existing documentation, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    },
  },
  employers: {
    comment: {
      maxLength: "$t(shared.maxEmployerCommentLengthError)",
    },
    contains_v1_and_v2_eforms:
      "<h3>Call the Contact Center to review this application</h3><p>We can’t display this application for review online. To review this application, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p><strong>What you will need to know when you call the agent:</strong></p><ul><li>The employee’s name and application ID. You can find these on the Dashboard, or in the email we sent to tell you that you can review this application.</li><li>The error code for this error: <strong>V-12</strong>.</li></ul><strong>Why you are seeing this error:</strong> Your employee told us about some other leave and benefits they are receiving in addition to paid leave from PFML. This information was added to their application recently. In some cases, when an employee who submitted an application before July 15th then adds other leave and benefits information later, it can cause this error.<p>This is a rare error that will not happen with new applications.</p>",
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
      employer_requires_verification_data:
        "Your account can’t be verified yet, because your organization has not made any paid leave contributions. Once this organization pays quarterly taxes, you can verify your account and review applications. <file-a-return-link>Learn more about filing returns and sending contributions</file-a-return-link>.",
      pattern:
        "Enter your 9-digit Employer Identification Number in the correct format.",
      require_contributing_employer:
        "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly and the associated business is contributing to Paid Family and Medical Leave.",
      require_employer:
        "Enter a valid Employer Identification Number (EIN). Check that you entered your EIN correctly.",
      required: "Enter your 9-digit Employer Identification Number.",
    },
    hours_worked_per_week: {
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
  mfa: {
    code: {
      pattern:
        "Enter the 6-digit code sent to your phone number and ensure it does not include any punctuation.",
      required: "Enter the 6-digit code sent to your phone number",
    },
    enterMFASetupFlow: {
      required:
        "Select Yes if you want to add a phone number for verifying logins.",
    },
  },
  network:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>",
  payments: {
    payment_preference: {
      retype_account_number: {
        required: "Retype your account number",
        mismatch:
          "The account numbers you entered do not match. Make sure the numbers are exactly the same.",
      },
    },
  },
  users: {
    email_address: {
      exists: "$t(shared.auth.emailError_exists)",
      format:
        "Enter an email address in the correct format, like name@example.com",
      required: "$t(shared.auth.emailError_required)",
    },
    mfa_phone_number: {
      phone_number: {
        // Used by the mfa service, more than 12 digits
        international_number:
          "We don't support international phone numbers yet. Enter a U.S. phone number to set up additional login verifications.",
        // There are 10 digits
        pattern: "Enter a valid phone number",
        // Used by the mfa service, field cant be blank
        required: "Enter a phone number",
      },
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
  // Generic fallbacks, when there isn't content defined for an error's namespace.
  // These may also be used if we add a new field/validation on the backend, without
  // also adding its i18n error message to this file.
  validationFallback: {
    fineos_claim_withdrawn:
      "Application has been withdrawn and is no longer being processed.",
    invalid: "Field ({{field}}) has invalid value.",
    invalid_masked_field: "Re-enter the full value to make a change.",
    // Field's value didn't match an expected regex pattern:
    pattern: "Field ({{field}}) didn’t match expected format.",
  },
};

const shared: {
  // Keys are limited to three levels deep, for example `shared.auth.emailMissing`.
  // This makes the structure easier to navigate and the process of finding a specific element more consistent
  [contentKey: string]: string | I18nContentGroup;
} = {
  absenceCaseStatus_approved: "Approved",
  absenceCaseStatus_closed: "Closed",
  absenceCaseStatus_denied: "Denied",
  absenceCaseStatus_noAction: "No action required",
  absenceCaseStatus_pending: "Pending",
  achTypeChecking: "Checking",
  achTypeSavings: "Savings",
  addApplication: "Add an existing application",
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
  applicationImportError_noMatch:
    "No match found. Applications started on the phone with a Contact Center agent can take up to 24 hours to appear in our online system. Check back again. If you’re still unable to find your application, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
  applicationImportError_unsupported:
    "This application cannot be added at this time. If you are applying for <applying-to-military-leave>military-related paid family leave benefits</applying-to-military-leave>, or you are currently <applying-self-or-unemployed>self-employed or unemployed</applying-self-or-unemployed>, your application cannot be managed by this website. You will need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to work on your application or get status updates.",
  auth: {
    emailError_exists: "An account with the given email already exists",
    emailError_required: "Enter your email address",
    passwordError_insecure:
      "Choose a different password. Avoid commonly used passwords and avoid using the same password on multiple websites.",
    passwordError_invalid:
      "Your password does not meet the requirements. Please check the requirements and try again.",
    passwordError_required: "Enter your password",
    skip: "Skip this step",
  },
  backToLoginLink: "Back to log in",
  backToYourApplicationsLink: "Back to your applications",
  certificationFormCare:
    "Certification of Your Family Member’s Serious Health Condition",
  certificationFormMedical: "Certification of Your Serious Health Condition",
  choiceHint_familyOrMedicalLeave: "For example, a paid parental leave policy",
  choiceHint_shortTermDisability: "Short-term or long-term disability",
  choiceNo: "No",
  choiceYes: "Yes",
  claimDurationTypeContinuous: "Continuous leave",
  claimDurationTypeIntermittent: "Intermittent leave",
  claimDurationTypeReduced: "Reduced leave",
  claimDurationTypeReducedSchedule: "Reduced leave schedule",
  claimsEmploymentInfoTitle: "Employment information",
  claimsLeaveDetailsTitle: "Leave details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsModifyTitle: "Change your application",
  claimsOtherLeaveTitle: "Other leave, benefits, and income",
  claimsPreviousLeaveDetails: {
    addButton: "Add another previous leave",
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
    minimumDateHint: "This date must be on or after {{minimumDate}}.",
    removeButton: "Remove this previous leave",
    sectionHint:
      "Enter details about each period of leave taken between {{previousLeaveStartDate}} and {{leaveStartDate}}. A leave period begins on the day you first went on leave and ends on the last day of leave. If you were on leave intermittently, your leave period begins on the first day you went on leave and ends on the very last day.<br/><br/>You don't need to tell us about previous leave you’ve taken through Massachusetts’ PFML program.",
    sectionLabel: "Tell us about your previous leave",
    workedPerWeekMinutesDetails:
      "If your weekly schedule was not consistent, enter the average number of hours you would have worked per week. For example, if your leave was across two different weeks, and your normal work schedule was 40 hours in one week and 20 hours in the next, you should enter 30 hours.",
    workedPerWeekMinutesDetailsLabel: "What if my schedule was not consistent?",
    workedPerWeekMinutesHint:
      "Enter the number of hours you would have worked each week, if you were not on leave.",
    workedPerWeekMinutesLabel:
      "How many hours would you normally have worked per week at the time you took this leave?",
  },
  claimsPreviousLeaveErrors: {
    isForCurrentEmployer_required:
      "Select Yes if your leave is from this employer.",
    leaveEndDate_format:
      "The date your leave ended must include a valid month, day, and year.",
    leaveEndDate_invalidDateRange:
      "The date your leave ends must be on or after the date your leave began.",
    leaveEndDate_minimum: "Only enter previous leaves with a valid start date.",
    leaveEndDate_required: "Enter the date your leave ended.",
    leaveMinutes_maximum: "The hours entered are more than the possible hours.",
    leaveMinutes_required: "Enter the hours you took off work for your leave.",
    leaveReason_required: "Select the qualifying reason for your leave.",
    leaveStartDate_format:
      "The date your leave began must include a valid month, day, and year.",
    leaveStartDate_minimum:
      "Only enter previous leaves with a valid start date.",
    leaveStartDate_required: "Enter the date your leave began.",
    workedPerWeekMinutes_maximum:
      "The hours entered are more than the possible hours.",
    workedPerWeekMinutes_required: "Enter the hours you normally worked.",
  },
  claimsVerifyIdTitle: "Your identification",
  contactCenterAddress:
    "PO Box 838$t(chars.nbsp)Lawrence, MA$t(chars.nbsp)01842",
  contactCenterFaxNumber: "(617)$t(chars.nbsp)855$t(chars.nbhyphen)6180",
  contactCenterPhoneNumber: "(833) 344-7365",
  contactCenterPhoneNumberNoBreak:
    "(833)$t(chars.nbsp)344$t(chars.nbhyphen)7365",
  contactCenterReportHoursPhoneNumber: "(857) 972-9256",
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
  disallow_overlapping_waiting_period_and_concurrent_leave_end_date:
    "The last day of your accrued paid leave must be after the 7-day waiting period for PFML.",
  disallow_overlapping_waiting_period_and_concurrent_leave_start_date:
    "The first day of your accrued paid leave must be after the 7-day waiting period for PFML.",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime: "{{hours}}h {{minutes}}m",
  // TODO (CP-1335): Add i18next formatter for time
  displayTime_noMinutes: "{{hours}}h",
  docsRequired: {
    newborn:
      "Once your child is born, submit proof of birth so that we can review your application. Learn more about <proof-document-link>proof of birth documents</proof-document-link> we accept.",
  },
  documentCategory: {
    certification: "certification form",
    identification: "identification documents",
  },
  documentsLoadError:
    "An error was encountered while checking your application for documents. If this continues to happen, call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
  documentsUploadError:
    "We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
  employerBenefitEntryPrefix: "Benefit",
  employerBenefitType_familyOrMedicalLeave: "Family or medical leave insurance",
  employerBenefitType_paidLeave: "Accrued paid leave",
  employerBenefitType_permanentDisability: "Permanent disability insurance",
  employerBenefitType_shortTermDisability: "Temporary disability insurance",
  employerInstructions_addComment:
    "If something is incomplete, add a comment at the end of the page.",
  employerInstructions_followUpDate:
    "<strong>Review and respond by:</strong> {{date}} at 11:59 p.m. Eastern time",
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
  infoAlertBody_bonding:
    "You may be able to take up to 20 weeks of paid medical leave if you’re unable to work during your pregnancy or for your recovery from childbirth. Your health care provider determines how much medical leave you will need. Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if you need <about-bonding-leave-link>medical leave after giving birth</about-bonding-leave-link>. You should not submit a second application.",
  infoAlertBody_pregnancy:
    "You may be able to take up to 12 weeks of paid family leave to bond with your child after your medical leave ends. <about-bonding-leave-link>Family leave to bond with your child</about-bonding-leave-link> can be easily added to your application by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. You should not submit a second application.",
  infoAlertHeading_bonding:
    "If you are giving birth, you may also be eligible for paid medical leave",
  infoAlertHeading_pregnancy: "You may also be eligible for paid family leave",
  leavePeriodCaringAlert:
    "You will need a completed <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> for this$t(chars.nbsp)section.",
  leavePeriodContinuousDatesLeadMedicalOrPregnancy:
    "Your answer must match the continuous leave period start and end dates in the $t(shared.certificationFormMedical).",
  leavePeriodHasLeaveHintCare:
    "Your answer must match the $t(shared.certificationFormCare).",
  leavePeriodHasLeaveHintMedicalOrPregnancy:
    "Your answer must match the $t(shared.certificationFormMedical).",
  leavePeriodIntermittentDatesLeadMedicalOrPregnancy:
    "Your answer must match the intermittent leave start and end dates in the $t(shared.certificationFormMedical).",
  leavePeriodMedicalAlert:
    "You will need a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link> for this$t(chars.nbsp)section.",
  leavePeriodReducedDatesLeadMedicalOrPregnancy:
    "Your answer must match the reduced leave start and end dates in the $t(shared.certificationFormMedical).",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Bond with a child",
  leaveReasonBondingHeader: "Leave to bond with a child",
  leaveReasonCare: "Care for a family member",
  leaveReasonCareHeader: "Leave to care for a family member",
  leaveReasonMedical: "Medical leave",
  leaveReasonMedicalIllness: "Leave for an illness or injury",
  leaveReasonMedicalSchedule: "Medical leave schedule",
  leaveReasonPregnancy: "Medical leave for pregnancy or birth",
  leaveReasonPregnancyHeader: "Medical leave for pregnancy",
  leaveReasonServiceMemberFamily: "Military family",
  loadingClaimDetailLabel: "Loading details",
  loadingDocumentsLabel: "Loading documents",
  maxEmployerCommentLengthError:
    "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
  maximumReducedLeaveMinutes:
    "Hours you will take off cannot exceed your work schedule.",
  minimumReducedLeaveMinutes:
    "Reduced leave schedule hours must be 0 or greater.",
  minutesLabel: "Minutes",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>",
  newbornCertificationDocOptions:
    "<ul><li>Your child’s birth certificate.</li><li>A note from your child’s health care provider stating your child’s date of birth.</li><li>A note from the health care provider of the person who gave birth stating your child’s date of birth.</li></ul>",
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
  saveAndContinue: "Save and continue",
  siteDescription:
    "Apply for this Commonwealth-offered benefit here, or log in to review your applications.",
  startByPhoneDescription:
    "Some applications started on the phone can be added to this website. Once added, you can upload documents and see your application’s status and payments online.",
  startByPhoneLabel: "Did you start an application by phone?",
  submitApplicationButton: "I understand and agree",
  trackStatus:
    "<track-status-link>Track the status of your application here</track-status-link>.",
  uploadingMessage: "Uploading documents… Do not refresh or go back.",
  usernameLabel: "Email address",
  verificationCodeLabel: "6-digit code",
  viewPostSubmissionVideo:
    "View the video below to learn about what happens between submitting your application and receiving payments.",
};

const pages: {
  // Keys are limited to three levels deep, for example `pages.claimsDateOfBirth.title`.
  // This makes the structure easier to navigate and the process of finding a specific element more consistent
  [pageKey: string]: I18nContentGroup;
} = {
  app: {
    seoDescription: "$t(shared.siteDescription)",
  },
  applications: {
    addApplication: "$t(shared.addApplication)",
    can_submit_application_across_benefit_year:
      "If you submit an application with leave dates that are in both your current and a new benefit year, we'll review the request as two separate applications. $t(pages.applications.claimsApprovalProcess)",
    claimsApprovalProcess:
      "Learn more about the <approval-process-link>application review and approval process</approval-process-link>.",
    createApplicationHeading: "Create a new application",
    getReadyLink: "Start a new application",
    startByPhoneDescription: "$t(shared.startByPhoneDescription)",
    startByPhoneLabel: "$t(shared.startByPhoneLabel)",
    title: "Your applications",
    uploadSuccessHeading: "You successfully submitted your documents",
    uploadSuccessMessage:
      "Our Contact Center staff will review your documents for {{absence_id}}.",
    your_benefit_year:
      "Your current <benefit-year-guide-link>benefit year</benefit-year-guide-link> is {{startDate}} to {{endDate}}. Most Massachusetts employees are eligible for up to 26 weeks of combined family and medical leave per benefit year.",
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
    title: "Create an employee account to apply for paid leave",
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
      "Thanks for verifying your email address. You may now log in to your account.",
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
      "We sent a 6-digit code to your email address. If you don’t see that email, check your spam folder. If you didn’t get an email with a code, you may need to <verify-link>verify your email address</verify-link> before you can reset your$t(chars.nbsp)password.",
    codeResentHeading: "Check your email",
    codeResent_email:
      "We sent a 6-digit code to {{emailAddress}}. If you don’t see that email, check your spam folder. If you didn’t get an email with a code, you may need to <verify-link>verify your email address</verify-link> before you can reset your$t(chars.nbsp)password.",
    lead: "If you received a 6-digit code to create a new password, enter it below to confirm your email and reset your password.",
    lead_email:
      "If an account exists for {{emailAddress}}, we emailed a 6 digit verification code to it. Enter the code below to confirm your email and reset your password.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    submitButton: "Set new password",
    title: "Create a new password",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  authTwoFactorSmsConfirm: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead: "Enter the 6-digit code we sent to your phone number {{mfaPhoneNumber}}.",
    resendCodeButton: "$t(shared.resendVerificationCodeLink)",
    saveButton: "$t(shared.saveAndContinue)",
    title: "Confirm your phone number",
  },
  authTwoFactorSmsIndex: {
    hint: "<p>This optional step makes your account more secure. This will also allow you to access sensitive information like tax documents (when available).</p><p>If you select Yes, we’ll ask for a phone number that can receive text messages (SMS). When you log in to your account, we’ll send a 6-digit code you’ll need to enter to verify it’s really you.</p><p>You can add or change your phone number later by going to the Settings page.</p>",
    optIn: "Yes, I want to add a phone number for additional security.",
    optOut: "No, I do not want to add a phone number.",
    optOutNoSms: "I do not have a phone that can receive text messages.",
    saveButton: "$t(shared.saveAndContinue)",
    title:
      "Do you want to add a cell phone number to verify it's you when you log in?",
  },
  authTwoFactorSmsSetup: {
    lead: "Enter a number that can receive text messages and that you'll have consistent access to. We’ll send a 6-digit code by text message (SMS) to confirm your phone number.",
    phoneNumberLabel: "Phone number",
    saveButton: "$t(shared.saveAndContinue)",
    skipButton: "$t(shared.auth.skip)",
    title:
      "Provide a phone number we can use when we need to verify your login",
  },
  authTwoFactorSmsVerify: {
    codeLabel: "$t(shared.verificationCodeLabel)",
    lead: "To protect your security we sent a 6-digit code to the phone number we have on file for verification.  Don’t share this code with anyone. We’ll never call or text you for this code.",
    resendCode:
      "To receive a new code, <login-link>log in again</login-link>. If you need help, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    submitButton: "Submit",
    title: "Enter your security code",
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
    afterSubmissionAlert_partOne:
      "You successfully submitted Part 1. Submit Parts 2 and 3 so that we can review your application.",
    afterSubmissionAlert_payment:
      "You successfully submitted your payment method. Complete the remaining steps so that you can submit your application.",
    afterSubmissionAlert_taxPref:
      "You successfully submitted your tax withholding preference. Complete the remaining steps so that you can submit your application.",
    backButtonLabel: "Back to applications",
    completed_editable: "Completed",
    completed_uneditable: "Confirmed",
    documentsLoadError: "$t(shared.documentsLoadError)",
    edit: "Edit",
    leaveDetailsBenefitYears:
      "Your leave dates extend into a new benefit year. Your current <benefit-year-guide-link>benefit year</benefit-year-guide-link> is {{startDate}} to {{endDate}}. After you submit Part 1 of your application, we'll automatically split this application into two, one for each benefit year.",
    // TODO (CP-2354) Remove CC guidance for claims with Part 1 submitted without reductions data
    otherLeaveSubmittedDetailsBody:
      "<ul><li>You have already taken leave to care for a family member since July 1, 2021</li><li>You have already taken leave since {{otherLeaveStartDate}} <when-can-i-use-pfml>for any other reason that qualifies for PFML</when-can-i-use-pfml></li><li>You plan to use any accrued paid leave or any other benefits from your employer during your paid leave from PFML (for example: your employer’s parental leave program or paid sick time)</li><li>You expect to get income from any other sources during your leave (for example: disability insurance, retirement benefits, or another job)</li></ul>",
    otherLeaveSubmittedDetailsLabel: "What do I need to report?",
    otherLeaveSubmittedIntro:
      "<p>If you have any other leaves, benefits, or income to report, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",

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
      "You will need to know:<ul><li>Your employer’s 9 digit federal employer identification number (FEIN or EIN). <br><strong>Where to find this: </strong>on your W$t(chars.nbhyphen)2 or 1099-MISC, or ask your employer’s finance department.</li><li>The date you told your employer you were taking leave.</li></ul><p>If you are taking leave from multiple employers, you must create separate applications for each job.</p>",
    stepHTMLDescription_leaveDetails:
      "<p>If you’re not sure what kind of leave to apply for, <which-paid-leave-link>learn more about Paid Family and Medical Leave</which-paid-leave-link>.</p><p><strong>Are you taking medical leave for your own serious health condition?</strong></p><p>You need to have a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link>. Use your health care provider’s answers on the certification form to fill out some parts of the application.</p><p>If you give birth and plan to take both pregnancy-related medical leave and family leave to bond with your newborn, you should apply for medical leave first. Family leave to bond with your child can be easily added to your application by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p><strong>Are you taking leave to bond with a child?</strong></p><p>You need to know the child’s date of birth, due date, or the date they arrived in your home for adoption or foster care.</p><p>You also need to know when you want your leave to begin and end.</p><p><strong>Are you taking leave to care for a family member?</strong></p><p>You need to have the <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> completed by their health care provider. You will need to use the health care provider’s answers on the certification form to fill out some parts of the application.</p><p>You also need to be sure of the <caregiver-relationship-link>eligibility of your relationship</caregiver-relationship-link>.</p>",
    stepHTMLDescription_medical:
      "<p>You need to provide your completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link>.</p><p>Your certification documents will be shared with your employer as part of your leave application.</p>",
    stepHTMLDescription_otherLeave:
      "You will need to know:<ul><li>If you will use any benefits from your employer because you are taking leave.</li><li>If you will receive income from any other sources during your leave.</li><li>The dates for any leave you’ve taken since {{otherLeaveStartDate}} for a reason that is covered by Paid Family and Medical Leave.</li></ul>",
    stepHTMLDescription_payment:
      "<p>If you want to receive payment by direct deposit, you will need to provide your bank account information, including a routing number and account number.</p>",
    stepHTMLDescription_reviewAndConfirm:
      "<p>Once you confirm your leave information, we’ll notify your employer. Your job will be protected. To complete your application, you will need to finish the following three steps and submit.</p><p>If you need to edit your information in Part 1 after completing this step, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    stepHTMLDescription_taxWithholding:
      "<p>You need to decide if you want to withhold state and federal taxes from this benefit. If you're unsure, we recommend speaking with a tax professional.</p>",
    stepHTMLDescription_uploadId:
      "<p>Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same$t(chars.nbsp)ID.</p><p>For other IDs, follow the instructions for acceptable proof of identity on the upload page.</p>",
    stepHTMLDescription_verifyId:
      "<p>You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card.</p><p>You will need to provide:</p><ul><li>Your name as it appears on your ID.</li><li>Your driver’s license number or Mass ID number, if you have one.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li></ul>",
    stepListDescription_1:
      "Your progress is automatically saved as you complete the application. You can edit any information you enter in Part 1 until step 5 is completed.",
    stepListDescription_1_submitted:
      "Your in-progress application will be viewable by our Contact Center staff. If you need to edit your information in Part 1, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_2:
      "Entering information here leads to faster processing, but you can also call$t(chars.nbsp)<contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
    stepListDescription_2_submitted:
      "If you need to edit your information in Part 2, you’ll need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>.",
    stepListDescription_3:
      "Uploading documents online leads to faster processing, but you can also <mail-fax-instructions-link>fax or mail documents</mail-fax-instructions-link>.",
    stepListTitlePrefix: "Part {{number}}",
    stepListTitle_1: "Tell us about yourself and your leave",
    stepListTitle_2: "Tell us how you want to receive your benefit",
    stepListTitle_3: "Upload your documents",
    stepTitle_employerInformation: "Enter employment information",
    stepTitle_leaveDetails: "Enter leave details",
    stepTitle_otherLeave: "Report other leave, benefits, and income",
    stepTitle_payment: "Enter payment method",
    stepTitle_reviewAndConfirm: "Review and confirm",
    stepTitle_taxWithholding: "Enter tax withholding preference",
    stepTitle_uploadCertification: "Upload leave certification documents",
    stepTitle_uploadId: "Upload identification document",
    stepTitle_verifyId: "Verify your identification",
    submitButton: "Review and submit application",
    title: "Your in-progress application",
    titleBody: "Submit all three parts so that we can review your application.",
  },

  claimsConcurrentLeaves: {
    choiceNo: "$t(shared.choiceNo)",
    choiceNoHint:
      "I don’t need to report any employer-sponsored paid time off after the 7-day waiting period, or I don’t know yet",
    choiceYes: "$t(shared.choiceYes)",
    choiceYesHint:
      "I need to report employer-sponsored paid time off I will use after the 7-day waiting period.",
    dontNeedToReport:
      "Don’t report paid time off that you use during the 7-day waiting period",
    dontNeedToReport_intermittentLeave:
      "You don't need to report accrued paid leave that you use during the 7-day waiting period, which is 7 consecutive calendar days from the date of the first instance of leave from your employer",
    hintWhatKindBody:
      "<p>This includes any paid vacation time, sick time, and personal time. It should be reported if it’s taken during your leave period, whether it’s during the 7-day waiting period or after. Reminder: you can use accrued paid leave during the 7-day waiting period with no impact to your PFML benefit.</p>",
    hintWhatKindHeading: "What kinds of paid time off to report",
    hintWhenToReportBody:
      "<p>If your PFML leave includes taking time off work completely for a period of time (continuous leave), you need to report any accrued paid leave you plan to take during that continuous leave. Select Yes to report this leave.</p><p>If your PFML leave includes working fewer hours than normal (a reduced leave schedule) or taking time off work in uneven or unpredictable blocks of time (intermittent leave), you need to report leave if ONE of the following two statements is true:</p><ul><li>You are planning to use this accrued paid leave on days when you are also taking PFML leave.</li><li>You are planning to use this accrued paid leave for a PFML qualifying reason, even if it’s not the same reason you are applying for now.</li></ul>",
    hintWhenToReportDetailsBody:
      "<ul><li>You had a serious health condition, including illness, injury, or pregnancy.</li><li>If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care.</li><li>You bonded with your child after birth or placement.</li><li>You needed to manage family affairs while a family member is on active duty in the armed forces.</li><li>You needed to care for a family member who serves in the armed forces.</li><li>You needed to care for a family member with a serious health condition.</li></ul>",
    hintWhenToReportDetailsLabel: "What are the qualifying reasons?",
    hintWhenToReportHeading: "When you need to report it",
    intro_Continuous:
      "Employer-sponsored paid vacation time, sick time, and personal time you plan to take during your paid leave from PFML.",
    intro_ContinuousReduced:
      "Employer-sponsored paid vacation time, sick time, and personal time.",
    intro_ReducedOrIntermittent:
      "<div><p>Employer-sponsored paid vacation time, sick time, and personal time that:</p><ul><li>You are planning to use on days when you are also taking PFML leave.</li></ul><p>Or</p><ul><li>You are planning to use for a PFML qualifying reason, even if it’s not the same reason you are applying for now.</li></ul></div>",
    sectionLabel:
      "Will you use any employer-sponsored paid time off during your leave period?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typesOfLeaveToReport:
      "For PFML leave that includes taking time off work completely for a period of time (continuous leave), you need to report any accrued paid leave you plan to take during that continuous leave.",
    whenToReportContinuousLeave: "When to report during continuous leave",
    whenToReportReducedLeave: "When to report during reduced leave",
  },
  claimsConcurrentLeavesDetails: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    detailsBody:
      "Employer-sponsored paid vacation time, sick time, and personal time you plan to take during your paid leave from PFML.",
    detailsLabel: "What is employer-sponsored paid time off?",
    hintHeader:
      "This is the same Employer Identification Number you entered earlier in your application. After you submit your application, this employer will be able to review it. We won’t share any leave you plan to take from other employers.",
    leaveEndDateLabel:
      "What is the last day of your employer-sponsored paid time off?",
    leaveStartDateLabel:
      "What is the first day of your employer-sponsored paid time off?",
    sectionLabel:
      "Will you use employer-sponsored paid time off from this employer? EIN: {{employer_fein, ein}}",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsConcurrentLeavesIntro: {
    intro:
      "<p>Next, we need to know about paid time off from your employer that you plan to use between {{startDate}} and {{endDate}}. This includes paid vacation time, sick time, personal time, and other paid time off provided by your employer. You do not need to tell us about short or long-term disability programs, or other family or medical leave benefits provided by your employer in this section. We’ll ask about that in the next section.</p><p>When your PFML leave begins, there is a 7-day waiting period before PFML payments start. During this 7-day waiting period, you can use paid time off from your employer with no impact to your PFML benefit.</p><p>After the 7-day waiting period, <strong>you cannot use both employer-sponsored paid time off and paid leave from PFML on the same day.</strong> In some cases, using accrued paid leave after the 7-day waiting period has ended can cause your PFML benefits to stop. You will need to re-apply to receive PFML benefits again. To avoid this, use accrued paid leave only at the start or end of your PFML leave. <examples-of-using-paid-leave>See examples of how you can use accrued paid leave</examples-of-using-paid-leave>.</p>",
    sectionLabel:
      "Tell us about the employer-sponsored paid time off you’ll use during your  leave period.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsDateOfBirth: {
    sectionLabel: "What’s your date of birth?",
    title: "$t(shared.claimsVerifyIdTitle)",
  },
  claimsEmployerBenefits: {
    choiceNo: "$t(shared.choiceNo)",
    choiceNoAlert:
      "If you receive any other employer-sponsored benefits after you apply, you’ll need to call the Contact Center to let us know.",
    choiceNoHint:
      "I won’t receive employer-sponsored benefits, I've applied but it hasn't been approved, or I don’t know the benefit amount yet",
    choiceYes: "$t(shared.choiceYes)",
    choiceYesHint:
      "I will receive employer-sponsored benefits during my paid leave",
    doNotReportHintHeading: "You don’t need to report:",
    doNotReportHintList:
      "<ul><li>Benefits from any other employers</li><li>Temporary disability insurance that does not fully replace your wages</li></ul>",
    doReportHintHeading: "The employer-sponsored benefits you must report are:",
    doReportHintList:
      "<ul><li>Temporary disability insurance that fully replaces your wages, for either short-term or long-term disability</li><li>Permanent disability insurance</li><li>Family or medical leave benefits, such as a parental leave program</li><li>You only have to report benefits from the employer with this EIN: {{employer_fein}}. This is the same Employer Identification Number you entered earlier in your application.</li></ul>",
    sectionLabel:
      "Will you use any employer-sponsored benefits from this employer during your paid leave from PFML?",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsEmployerBenefitsDetails: {
    addButton: "Add another benefit",
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
  claimsImport: {
    absenceIdHint:
      "Enter the application ID given to you when you applied by phone. It contains both numbers and letters and looks like NTN-123456-ABS-01.",
    absenceIdLabel: "Application ID",
    leadIdentify: "We need some information to identify your application.",
    leadIntro:
      "Some applications started on the phone can be added to this website. Once added, you can upload documents and see your application’s status and payments online.",
    mfaDisabledWarningBody:
      "In order to add an existing application, you need to provide a phone number we can use to <verify-link>verify your login</verify-link>. This number must match the one you gave the Contact Center when you applied.",
    mfaDisabledWarningHeading: "We need to verify your login.",
    phoneHint:
      "This number must match the one you gave the Contact Center when you applied.",
    phoneLabel: "Cell phone number",
    phoneLink_unverified: "Verify your login",
    phoneLink_verified: "Change your phone number",
    submitButton: "Add application",
    taxIdHint:
      "Don’t have a Social Security Number? Use your Individual Taxpayer Identification Number (ITIN).",
    taxIdLabel: "Social Security Number",
    title: "Add an existing application",
    uploadingMessage: "Submitting… Do not refresh or go back",
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
      "If you have already taken family leave to bond with a child since their date of birth, or the date of their adoption or foster care placement, tell us the first day you missed work, and the last day you expect to be on leave.<br /><br />You must complete your leave before the child’s first birthday, or the one-year anniversary of their adoption or foster care placement.",
    datesLead_care:
      "Your answer must match the continuous leave period start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodContinuousDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodContinuousDatesLeadMedicalOrPregnancy)",
    datesSectionLabel:
      "Enter the start and end dates for your continuous leave.",
    endDateLabel: "Last day of leave",
    hasLeaveHint_care: "$t(shared.leavePeriodHasLeaveHintCare)",
    hasLeaveHint_medical:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_pregnancy:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
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
      "If you have already taken family leave to bond with a child since their date of birth, or the date of their adoption or foster care placement, tell us the first day you missed work, and the last day you expect to be on leave.<br /><br />You must complete your leave before the child’s first birthday, or the one-year anniversary of their adoption or foster care placement.",
    datesLead_care:
      "Your answer must match the intermittent leave start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodIntermittentDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodIntermittentDatesLeadMedicalOrPregnancy)",
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
      "If you have already taken family leave to bond with a child since their date of birth, or the date of their adoption or foster care placement, tell us the first day you missed work, and the last day you expect to be on leave.<br /><br />You must complete your leave before the child’s first birthday, or the one-year anniversary of their adoption or foster care placement.",
    datesLead_care:
      "Your answer must match the reduced leave start and end dates in the $t(shared.certificationFormCare).",
    datesLead_medical:
      "$t(shared.leavePeriodReducedDatesLeadMedicalOrPregnancy)",
    datesLead_pregnancy:
      "$t(shared.leavePeriodReducedDatesLeadMedicalOrPregnancy)",
    datesSectionLabel:
      "Enter the start and end dates for your reduced leave schedule.",
    endDateLabel: "Last day of leave",
    endDateLabel_medical: "Last day of leave",
    hasLeaveHint_care: "$t(shared.leavePeriodHasLeaveHintCare)",
    hasLeaveHint_medical:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
    hasLeaveHint_pregnancy:
      "$t(shared.leavePeriodHasLeaveHintMedicalOrPregnancy)",
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
      "Leave is determined based on your benefit year (a period of 52 weeks starting on the Sunday prior to your first day of paid leave through any leave program), not based on the number of children. You have 1 year to take your family leave from the date of the birth/placement of your child. <multiple-births-link>Learn more about taking leave for multiple childbirths or placements</multiple-births-link>.",
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
  claimsModifyCancel: {
    sectionLabel: "Are you sure you want to cancel your leave?",
    title: "$t(shared.claimsModifyTitle)",
  },
  claimsModifyChecklist: {
    backButtonLabel: "$t(shared.backToYourApplicationsLink)",
    title: "Welcome back to your in-progress change request",
  },
  claimsModifyGetReady: {
    backButtonLabel: "$t(shared.backToYourApplicationsLink)",
    button: "Continue",
    title: "Request a change to your application",
  },
  claimsModifyReview: {
    sectionLabel: "Review and submit your requested change",
    title: "$t(shared.claimsModifyTitle)",
  },
  claimsModifySuccess: {
    backButtonLabel: "$t(shared.backToYourApplicationsLink)",
    title: "You've submitted your change request",
  },
  claimsModifyType: {
    sectionLabel: "How do you want to change your application?",
    title: "$t(shared.claimsModifyTitle)",
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
  claimsOrganizationUnit: {
    choiceNo: "$t(shared.choiceNo)",
    choiceNotSure: "I'm not sure",
    choiceYes: "$t(shared.choiceYes)",
    comboBoxLabel: "Select your department",
    confirmHint:
      "Based on what you’ve entered, our records show you work at <strong>{{organization_unit}}</strong>. Is this the department where you are applying to take leave?",
    confirmSectionLabel: "Confirm your department",
    failureWarning:
      "Failure to select the right department will delay your application.",
    followupInfo:
      "Our team will check their records to find your department. If there is no match, someone from the Contact Center will follow up with you after you apply to make sure the right department reviews your application.",
    sectionLabel: "Select the department where you are applying to take leave",
  },
  claimsOtherIncomes: {
    choiceNo: "$t(shared.choiceNo)",
    choiceNoAlert:
      "If you receive any other income after you apply, you’ll need to call the Contact Center to let us know.",
    choiceNoHint:
      "I won't receive other income from the above sources during my paid leave,  I've applied but it hasn't been approved, or I don’t know the income amount yet",
    choiceYes: "$t(shared.choiceYes)",
    choiceYesHint:
      "I will receive other income from other sources during my paid leave",
    doNotReportHintHeading: "You don't need to report:",
    doNotReportHintList:
      "<ul><li>Other income that you've applied for but are not yet receiving</li><li>Income from past PFML benefits</li><li>Income received through a bonus, like a holiday bonus or an annual sum paid out at the end of the year</li></ul>",
    doReportHintHeading: "You must report these sources of income:",
    doReportHintList:
      "<ul><li>Workers Compensation</li><li>Unemployment Insurance</li><li>Social Security Disability Insurance</li><li>Disability benefits under a governmental retirement plan such as STRS or PERS</li><li>Jones Act benefits</li><li>Railroad Retirement benefits</li><li>Earnings or benefits from another employer, or through self-employment<ul>",
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
    accountNumberWarning:
      "Your account number looks similar to a routing number. Check that you entered your account number correctly.",
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
    retypeAccountNumberHint:
      "Make sure your account numbers match exactly. You can't copy and paste into this field.",
    retypeAccountNumberLabel: "Retype account number",
    retypeAccountNumberRequired: "Retype your account number",
    routingNumberHint:
      "This is the 9-digit number found on the lower left corner of a check or deposit slip.",
    routingNumberLabel: "Routing number",
    sectionLabel: "How do you want to get your weekly benefit?",
    sectionLabelHint:
      "Your choice will be applied to any previous applications you have submitted.",
    submitPayment: "Submit payment method",
    title: "Payment method",
    warning:
      "After you submit your payment method, it can’t be edited on this website. To change it, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.",
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
    detailsBenefitYear:
      "<p>The benefit year is a period of 52 weeks that starts on the Sunday before when you first miss work for a qualifying reason. You are entitled to up to 20 weeks of medical leave, 12 weeks of family leave, or 26 weeks for a combination of both during a single benefit year.</p><p>You can submit an application for leave that crosses into a new benefit year. We will review the request as if it is two separate applications. The Department's determination for one application may be different from its determination for the other.</p><p>Example: The first time you took leave for a qualifying reason began on Thursday, April 1, 2021. The benefit year began on the Sunday before, which is March 28, 2021. The benefit year lasts 52 weeks and ends on Saturday, which is March 26, 2022.</p><ul><li>Your example first day of leave: 4/1/2021</li><li>Your example benefit year: 3/28/2021 to 3/26/2022</li></ul>",
    detailsBenefitYearHeader: "What is a benefit year?",
    detailsQualifyingReason:
      "<p>A qualifying reason is the cause or event that makes you unable to work and eligible for Paid Family and Medical Leave benefits.</p><p>Qualifying reasons include:</p><ul><li>Bonding with your child during the first 12 months after birth, adoption, or placement</li><li>Caring for a family member with a serious health condition as certified by a health care provider, including illness, injury, or pregnancy</li><li>Managing affairs while a family member is on active duty</li><li>Caring for a family member who was injured serving in the armed forces</li><li>Caring for your own serious health condition as certified by a health care provider, including illness, injury, or pregnancy</li></ul>",
    detailsQualifyingReasonHeader: "What is a qualifying reason?",
    dontNeed:
      "<ul><li>Leave that was taken through Massachusetts’ PFML program</li><li>Leave that was taken outside of your current benefit year</li><li>Family leave to care for a family member before July 1, 2021</li></ul>",
    dontNeedHeader: "You don’t need to report:",
    need: "<ul><li>Any previous leave (paid or unpaid) for the same reason that you are applying for paid leave now</li><li>Any previous leave for a different qualifying reason</li></ul>",
    needHeader:
      "You’ll need to report previous leave you have taken between {{otherLeaveStartDate}} and {{startDate}}:",
    sectionLabel: "Tell us about your previous leave.",
    title: "$t(shared.claimsOtherLeaveTitle)",
  },
  claimsPreviousLeavesOtherReason: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    detailsLabel: "What counts as a qualifying reason?",
    hintDoHeader:
      "You must report paid or unpaid leave for these qualifying reasons that aren't the reason you are applying for paid leave now:",
    hintDontHeader: "You don't need to report:",
    hintHeader:
      "Answer yes if you took paid or unpaid leave for a qualifying reason that is not the reason you are applying for paid leave now. The following are qualifying reasons:",
    hintList:
      "<ul><li>You had a serious health condition, including illness, injury, or pregnancy.</li><li>If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care.</li><li>You bonded with your child after birth or placement.</li><li>You needed to manage family affairs while a family member is on active duty in the armed forces.</li><li>You needed to care for a family member who serves in the armed forces.</li><li>You needed to care for a family member with a serious health condition and your leave began on or after July 1, 2021.</li></ul>",
    hintTextNo:
      "I haven’t taken previous leave for a qualifying reason, or my other leave was through Massachusetts’ PFML program",
    hintTextYes:
      "I have taken previous leave for one or more qualifying reasons",
    leaveTakenThroughPFML:
      "<ul><li>Leave that was taken through Massachusetts' PFML program</li></ul>",
    sectionLabel:
      "Did you take any previous leave between {{otherLeaveStartDate}} and {{leaveStartDate}} and for a different qualifying reason?",
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
    leaveEndDateHint: "$t(shared.claimsPreviousLeaveDetails.minimumDateHint)",
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
    leaveStartDateHint: "$t(shared.claimsPreviousLeaveDetails.minimumDateHint)",
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
    hintNo:
      "I have not taken previous leave for the same reason, or my other leave was through Massachusetts’ PFML program",
    hintYes: "I have taken previous leave for the same reason",
    sectionLabel:
      "Did you take any previous leave between {{previousLeaveStartDate}} and {{leaveStartDate}} for the same reason as you are applying for paid leave now?",
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
    leaveEndDateHint: "$t(shared.claimsPreviousLeaveDetails.minimumDateHint)",
    leaveEndDateLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveEndDateLabel)",
    leaveMinutesHint: "$t(shared.claimsPreviousLeaveDetails.leaveMinutesHint)",
    leaveMinutesLabel:
      "$t(shared.claimsPreviousLeaveDetails.leaveMinutesLabel)",
    leaveStartDateHint: "$t(shared.claimsPreviousLeaveDetails.minimumDateHint)",
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
    employeeOrganizationUnit: "Department",
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
    leaveDetailsBenefitYearsIntroduction:
      "<p>Your current <benefit-year-guide-link>benefit year</benefit-year-guide-link> is {{startDate}} to {{endDate}}. After you submit Part 1 of your application, we'll automatically split this application into two, one for each benefit year. You can upload the same supporting documentation for both applications.",
    leaveDetailsBenefitYearsSixtyYearsAndBelow:
      "<p>Your current <benefit-year-guide-link>benefit year</benefit-year-guide-link> is {{startDate}} to {{endDate}}. After you submit Part 1 of your application, we'll automatically split this application into two, one for each benefit year. You can upload the same supporting documentation for both applications.</p><ul><li><strong>Current benefit year:</strong> leave dates from 2/14/2022 to 2/26/2022</li><li><strong>New benefit year:</strong> leave dates from 2/27/2022 to 4/19/2022</li></ul><p>We’ll review each application separately. This means that:</p><ul><li>The Department's determination for one application may be different from its determination for the other.</li><li> The Department will calculate your weekly benefit amount for each application separately. You may receive different payment amounts for each application. Learn more about how PFML weekly benefit amounts are calculated.</li><li>You'll have two 7-day waiting periods, one at the start of each period of your leave. Learn more about the <benefit-year-guide-link>7-day waiting period.</benefit-year-guide-link></li></ul>",
    leaveDetailsCurrentBenefitYearsDates:
      "<strong>Current benefit year:</strong> leave dates from {{startDate}} to {{endDate}}",
    leaveDetailsNewBenefitYearsDates:
      "<strong>New benefit year:</strong> leave dates from {{startDate}} to {{endDate}}",
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
    partDescription:
      "If you need to make edits to Part {{step}}, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Your application ID is <strong>{{absence_id}}</strong>",
    partHeadingPrefix: "Part {{number}}",
    partHeading_1: "Review: Tell us about yourself and your$t(chars.nbsp)leave",
    partHeading_2: "Review: Tell us how you want to receive your payment",
    partHeading_3: "Review: Upload your documents",
    partOneNextSteps:
      "<p>Once you review and submit Part 1, your in-progress application will be viewable by our Contact Center staff. If you need to make edits to Part 1, you’ll need to call our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>We’ll also notify your employer that you’ve started an application for paid family and medical leave.</p><p>Next, you’ll be able to work on Parts 2 and 3, and submit your application.</p>",
    paymentAccountNumLabel: "Account number",
    paymentMethodLabel: "Direct deposit or paper check",
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
      "Family leave to manage family affairs while a family member was on active duty in the armed forces",
    previousLeaveReason_bonding:
      "Family leave to bond with a child after birth or placement",
    previousLeaveReason_care: "Family leave to care for a family member",
    previousLeaveReason_medical: "Medical leave for an illness or injury",
    previousLeaveReason_pregnancy: "Medical leave related to pregnancy",
    previousLeaveReason_serviceMemberFamily:
      "Family leave to care for a family member who serves in the armed forces",
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
    stepHeading_payment: "Payment method",
    stepHeading_tax: "Tax withholding",
    stepHeading_uploadCertification: "Upload certification document",
    stepHeading_uploadId: "Upload identity document",
    stepHeading_verifyId: "$t(shared.claimsVerifyIdTitle)",
    submitAction_final: "Submit application",
    submitAction_part1: "Submit Part 1",
    submitLoadingMessage: "Submitting… Do not refresh or go back.",
    taxLabel: "Withhold state and federal taxes?",
    taxNoWithhold: "$t(shared.choiceNo)",
    taxYesWithhold: "$t(shared.choiceYes)",
    title_final: "Review and submit your application",
    title_part1:
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
  claimsStatus: {
    applicationID: "Application ID",
    applicationTitle: "Application details",
    applicationUpdatesHeading: "Application updates",
    backButtonLabel: "$t(shared.backToYourApplicationsLink)",
    employerEIN: "Employer Identification Number (EIN)",
    infoAlertBody_bonding: "$t(shared.infoAlertBody_bonding)",
    infoAlertBody_pregnancy: "$t(shared.infoAlertBody_pregnancy)",
    infoAlertHeading_bonding: "$t(shared.infoAlertHeading_bonding)",
    infoAlertHeading_pregnancy: "$t(shared.infoAlertHeading_pregnancy)",
    infoRequestsBody_Decision:
      "We have made a final decision for this application. Your final decision notice has more details about the appeals process.<p>If you would like to appeal the final decision, you can do so using mail, fax, or our <online-appeals-form>online appeals form</online-appeals-form>.</p>",
    infoRequestsBody_Pending:
      "If you have a request for more information, use this button to upload the requested documentation.",
    infoRequestsHeading: "Respond to requests for information",
    leavePeriodDates: "From {{startDate}} to {{endDate}}",
    leavePeriodLabel_continuous: "$t(shared.claimDurationTypeContinuous)",
    leavePeriodLabel_intermittent: "$t(shared.claimDurationTypeIntermittent)",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReduced)",
    leaveReasonValueHeader_bonding: "$t(shared.leaveReasonBondingHeader)",
    leaveReasonValueHeader_care: "$t(shared.leaveReasonCareHeader)",
    leaveReasonValueHeader_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValueHeader_pregnancy: "$t(shared.leaveReasonPregnancyHeader)",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "Leave to bond with a child schedule",
    leaveReasonValue_care: "Leave to care for a family member schedule",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedicalSchedule)",
    leaveReasonValue_pregnancy: "$t(shared.leaveReasonMedicalSchedule)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveStatusMessage_Approved:
      "<strong>This leave was approved.</strong><p>View your approval notice below for more details about your benefit amount, and how to appeal if your benefits appear incorrect. Learn more about the <request-appeal-link>appeal process</request-appeal-link>.</p>",
    leaveStatusMessage_Cancelled:
      "<strong>This leave was cancelled.</strong><p>This application will no longer be processed. If you want to apply for paid leave again, you can begin another application.</p><p><application-link>Start another application</application-link></p>",
    leaveStatusMessage_Denied:
      "<strong>This leave was denied.</strong><p>View your denial notice below for more details and an explanation of the appeal process.</p><p>If you would like to appeal, you must submit your request within 10 calendar days of the date on your denial notice. Learn more about the <request-appeal-link>appeal process</request-appeal-link>.</p>",
    "leaveStatusMessage_In Review":
      "<strong>We’re reviewing your requested changes or appeal for this leave.</strong>",
    leaveStatusMessage_Pending:
      "<strong>This leave is being reviewed.</strong>",
    // TODO (PORTAL-1652): Create content for these request decision options
    leaveStatusMessage_Projected:
      "<strong>This leave is being reviewed.</strong>",
    leaveStatusMessage_Voided:
      "<strong>This leave was cancelled.</strong><p>This application will no longer be processed. If you want to apply for paid leave again, you can begin another application.</p><p><application-link>Start another application</application-link></p>",
    leaveStatusMessage_Withdrawn:
      "<strong>This leave was withdrawn.</strong><p>You have withdrawn your application from the review process. If you want to apply for paid leave again, you can begin another application.</p><p><application-link>Start another application</application-link></p>",
    legalNoticesFallback:
      "We will notify you once we’ve made a decision. You’ll be able to download the decision notice on this website.",
    loadingClaimDetailLabel: "$t(shared.loadingClaimDetailLabel)",
    loadingLegalNoticesLabel: "Loading legal notices",
    makeChangesBody:
      "<p>To make changes to your application, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. If you request a change to your start and end dates, we may need to review your application again.</p>",
    makeChangesHeading: "Make changes",
    manageApplicationHeading: "Manage your application",
    manageApprovedApplicationText:
      "<p>See more <manage-approved-app-link>examples of how to manage your approved application.</manage-approved-app-link></p>",
    reportOtherBenefitsBody:
      "<p>If your plans for other benefits or income during your paid leave have changed, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>. Report changes to:</p><ul><li>Benefits from your employer that you plan to use in addition to paid leave from PFML. For example, if you are taking a different amount of sick days than you first planned, or if you are taking employer sponsored parental leave on a different schedule than you expected, report this change.</li><li>Income from other sources during your leave. For example, if you got approved for a disability benefit or a worker’s compensation claim after you submitted your application, report this change.</li></ul>",
    reportOtherBenefitsHeading: "Report other benefits or income",
    statusTimelineNotice:
      "Notices usually appear within 30 minutes after we update the status of your application.",
    timelineDescription:
      "<p>Your application is complete when:</p><ul><li>You have submitted all required documents</li><li>Your employer has responded or their deadline passes</li></ul>",
    timelineHeading: "Timeline",
    timelineTextFollowUpEmployer:
      "<p>Your employer has until <strong>{{employerFollowUpDate}}</strong> to respond to your application.</p>",
    timelineTextFollowUpGenericDFML:
      "<p>We have <strong>14 calendar days</strong> after receiving your completed application to make a decision to approve, deny or request more information.</p>",
    timelineTextFollowUpGenericEmployer:
      "<p>Your employer has <strong>10 business days</strong> to respond to your application.</p>",
    timelineTextFollowUpMayTakeLonger:
      "<p>The process may take longer if we request more information to complete your application or if you request changes to your application.</p>",
    timelineTextLearnMore:
      "<p>Learn more about the <timeline-link>application approval process.</timeline-link></p>",
    uploadDocumentsButton: "Upload additional documents",
    uploadDocumentsHeading: "Upload Documents",
    uploadSuccessHeading: "You've successfully submitted your {{document}}",
    "uploadSuccessHeadingDocumentName_family-member-medical-certification":
      "$t(shared.documentCategory.certification)",
    "uploadSuccessHeadingDocumentName_medical-certification":
      "$t(shared.documentCategory.certification)",
    "uploadSuccessHeadingDocumentName_other-id":
      "$t(shared.documentCategory.identification)",
    "uploadSuccessHeadingDocumentName_pregnancy-medical-certification":
      "$t(shared.documentCategory.certification)",
    "uploadSuccessHeadingDocumentName_proof-of-birth":
      "proof of birth documents",
    "uploadSuccessHeadingDocumentName_proof-of-placement":
      "proof of placement documents",
    "uploadSuccessHeadingDocumentName_state-id":
      "$t(shared.documentCategory.identification)",
    viewNoticesHeading: "View your notices",
    viewPaymentTimeline:
      "<p>See your payment status and estimated payment date on your payments page.</p><p><payments-page-link>Track your payments</payments-page-link></p>",
    whatHappensNext: "What happens next",
    whatHappensNextButton_adoption: "Upload proof of adoption",
    whatHappensNextButton_fosterCare: "Upload proof of placement",
    whatHappensNextButton_newborn: "Upload proof of birth",
    whatYouNeedToDo: "What you need to do",
    whatYouNeedToDoText_adoption:
      "Once your child is adopted, submit a certificate of proof, including the date of the adoption, so that we can review your application. Learn more about the <proof-document-link>proof of adoption documents</proof-document-link> we accept.",
    whatYouNeedToDoText_fosterCare:
      "Once your child is placed, submit a certificate of proof, including the date of the placement, so that we can review your application. Learn more about the <proof-document-link>proof of placement documents</proof-document-link> we accept.",
    whatYouNeedToDoText_newborn: "$t(shared.docsRequired.newborn)",
  },
  claimsSuccess: {
    adjudicationProcess:
      "<ul> <li>Your employer has 10 business days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>We will notify you once we’ve made a decision. You’ll be able to read the details of the decision on this website. Your employer will also get a copy of the decision.</li><li>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started. If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts. After that, you will receive your payments every week.</li><li>$t(shared.trackStatus)</li><li>$t(shared.viewPostSubmissionVideo)</li></ul>",
    adjudicationProcessHeading: "What happens next",
    adjudicationProcess_bondingAdoptFosterFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of placement, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child arrived in your home earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li><li>$t(shared.trackStatus)</li><li>$t(shared.viewPostSubmissionVideo)</li></ul>",
    adjudicationProcess_bondingNewbornFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li> <li>Once you’ve provided proof of birth, we’ll confirm your eligibility and make sure that your documents are valid.</li> <li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li> <li>If you need to change your leave dates because your child was born earlier or later than expected, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li><li>$t(shared.trackStatus)</li><li>$t(shared.viewPostSubmissionVideo)</li></ul>",
    adjudicationProcess_caringLeave:
      "<ul><li>Your employer has 10 business days to provide feedback on your application.</li> <li>We’ll confirm your eligibility and make sure that your documents are valid.</li> <li>We will notify you once we’ve made a decision. You’ll be able to read the details of the decision on this website. Your employer will also get a copy of the decision.</li><li>Once your application is approved, you can expect your first payment to arrive at the beginning of your fourth week of leave, if your leave has already started. If your leave starts in the future, you can expect your first payment 2-4 weeks after your leave starts. After that, you will receive your payments every week.</li><li>If you need to end your leave early, you must call the DFML Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li><li>$t(shared.trackStatus)</li><li>$t(shared.viewPostSubmissionVideo)</li></ul>",
    adjudicationProcess_medicalPregnantFuture:
      "<ul><li>Your employer has 10 days to provide feedback on your application.</li><li>After we’ve made a decision, you’ll receive an email notification with a link to details about the decision.</li><li>If your application is approved prior to your leave, you can expect your first payment to arrive about 3 weeks after your leave starts. Otherwise, you can expect your first payment 2-3 weeks after your leave is approved.</li><li>$t(shared.trackStatus)</li><li>$t(shared.viewPostSubmissionVideo)</li></ul>",
    claimantApplicationId:
      "Your application ID is <strong>{{absence_id}}</strong>",
    exitLink: "View your application",
    familyLeaveToBond:
      "You may be able to take up to 12 weeks of paid family leave to bond with your child after your medical leave ends. <medical-bonding-link>Family leave to bond with your child</medical-bonding-link> can be easily added to your application by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> after your medical leave is approved. You should not submit a second application.",
    familyLeaveToBondHeading: "You may also be eligible for paid family leave",
    learnMore:
      "Review <benefits-amount-details-link>our benefits guide</benefits-amount-details-link> to find out more about how benefits are determined. For a rough estimate of how much you might receive, <benefits-calculator-link>use this calculator</benefits-calculator-link>. The maximum total amount that a person can receive in PFML benefits is ${{maxBenefitAmount}} per week, even if you have been approved for leave benefits from multiple employers.", // eslint-disable-line no-template-curly-in-string
    learnMoreHeading: "Learn more about paid leave benefits",
    medicalLeaveAfterBirth:
      "You may be able to take up to 20 weeks of paid medical leave if you’re unable to work during your pregnancy or for your recovery from childbirth. Your health care provider determines how much medical leave you will need. Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if you need <medical-bonding-link>medical leave after giving birth</medical-bonding-link>.",
    medicalLeaveAfterBirthHeading:
      "If you are giving birth, you may also be eligible for paid medical leave",
    proofRequired_bondingAdoptFosterFuture:
      "After your child arrives in your home, you will need to upload, mail, or fax a document that shows your child’s placement date.",
    proofRequired_bondingNewbornFuture:
      "After your child is born, you will need to upload, mail, or fax a document that shows your child’s date of birth.",
    proofRequired_medicalPregnantFuture:
      "You must call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> once your medical leave begins to confirm that your leave has begun. We can’t approve your application until we hear from$t(chars.nbsp)you.",
    reportReductionsHeading: "We may need more information from you",
    reportReductionsMessage:
      "<p>Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if any of these are true:</p><ul><li>You have already taken leave to care for a family member since July 1, 2021</li><li>You have already taken leave since January 1, 2021 for <when-can-i-use-pfml>any other reason that qualifies for PFML</when-can-i-use-pfml></li><li>You plan to use any accrued paid leave or any other benefits from your employer during your paid leave from PFML (for example: your employer’s parental leave program or paid sick time)</li><li>You expect to get income from any other sources during your leave (for example: disability insurance, retirement benefits, or another job)</li></ul>",
    title: "You submitted your application",
    viewStatus: "View status and details for your application",
  },
  claimsTaxWithholding: {
    choiceNo: "No, don’t withhold state and federal taxes",
    choiceYes: "Yes, withhold state and federal taxes",
    explanation:
      "<p>You have the option to have state and federal taxes withheld from your weekly benefit. If you choose to have taxes withheld, we will withhold 5% for state taxes and 10% for federal taxes. These percentages can’t be adjusted.</p><p>The IRS hasn’t decided if paid leave benefits are considered taxable income. Massachusetts tax treatment will follow the guidance provided by the IRS.</p><p>If you're unsure whether you want to withhold taxes, we recommend speaking with a <tax-professional-link>tax professional</tax-professional-link> about how IRS decisions could affect your personal tax liability. We cannot offer guidance or advice for individual tax situations.</p>",
    sectionLabel:
      "Do you want us to withhold state and federal taxes from this paid leave benefit?",
    submit: "Submit tax withholding preference",
    title: "Tax withholding",
    warning:
      "<p>After you submit your tax withholding preference, it can’t be edited on this website. To change it before your application has been approved, you will need to call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p><strong>Attention: This selection can’t be changed once your application has been approved.</strong></p>",
  },
  claimsUploadCertification: {
    addAnotherFileButton: "Choose another file",
    addFirstFileButton: "Choose files",
    certificationDocumentsCount: "$t(shared.filesUploaded)",
    documentsLoadError: "$t(shared.documentsLoadError)",
    fileHeadingPrefix: "File",
    leadListNewborn: "$t(shared.newbornCertificationDocOptions)",
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
    uploadingMessage: "$t(shared.uploadingMessage)",
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
  claimsUploadDocumentType: {
    addAnotherFileButton: "$t(shared.fileUpload_addAnotherFileButton)",
    addFirstFileButton: "$t(shared.fileUpload_addFirstFileButton)",
    documentsLoadError: "$t(shared.documentsLoadError)",
    fileHeadingPrefix: "$t(shared.fileUpload_fileHeadingPrefix)",
    idAccordionContent:
      "<p><strong>If you don’t have any of those, you can provide one of the following plus proof of your Social Security Number or Individual Tax Identification Number:</strong></p><ul><li>Valid, unexpired U.S. State or Territory License or ID, both front and back</li><li>Certified copy of a birth certificate filed with a State Office of Vital Statistics or equivalent agency in the individual’s state of birth. (You can only use a <puerto-rican-birth-certificate-link>Puerto Rican birth certificate</puerto-rican-birth-certificate-link> if it was issued on or after July 1, 2010.)</li><li>Certificate of Citizenship (Form N$t(chars.nbhyphen)560, or Form N$t(chars.nbhyphen)561)</li><li>Certificate of Naturalization (Form N$t(chars.nbhyphen)550 or N$t(chars.nbhyphen)570)</li></ul><p><strong>You can provide proof of your Social Security Number using one of the following documents displaying your complete Social Security Number:</strong></p><ul><li>Social Security card</li><li>W$t(chars.nbhyphen)2 Form</li><li>SSA$t(chars.nbhyphen)1099 Form</li><li>Non$t(chars.nbhyphen)SSA$t(chars.nbhyphen)1099 Form</li><li>Pay stub with your name on it</li></ul><p><identity-proof-link>Learn more about verifying your identity with different documents.</identity-proof-link></p>",
    idAccordionHeading: "If you don’t have any of those documents:",
    leadListNewborn: "$t(shared.newbornCertificationDocOptions)",
    lead_bonding_adopt_foster:
      "You need to upload a statement from your adoption or foster agency or from the Massachusetts Department of Children and Families to confirm the placement and the date of the placement.",
    lead_bonding_newborn:
      "You need to upload one of the following documents to confirm your child’s date of birth:",
    lead_care:
      "You need to upload a completed <caregiver-certification-form-link>$t(shared.certificationFormCare)</caregiver-certification-form-link> to prove that you need to take leave to care for a family member with a serious medical condition.",
    lead_medical:
      "You need to upload a completed <healthcare-provider-form-link>$t(shared.certificationFormMedical)</healthcare-provider-form-link> to prove that you need to take medical leave.",
    otherIdentityDocs:
      "<p><strong>You can upload a copy of one of the following documents:</strong></p><ul><li>U.S. State or Territory Real ID, both front and back</li><li>U.S. passport or passport card</li><li>Permanent Resident Card issued by DHS or INS</li><li>Employment Authorization Document (EAD) issued by DHS</li><li>Foreign passport <strong>and</strong> a <work-visa-link>work visa</work-visa-link></li></ul>",
    sectionLabel_bonding: "Upload your documentation",
    sectionLabel_certification: "Upload your certification form",
    sectionLabel_massId:
      "Upload the front and back of your Massachusetts driver’s license or ID card",
    sectionLabel_otherId:
      "Upload an identification document issued by state or federal government",
    title_certification: "Upload certification",
    title_id: "$t(shared.claimsVerifyIdTitle)",
    uploadingMessage: "$t(shared.uploadingMessage)",
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
    uploadingMessage: "$t(shared.uploadingMessage)",
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
  convertToEmployee: {
    alertDescription:
      'Converting your account from "employer" to "employee" is irreversible and will not be possible if your account has been verified.',
    alertHeading: "This action is irreversible!",
    submit: "Convert account",
    title: "Convert to employee account",
  },
  convertToEmployer: {
    alertDescription:
      'Converting your account from "employee" to "employer" is irreversible and will not be possible if any applications have been created, are in-progress, or are completed.',
    alertHeading: "This action is irreversible!",
    einHint:
      "Your Employer Identification Number is a <ein-link>9-digit number</ein-link> assigned by the Internal Revenue Service. It is listed on tax returns and your payroll department should have this information.",
    einLabel: "Employer ID number (EIN)",
    submit: "Convert account",
    title: "Convert to employer account",
  },
  employersAuthCreateAccount: {
    alertHeading:
      "Employees in Massachusetts who wish to apply for paid leave should follow <create-account-link>these instructions</create-account-link>.",
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
      "Welcome! Please take a few minutes to create an account for your organization so you can manage leave for your team. Employees in Massachusetts can now apply for paid family and medical leave.",
    leadMultipleCompanies:
      "If you manage leave for multiple organizations, please create an account for one using the form below. Then you’ll be able to add multiple organizations to your account.",
    nextStep: "We’ll send you a 6-digit code to verify your email address.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    title: "Create an employer account",
    usernameHint:
      "Use a secure work address. An email address can only be associated with one account.",
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
      "<p>Thanks for letting us know that you’re not the right person to review this.</p><ul><li>Please check with your human resources team and your colleagues to see who should respond.</li><li>If the right person at your organization already has an employer account, they received the same email you did and can respond directly.</li><li>Otherwise, please ask them to call us at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</li></ul>",
    instructionsFollowUpDateLabel:
      "<div><strong>Review by:</strong> {{date}} at 11:59 p.m. Eastern time</div>",
    instructions_processingApplication:
      "If we do not hear from anyone at your organization before the deadline, we will process the application solely based on the information the employee provided.",
    title: "Help us find the right person to review the application",
  },
  employersClaimsNewApplication: {
    agreementBody:
      "I understand that I need to give true answers to all questions in order to fulfill my responsibilities as a Massachusetts employer, and that my response may be shared with the employee and third parties. I certify under penalty of perjury that my answers will be complete and accurate.",
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    dobLabel: "Date of birth",
    employeeNameLabel: "Employee name",
    employerIdNumberLabel: "Employer ID number (EIN)",
    instructions:
      "<p>This takes about 10 minutes. We use the information you provide to determine the leave time and benefit amount your employee will receive.</p><p>Your response may be shared with the employee and third parties for purposes of processing and adjudicating this application.</p><p>We need true answers to every question so that we can manage the program the way the law requires. Please confirm that you will answer as truthfully as you can.</p>",
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
    absenceIdLabel: "Application ID: {{absenceId}}",
    instructionsAmendment:
      "Please review the details of this application carefully. If anything is incorrect or incomplete, you can add an amendment or include specific comments at the end. Changes are not saved until you submit your review.",
    instructionsFollowUpDate: "$t(shared.employerInstructions_followUpDate)",
    otherLeavesBody:
      "<p>Please review the leaves and benefits listed in the tables below. If everything looks correct, then there’s no action needed. If something looks incorrect or incomplete, you can:</p><ul><li>Amend reported leaves and benefits.</li><li>Add a leave or benefit that your employee used or will use.</li></ul><p>If you need to remove a leave or benefit, use the comment box at the end of this page.</p>",
    otherLeavesBodyV1:
      "<p>Please review the benefits listed below. If everything looks correct, then there’s no action needed. If something looks incorrect or incomplete, you can amend it. If you need to remove or add a benefit, use the comment box at the end of this page.</p>",
    otherLeavesSummaryBoxBody:
      "<ul><li>Previous leave for a qualifying reason that they took before their paid leave from PFML</li><li>Accrued paid leave they plan to use during their paid leave from PFML</li><li>Employer-sponsored benefits they plan to use during their paid leave from PFML</li></ul>",
    otherLeavesSummaryBoxTitle: "Employees are asked to report:",
    otherLeavesTitle: "Other leaves and benefits",
    previouslyReviewed:
      "This application has changed since it was last reviewed.",
    previouslyReviewed_withDate:
      "This application has changed since it was reviewed on {{date}}.",
    submitButton: "Submit",
    submitLoadingMessage: "Submitting… Do not refresh or go back.",
    title: "Review application from {{name}}",
  },
  employersClaimsStatus: {
    applicationIdLabel: "Application ID",
    lead: "No action is required of you. You can view this page at any time to download notices, see decisions, or access the leave details for this application. Your employee has the right to appeal decisions under Massachusetts regulations (<dfml-regulations-link>458 CMR 2.14</dfml-regulations-link>).",
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
    employeeNameLabel: "<strong>Employee name:</strong> {{employeeName}}",
    instructions_processingApplication:
      "We’ll begin processing this application and your employee should hear from us within 14 calendar days. Once we’ve made a decision, you’ll receive an email with a direct link to details about the decision.",
    instructions_reimbursement:
      "If your organization has a paid disability, family, or medical leave policy for employees, you may qualify for <reimbursements-link>reimbursements for payments made during this leave</reimbursements-link>.",
    reviewedOnLabel: "<strong>Reviewed on:</strong>  {{date}}",
    title: "Thanks for reviewing the application",
  },
  employersDashboard: {
    // Fallback in case some unexpected leave reason is sent from Fineos:
    absencePeriodReason: "Leave period",
    absencePeriodReason_activeDutyFamily:
      "$t(shared.leaveReasonActiveDutyFamily)",
    absencePeriodReason_bonding: "$t(shared.leaveReasonBonding)",
    absencePeriodReason_care: "$t(shared.leaveReasonCare)",
    absencePeriodReason_medical: "$t(shared.leaveReasonMedical)",
    absencePeriodReason_pregnancy: "$t(shared.leaveReasonPregnancy)",
    absencePeriodReason_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    absencePeriodType_Continuous: "$t(shared.claimDurationTypeContinuous)",
    absencePeriodType_Intermittent: "$t(shared.claimDurationTypeIntermittent)",
    "absencePeriodType_Reduced Schedule":
      "$t(shared.claimDurationTypeReducedSchedule)",
    filterNavLabel: "Filters:",
    filterOrgsLabel: "Organizations",
    filterRemove: "Remove filter:",
    filterRequestDecisionLabel: "Leave details",
    filterRequestDecision_all: "Show all",
    filterRequestDecision_approved: "Approved",
    filterRequestDecision_cancelled: "Cancelled",
    filterRequestDecision_denied: "Denied",
    filterRequestDecision_pending: "Pending",
    filterRequestDecision_withdrawn: "Withdrawn",
    filterReviewableLabel: "Review requested",
    filterReviewable_all: "Show all",
    filterReviewable_no: "No, review not needed",
    filterReviewable_yes: "Yes, review requested",
    filterStatusChoice_Approved: "$t(shared.absenceCaseStatus_approved)",
    filterStatusChoice_Closed: "$t(shared.absenceCaseStatus_closed)",
    filterStatusChoice_Declined: "$t(shared.absenceCaseStatus_denied)",
    filterStatusChoice_OpenRequirement: "Review by",
    filterStatusChoice_PendingNoAction: "$t(shared.absenceCaseStatus_noAction)",
    filterStatusLabel: "Status",
    filtersApply: "Apply filters",
    filtersReset: "Reset all filters",
    filtersShowWithCount: "Show filters ({{count}})",
    filtersToggle: "Show filters",
    filtersToggle_expanded: "Hide filters",
    noClaimResults: "No applications on file",
    numAbsencePeriodsHidden: "+ {{hiddenCount}} more",
    respondBy: "Respond by {{ date }}",
    reviewAction: "Review Application",
    searchLabel: "Search for employee name or application ID",
    searchSubmit: "Search",
    sortChoice_employee_az: "Last name – A to Z",
    sortChoice_employee_za: "Last name – Z to A",
    sortChoice_newest: "Newest applications",
    sortChoice_oldest: "Oldest applications",
    sortChoice_status: "Status",
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
    statusDescription_reviewBy:
      "<strong>Review by:</strong> Review this application by this date to provide DFML with your input.",
    statusDescriptionsLabel: "Status descriptions",
    tableColHeading_created_at: "Application start date",
    tableColHeading_employee_and_case: "Employee (Application ID)",
    tableColHeading_employee_name: "Employee name",
    tableColHeading_employer: "Organization (FEIN)",
    tableColHeading_employer_dba: "Organization",
    tableColHeading_employer_fein: "Employer ID number",
    tableColHeading_fineos_absence_id: "Application ID",
    tableColHeading_leave_details: "Leave details",
    tableColHeading_review_status: "Review due date",
    tableColHeading_status: "Status",
    title: "Dashboard",
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
      "Your account has been verified. If anyone else on your team needs to review applications, they’ll also need to complete the <learn-more-link>verification process</learn-more-link>.",
    title: "Thanks for verifying your paid leave contributions",
  },
  employersOrganizationsVerifyContributions: {
    companyNameLabel: "<strong>Organization:</strong> {{company}}",
    detailsLabel: "Where to find your paid leave contributions",
    detailsList:
      "Log in to <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> or contact your payroll department to complete these steps:<ol><li>On the <strong>Summary</strong> page, scroll down to the <strong>Paid Family and Medical Leave</strong> section on the left. In the <strong>Account</strong> portion, select <strong>Returns</strong>.</li><li>Choose <strong>the last period</strong> for which a return has been <strong>received</strong>. For example, if you sent your contributions for 3-31-2021, and the return has been processed and designated as ‘received’, you can use the amount from that period to verify your account. If you have not yet sent your contributions or it is still being processed, use the amount from the most recent period for which you filed that has been processed.</li><li>Go into the return. Click <strong>View or Amend Return</strong>. Then select <strong>Next</strong> at the bottom. Look to <strong>line 6</strong> and you will find the <strong>Total Contributions Due</strong>.</li><li>Copy the <strong>Total Contributions Due</strong> amount for verification.</li></ol>If you have any questions about your paid leave contributions, please contact the Department of Revenue at <dor-phone-link><strong>$t(shared.departmentOfRevenuePhoneNumber)</strong></dor-phone-link> from 9am-4pm ET.",
    employerIdNumberLabel: "<strong>Employer ID number (EIN):</strong> {{ein}}",
    haveAnAccount: "Have an account? <log-in-link>Log in</log-in-link>",
    lead: "We need more information to verify your identity. We require every employer to verify recent <mass-tax-connect-link>MassTaxConnect</mass-tax-connect-link> data when creating an account. This helps protect your employees and your organization's information.",
    submitButton: "Submit",
    title: "Verify your paid leave contributions from MassTaxConnect",
    withholdingAmountHint: "Include the full amount with dollars and cents.",
    withholdingAmountLabel: "Paid leave contributions from {{date}}",
  },
  employersWelcome: {
    checkEmailBody:
      "When an employee applies for leave, you’ll receive email updates about their application status and any steps you need to take. We’ll include everyone who has an employer account with your organization in case you’re out of the office.",
    checkEmailTitle: "Check your email regularly",
    learnMoreLinks:
      "<ul><li><mass-employer-role-link>Your role as a Massachusetts employer</mass-employer-role-link></li><li><reimbursements-link>Request to be reimbursed for paid leave benefits</reimbursements-link></li></ul>",
    learnMoreTitle: "Learn more",
    respondBody:
      "When an application is submitted, you have 10 business days to open the direct link from your email and review it online. You can comment on the application, approve or deny it, and report fraud if needed. Reviewing takes about 10 minutes. If we don’t hear from anyone at your organization before the deadline, we’ll process the application solely based on the information the employee provided.",
    respondTitle: "Respond to applications within 10 business days",
    settingsLink: "Your organizations",
    settingsTitle: "Settings",
    verificationAlertBody:
      "We require every employer to verify paid leave contributions when creating an account. You need to <your-organizations-link>complete this process</your-organizations-link> to review applications from your team.",
    verificationAlertTitle: "Verify your account to continue",
    viewApplicationsBody:
      "When you log in to your account you can now use the <dashboard-link>dashboard</dashboard-link> to see all the applications submitted by employees from your organization.",
    viewApplicationsTitle: "View all applications",
    viewFormsBody:
      "You’ll get an email about our application decision with a direct link to download the letter your employee received. For medical leave, you can download the <healthcare-provider-form-link>$t(shared.certificationFormMedical) form</healthcare-provider-form-link> during the review process. For leave to care for a family member you can download the <caregiver-certification-form-link>Certification to Care for a Family Member</caregiver-certification-form-link> during the review process. ",
    viewFormsTitle: "View forms and notices online",
    welcomeBody:
      "Thanks for joining the paid leave program. Your employees in Massachusetts can apply for Paid Family and Medical Leave. You can review and respond to their applications, and you can see the status of their leave.",
    welcomeTitle: "Welcome",
  },
  getReady: {
    addApplication: "$t(shared.addApplication)",
    alertHeading: "Only some people can apply online for now",
    alertOnline:
      "<p>If you are currently employed in Massachusetts but not self-employed, you can apply online or by phone for the following types of paid leave:</p><ul><li>Medical leave due to your own illness, injury, or pregnancy</li><li>Family leave to bond with your child after birth, adoption, or foster placement — whether you are applying before or after the child arrives</li><li>Family leave to care for a family member with a serious medical condition</li></ul>",
    alertOnlineHeading: "Apply online",
    alertPhone:
      "<p>Apply by calling the Department of Family and Medical Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> if <strong>any</strong> of the following are true:</p><ul><li>You are self-employed or unemployed and you are applying for paid leave</li><li>You need paid family leave to care for a family member who serves in the armed forces</li><li>You need paid family leave to manage family affairs when a family member is on active duty in the armed forces</li></ul>",
    alertPhoneHeading: "Apply by phone",
    applicationsLink: "View all applications",
    convertDescription: "Your account type is now converted.",
    convertHeading: "Success",
    createClaimButton: "Create an application",
    startByPhoneDescription: "$t(shared.startByPhoneDescription)",
    startByPhoneLabel: "$t(shared.startByPhoneLabel)",
    stepOne:
      "<p>If you can, tell your employer at least 30 days before your leave begins. If you need to take leave right away, tell your employer as soon as possible.</p><p>Once you tell your employer, you have the right to apply and your job is protected. Make a note of when you notified your employer. You will need to provide this date in your leave application.</p>",
    stepOneHeading: "1. Tell your employer that you need to take paid leave",
    stepThree:
      "<p>Applying takes around 15 minutes. Your information will save as you go, so you can finish your application later if you need to.</p><p>If you give birth and plan to take both pregnancy-related medical leave and family leave to bond with your newborn, you should apply for medical leave first. Family leave to bond with your child can be <medical-bonding-link>easily added to your application</medical-bonding-link> by calling our Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p><p>You need to create multiple leave applications if you are:</p><ul><li>Taking leave from multiple employers.</li><li>Taking time off in uneven blocks of time (intermittent leave), <strong>and</strong> taking time off completely or on a reduced schedule. You’ll need a separate application for the intermittent leave.</li></ul><p>PFML benefits are subject to reporting for tax purposes and may be subject to taxation. Your decision to have taxes withheld from your benefit may affect your personal tax liability. If you’re unsure whether you want to withhold taxes, we recommend speaking with a <tax-guide-link>tax professional</tax-guide-link>. Learn more about the <tax-liability-link>possible tax implications</tax-liability-link> of paid leave benefits.</p><p>The maximum benefit a person can receive per week is ${{maxBenefitAmount}}. Learn more about <benefits-amount-details-link>how benefits are calculated.</benefits-amount-details-link></p>", // eslint-disable-line no-template-curly-in-string
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
    claimantCardBody:
      "Apply for Paid Family and Medical Leave by creating an employee account.",
    claimantCreateAccountButton: "Create an account to apply",
    claimantHeading: "Employees",
    createAccountHeading: "Choose an account type",
    createAccountHint:
      "You can create an account to apply for leave as an employee or to manage leave an employer.",
    employerCardBody: "Manage leave for your team.",
    employerCreateAccountButton: "Create an employer account",
    employerHeading: "Employers",
    seoTitle:
      "Create or Log in to your account for Massachusetts Paid Family and Medical Leave",
    title:
      "People who work in Massachusetts can now apply for Paid Family and Medical Leave. Learn more about this <mass-paid-leave-link>new paid leave program</mass-paid-leave-link>.",
  },
  payments: {
    backButtonLabel: "$t(shared.backToYourApplicationsLink)",
    changesToPaymentsAmountAnswer:
      "<p>To see your maximum weekly benefit amount, view your approval notice in the <view-notices-link>notice section of your application.</view-notices-link>.</p><p>The payment amount you see on this page may be less than the maximum benefit amount due to <using-other-leave-link>other leave, income and benefits</using-other-leave-link> you reported. You will receive another notice if we reduce your benefit amount for any reason other than tax withholding. Please note that you can not change your tax withholding status at this point, since your application has been approved.</p><p><strong>Other scenarios that may change the payment amount you receive are:</strong></p><ul><li>You or your employer report other leave, income or benefits</li><li>You reach the maximum total amount that you can receive in PFML benefits across multiple applications</li><li>You receive a payment for a pay period less than a full week</li><li>You elected to have taxes withheld</li><li>You received an overpayment</li></ul>",
    changesToPaymentsAmountQuestion:
      "Why the amount you received may be less than your approved benefit amount",
    changesToPaymentsHeading: "Changes to payments",
    changesToPaymentsYourPreferencesAnswer:
      "<p>To make changes to your payment method or banking information, call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    changesToPaymentsYourPreferencesQuestion: "Change your payment preference",
    delaysToPaymentsScheduleAnswer:
      "<strong>What may cause a delayed payment</strong><p>The exact day you receive payment can be delayed because of:</p><ul><li>State and federal holidays</li><li>Pay periods that end on weekends</li><li>Your bank’s processes</li><li>Changes to your leave’s start and end dates</li><li>Changes to your benefit amount due to additional income or benefits you or your employer reported</li><li>Other processing issues such as issues with bank account information or your address</li></ul><p><strong>What may cause a cancelled payment</strong></p><p>Payments can be cancelled because of:</p><ul><li>Paid time off taken on the same day you receive receive PFML benefits</li><li>Changes to your leave’s start and end dates</li><li>Changes to your benefit amount due to additional income or benefits you or your employer reported</li><li>Hours worked outside of the schedule you set up with your employer or during reported intermittent hours</li><li>If you believe we’ve cancelled your payments for an incorrect reason, you can <online-appeals-form>appeal the DFML decision.</online-appeals-form></ul>",
    delaysToPaymentsScheduleQuestion:
      "What may cause a delayed or cancelled payment",
    estimatedDate:
      "This is the date range we expect to process your direct deposit payment or send your check in the mail. Depending on your bank, expect to receive direct deposit payments in your account 2-3 days after this date. Checks may take 7-11 days to arrive in the mail. Once your payment is processed or your check is sent, that date will be shown in the “date processed” column.",
    estimatedDateHeading: "What does the estimated date mean?",
    feedbackDetails:
      "<p>We’d like to hear more about your experience on this site. Please take a few minutes to share your feedback.</p><p><feedback-link>Take the survey</feedback-link></p>",
    feedbackHeader: "Help us improve payment information by giving feedback",
    infoAlertBody_bonding: "$t(shared.infoAlertBody_bonding)",
    infoAlertBody_pregnancy: "$t(shared.infoAlertBody_pregnancy)",
    infoAlertHeading_bonding: "$t(shared.infoAlertHeading_bonding)",
    infoAlertHeading_pregnancy: "$t(shared.infoAlertHeading_pregnancy)",
    loadingClaimDetailLabel: "$t(shared.loadingClaimDetailLabel)",
    paymentsIntro_Continuous_ApprovalPreStartDate:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}} </strong>. Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_Continuous_ApprovalPreStartDate_PostMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong>.</p><p>Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_Continuous_PostFourteenthClaimDate:
      "<p>Check back on {{checkbackDate}} to see when you can expect your first payment. Your first payment will include multiple weeks of leave. After your first payment, expect to be paid weekly.</p>",
    paymentsIntro_Continuous_PostFourteenthClaimDate_PostMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong>. This payment will include multiple weeks of your leave.</p> <p>Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_Continuous_PostFourteenthClaimDate_PreMondayPaymentSchedule:
      "Your first payment will be scheduled on <strong>{{checkbackDate}}</strong> to see when you can expect your first payment. Your first payment will include multiple weeks of leave. After your first payment, expect to be paid weekly.</p>",
    paymentsIntro_Continuous_PreFourteenthClaimDate:
      "<p>Check back on {{checkbackDate}} to see when you can expect your first payment. Your first payment will be scheduled after your second week of leave ends. After your first payment, expect to be paid weekly.</p>",
    paymentsIntro_Continuous_PreFourteenthClaimDate_PreMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong> to see when you can expect your first payment. Your first payment will be scheduled after your second week of leave ends. After your first payment, expect to be paid weekly.</p>",
    paymentsIntro_Continuous_Retroactive:
      "<p>Check back on {{checkbackDate}} to see when you can expect your first payment. You’ll receive one payment for your entire leave.</p>",
    paymentsIntro_Intermittent:
      "Once you report at least 8 hours, you can expect to receive a payment about one week later. You can receive more than one payment in a week depending on how your hours are reported. You can report your hours by calling <contact-center-report-phone-link>$t(shared.contactCenterReportHoursPhoneNumber)</contact-center-report-phone-link>.",
    paymentsIntro_Intermittent_PostMondayPaymentSchedule:
      "Once you report at least 8 hours, you can expect to receive a payment the following Monday, or on Tuesday if Monday is a holiday. You can receive more than one payment in a week depending on how your hours are reported. You can report your hours by calling  <contact-center-report-phone-link>$t(shared.contactCenterReportHoursPhoneNumber)</contact-center-report-phone-link>.",
    paymentsIntro_Intermittent_Unpaid:
      "<p>Your application has an unpaid 7-day waiting period that begins the first day you report taking leave.</p><p>You need to complete your unpaid 7-day waiting period waiting period and report at least 8 hours of leave before you will receive a payment from the Department. You may receive more than one payment per week depending on how your hours are reported.</p><p>Call the Hours Reporting line at <contact-center-report-phone-link>$t(shared.contactCenterReportHoursPhoneNumber)</contact-center-report-phone-link> each week to report the intermittent leave hours you used.</p>",
    paymentsIntro_NonIntermittent_NonRetro:
      "Payments are scheduled to be paid after each week of your leave. Check back weekly to see when your next payment will be scheduled.",
    paymentsIntro_NonIntermittent_NonRetro_PostMondayPaymentSchedule:
      "Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.",
    paymentsIntro_NonIntermittent_Retro:
      "Since you were approved after your leave ended, you’ll receive one payment for your entire leave.",
    paymentsIntro_NonIntermittent_Retro_PreMondayPaymentSchedule:
      "Since your application was approved after your leave ended, you’ll receive one payment for your entire leave.",
    paymentsIntro_ReducedSchedule_ApprovalPreStartDate:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong>.  You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p><p>Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_ReducedSchedule_ApprovalPreStartDate_PostMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong>.  You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p><p>Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_ReducedSchedule_PostFourteenthClaimDate:
      "<p>Check back on {{checkbackDate}} to see when you can expect your first payment. You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p>",
    paymentsIntro_ReducedSchedule_PostFourteenthClaimDate_PostMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong>. This payment will include multiple weeks of your leave. You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p><p>Payments are scheduled to be paid after each week of your leave on Mondays, or on Tuesday if Monday is a holiday.</p>",
    paymentsIntro_ReducedSchedule_PostFourteenthClaimDate_PreMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong> to see when you can expect your first payment. You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p>",
    paymentsIntro_ReducedSchedule_PreFourteenthClaimDate:
      "<p>Check back on {{checkbackDate}} to see when you can expect your first payment. You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p>",
    paymentsIntro_ReducedSchedule_PreFourteenthClaimDate_PreMondayPaymentSchedule:
      "<p>Your first payment will be scheduled on <strong>{{checkbackDate}}</strong> to see when you can expect your first payment. You need to take at least 8 hours of leave or wait until 30 days have passed for a payment to be scheduled.</p>",
    paymentsIntro_ReducedSchedule_Retroactive:
      "$t(pages.payments.paymentsIntro_Continuous_Retroactive)",
    paymentsTitle: "Payments",
    questionsDetails:
      "<p>Call the Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>.</p>",
    questionsHeader: "Questions?",
    tableAmountHeader: "Amount",
    tableAmountSent: "{{amount, currency}}",
    tablePayPeriodHeader: "Pay period",
    tablePaymentStatus_Cancelled:
      "This payment was cancelled. See <delays-accordion-link>what may cause a delayed or cancelled payment</delays-accordion-link>.",
    tablePaymentStatus_Check: "Check mailed on {{sentDate}}",
    tablePaymentStatus_Delayed:
      "See <delays-accordion-link>what may cause a delayed or cancelled payment</delays-accordion-link>.",
    "tablePaymentStatus_Delayed_Address Validation Error":
      "This payment is delayed due to an error with your provided mailing address. Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to resolve this issue.",
    "tablePaymentStatus_Delayed_Bank Processing Error":
      "$t(pages.payments.tablePaymentStatus_Delayed_Banking_Error)",
    tablePaymentStatus_Delayed_Banking_Error:
      "This payment has been rejected by your bank. Call <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link> to resolve this issue.",
    tablePaymentStatus_Delayed_Default:
      "This payment is delayed. See <delays-accordion-link>what may cause a delayed or cancelled payment</delays-accordion-link> for details. Most delays are resolved within 3 to 5 business days. The Contact Center will contact you if they require more information.",
    "tablePaymentStatus_Delayed_EFT Account Information Error":
      "$t(pages.payments.tablePaymentStatus_Delayed_Banking_Error)",
    "tablePaymentStatus_Delayed_Exempt Employer":
      "$t(pages.payments.tablePaymentStatus_Delayed_Default)",
    "tablePaymentStatus_Delayed_InvalidPayment NameMismatch":
      "$t(pages.payments.tablePaymentStatus_Delayed_Default)",
    "tablePaymentStatus_Delayed_Leave Plan In Review":
      "$t(pages.payments.tablePaymentStatus_Delayed_Default)",
    "tablePaymentStatus_Delayed_Max Weekly Benefits Exceeded":
      "$t(pages.payments.tablePaymentStatus_Delayed_Default)",
    tablePaymentStatus_Delayed_Processing:
      "Your payment is being processed. Your {{paymentMethod}} dates will be available in a few days. No action is required from you at this time.",
    tablePaymentStatus_Delayed_ProcessingWithDate:
      "$t(pages.payments.tablePaymentStatus_Pending)",
    tablePaymentStatus_Pending:
      "Your payment will be sent by {{paymentMethod}} between {{payPeriod}}.",
    "tablePaymentStatus_Sent to bank":
      "Direct deposit was sent on {{sentDate}}. Depending on your bank’s processes, expect to see this payment in your account 2-3 days after this date.",
    tableStatusHeader: "Status",
    tableWaitingWeekGeneric:
      "The first seven (7) days of approved leave are unpaid",
    tableWaitingWeekHeader: "Waiting period",
    tableWaitingWeekText:
      "You have an unpaid 7-day waiting period at the start of your leave. You won’t receive any PFML payments for leave you take during this time. Learn more about the <waiting-week-link>7-day waiting period</waiting-week-link>.",
    yourPayments: "Your payments",
  },
  userConsentToDataSharing: {
    agreementBody:
      "By continuing, I am indicating that I have read and understood the above user agreements. I give the Department of Family and Medical Leave permission to collect, share, and use my information consistent with the terms of the agreements linked$t(chars.nbsp)above.",
    applicationUsage: "",
    applicationUsageHeading_employer: "Reviewing paid leave applications",
    applicationUsageHeading_user: "Applying for benefits",
    applicationUsageIntro: "We need this information to:",
    applicationUsageList_employer:
      "<ul><li>Check eligibility for coverage</li><li>Determine your employee’s benefit amount</li><li>Administer the program and meet reporting requirements</li><li>Give you the best service possible</li></ul>",
    applicationUsageList_user:
      "<ul><li>Check your eligibility for coverage</li><li>Determine your benefit amount</li><li>Give you the best service possible</li></ul>",
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
  userSettings: {
    accountInformationHeading: "Account information",
    addPhoneNumberButtonText: "Add additional verification",
    additionalVerificationHeading: "Additional login verification",
    additionalVerificationNoMfaText:
      "<p>Make your account more secure by providing a phone number to associate with your account. We'll send you a 6-digit code to verify it's really you. You’ll need to enter the code in order to log in to your account. In the future, you’ll also be able to access sensitive information like tax documents (when available) once you set this up.</p><p>You will need to provide a phone number that can receive text messages (SMS) and that you’ll have consistent access to in case we need to verify your login.</p><p><strong>Additional login verification is not enabled</strong></p>",
    additionalVerificationWithMfaText:
      "To protect your security, we'll send you a 6-digit code to verify it's really you. You’ll need to enter the code in order to log in to your account.",
    backToApplicationsLinkText: "Back to applications",
    cancelEditLoginVerificationLinkText: "Cancel",
    editLoginVerificationLabel: "Edit login verification preferences",
    emailLabel: "Email address",
    mfaChoiceDisable: "Disable additional login verification",
    mfaChoiceEnable: "Enable additional login verification",
    mfaEnabledLabel: "Additional login verification is enabled",
    mfaPhoneNumberLabel: "Phone number",
    rowEditText: "Edit",
    saveLoginVerificationButtonText: "Save preference",
    title: "Settings",
  },
};

const components: {
  // Keys are limited to three levels deep, for example `components.spinner.label`.
  // This makes the structure easier to navigate and the process of finding a specific element more consistent
  [componentKey: string]: I18nContentGroup;
} = {
  absenceCaseStatusTag: {
    status_approved: "$t(shared.absenceCaseStatus_approved)",
    status_closed: "$t(shared.absenceCaseStatus_closed)",
    status_completed: "$t(shared.absenceCaseStatus_closed)",
    status_declined: "$t(shared.absenceCaseStatus_denied)",
    status_noAction: "$t(shared.absenceCaseStatus_noAction)",
    status_openRequirements: "Review by {{followupDate}}",
    status_pending: "$t(shared.absenceCaseStatus_pending)",
  },
  absencePeriodStatusTag: {
    label_approved: "Approved",
    label_cancelled: "Cancelled",
    label_denied: "Denied",
    label_inReview: "Pending",
    label_pending: "Pending",
    label_projected: "Pending",
    label_voided: "Cancelled",
    label_withdrawn: "Withdrawn",
  },
  amendButton: {
    amend: "Amend",
  },
  amendmentForm: {
    cancel: "Cancel amendment",
  },
  applicationCard: {
    applicationID: "Application ID",
    claimAssociatedSuccessfully:
      "Application {{fineos_absence_id}} has been added to your account.",
    continueApplication: "Continue application",
    earliestSubmissionDateInFuture:
      "You will be able to submit this application on <strong>{{earliest_submission_date}}</strong>. This is 60 days before the start of your leave. Applications cannot be submitted earlier than 60 days before the start of leave.",
    employerEIN: "Employer Identification Number (EIN)",
    heading_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    heading_bonding: "$t(shared.leaveReasonBondingHeader)",
    heading_care: "$t(shared.leaveReasonCareHeader)",
    heading_medical: "$t(shared.leaveReasonMedicalIllness)",
    heading_noReason: "In-progress application",
    heading_pregnancy: "$t(shared.leaveReasonPregnancyHeader)",
    heading_serviceMemberFamily: "$t(shared.leaveReasonServiceMemberFamily)",
    inProgressText:
      "Submit all three parts so that we can review your application.",
    leaveDates: "{{start}} to {{end}}",
    leaveDatesLabel: "Leave Dates",
    leavePeriodLabel_reduced: "$t(shared.claimDurationTypeReducedSchedule)",
    loadingLabel: "$t(shared.loadingDocumentsLabel)",
    noticeOnClickDetails:
      "When you click the notice link, the file will download to your device.",
    otherActions: "Other actions",
    respondToRequest: "Respond to a request for information",
    viewNotices: "View your notices",
    viewStatusUpdatesAndDetails: "View status updates and details",
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
      "<ul><li>The text must be clear and readable</li><li>Upload every page of the document where you or your health care provider have entered information</li><li>Each file you upload must be smaller than 4.5 MB</li></ul>",
    body_id:
      "<ul><li>The image of the card must be in full color</li><li>The text must be clear and readable</li><li>The front and back can be in one file, or in two separate files</li><li>Each file must be smaller than 4.5 MB</li></ul>",
    header: "Document Requirements:",
  },
  downloadableDocument: {
    createdAtDate: "Posted {{date}}.",
    noticeName: "Other notice $t(shared.pdfNoticeSuffix)", // it should fallback to this if we receive an unexpected or undefined enum
    noticeName_appealAcknowledgment:
      "Appeal Acknowledgment $t(shared.pdfNoticeSuffix)",
    noticeName_approvalNotice: "Approval notice $t(shared.pdfNoticeSuffix)",
    noticeName_approvedTimeCancelled:
      "Approved Time Cancelled $t(shared.pdfNoticeSuffix)",
    noticeName_benefitAmountChangeNotice:
      "Benefit Amount Change Notice $t(shared.pdfNoticeSuffix)",
    noticeName_changeRequestApproved:
      "Change Request Approved $t(shared.pdfNoticeSuffix)",
    noticeName_changeRequestDenied:
      "Change Request Denied $t(shared.pdfNoticeSuffix)",
    noticeName_denialNotice: "Denial notice $t(shared.pdfNoticeSuffix)",
    noticeName_leaveAllotmentChangeNotice:
      "Leave Allotment Change Notice $t(shared.pdfNoticeSuffix)",
    noticeName_maximumWeeklyBenefitChangeNotice:
      "Maximum Weekly Benefit Change Notice $t(shared.pdfNoticeSuffix)",
    noticeName_requestForInfoNotice:
      "Request for more information $t(shared.pdfNoticeSuffix)",
    noticeName_withdrawalNotice:
      "Pending Application Withdrawn $t(shared.pdfNoticeSuffix)",
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
  employersCaringLeaveQuestion: {
    choiceNo: "No (comment required)",
    choiceUnknown: "I don't know",
    choiceYes: "Yes",
    commentHeading: "Tell us why you think this relationship is inaccurate.",
    familyMemberRelationshipHint:
      "This employee has attested the family member relationship is <eligible-relationship-link>a covered relationship</eligible-relationship-link>. If something on the form seems incorrect, add a comment at the end of the page.",
    familyMemberRelationshipLabel:
      "Do you believe the listed relationship is described accurately? (Optional)",
    inaccurateRelationshipAlertHeading:
      "The employee will be denied paid leave.",
    inaccurateRelationshipAlertLead:
      "We take allegations about false relationships seriously. Choosing No may trigger a denial of the employee's application for paid leave. The employee has the right to appeal if their application is denied.",
    unknownRelationshipAlertLead:
      "If you have not confirmed the accuracy of the family relationship the employee has attested to, please note that the Department of Family and Medical leave will adjudicate based on the attestation the employee made when submitting their application.",
  },
  employersCertsAndPeriods: {
    caringLeaveDocumentInstructions: "View the family relationship on page 3.",
    documentName: "Your employee's certification document.",
    documentationLabel: "Documentation",
    header: "Leave details",
    leaveDurationLabel: "Leave duration",
    // Fallback in case some unexpected leave reason is sent from Fineos:
    reasonHeading: "Leave periods",
    reasonHeading_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    reasonHeading_bonding: "$t(shared.leaveReasonBonding)",
    reasonHeading_care: "$t(shared.leaveReasonCare)",
    reasonHeading_medical: "$t(shared.leaveReasonMedical)",
    reasonHeading_pregnancy: "$t(shared.leaveReasonPregnancy)",
    reasonHeading_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    recordkeepingInstructions:
      "To meet <mass-employer-role-link>federal laws and regulations</mass-employer-role-link>, you must keep medical records separate and confidential from any personnel files.",
  },
  employersConcurrentLeave: {
    addButton: "Add an accrued paid leave",
    dateRangeLabel: "Date range",
    explanation:
      "Your employee has told us about the following accrued paid leave they plan to use concurrent with their paid leave from PFML. This includes paid vacation time, sick time, personal time, and other paid time off. It does not include a family or medical leave policy or a disability program.",
    explanationDetails_continuousOrReduced:
      "Your employee won’t receive PFML payments for the first 7 calendar days of their PFML leave from {{startDate}} to {{endDate}}. During those 7 days they may use accrued paid leave, and you and your employee <strong>shouldn’t</strong> report it.",
    explanationDetails_intermittent:
      "Your employee won’t receive PFML payments for the first 7 calendar days from the date of their first instance of leave. During those 7 days they may use accrued paid leave, and you and your employee <strong>shouldn’t</strong> report it.",
    header: "Concurrent accrued paid leave",
  },
  employersEmployeeInformation: {
    addressLabel: "Mailing address",
    dobLabel: "Date of birth",
    employeeNameLabel: "Employee name",
    employerIdentifierLabel: "Employer ID number (EIN)",
    header: "Employee information",
    organizationNameLabel: "Organization",
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
    benefitTypeLabel: "Benefit type",
    caption_v1:
      "Your employee is planning to use these benefits. Employer sponsored benefits include temporary disability insurance, permanent disability insurance, paid time off (PTO) or accrued paid leave, and family or medical leave benefits such as a parental leave program. <reductions-overview-link>Learn more about how these affect payments.</reductions-overview-link>",
    caption_v2:
      "Your employee is planning to use these benefits during their paid leave under PFML. Employer-sponsored benefits include temporary disability insurance, permanent disability insurance, and family or medical leave benefits such as a parental leave program. For paid time off (PTO) and other accrued paid leave your employee will use, review “Concurrent accrued paid leave” above. <reductions-overview-link>Learn more about how these affect payments.</reductions-overview-link>",
    dateRangeLabel: "Date range",
    header: "Employer-sponsored benefits",
    tableName: "Employer-sponsored benefit details",
  },
  employersEmployerDecision: {
    choiceApprove: "Approve",
    choiceDeny: "Deny (explain below)",
    explanation:
      "Answer based on your organization's policies and our <mass-employer-role-link>guidelines for employers</mass-employer-role-link>. Your recommendation is helpful to the Department in making its determination.",
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
  employersNavigationTabs: {
    dashboard: "Dashboard",
    label: "Employer menu",
    welcome: "Welcome",
  },
  employersPaginationAbsencePeriodsTable: {
    claimDurationType_Continuous: "$t(shared.claimDurationTypeContinuous)",
    claimDurationType_Intermittent: "$t(shared.claimDurationTypeIntermittent)",
    "claimDurationType_Reduced Schedule":
      "$t(shared.claimDurationTypeReducedSchedule)",
    dateRangeLabel: "Date range",
    leaveFrequencyLabel: "Leave frequency",
    statusLabel: "Status",
  },
  employersPreviousLeaves: {
    addButton: "$t(shared.claimsPreviousLeaveDetails.addButton)",
    dateRangeLabel: "Date range",
    explanation:
      "<p>Verify the accuracy of your employee’s qualified leave dates. Any qualifying reason should only be reported if it was taken after {{other_reason_date}}.</p><p>This includes both paid leave (for example: paid vacation or sick days) and unpaid leave (for example: FMLA leave).</p>",
    explanation_differentDates:
      "<p>Verify the accuracy of your employee’s qualified leave dates. Leave to care for a family member should only be reported if it was taken after {{same_reason_date}}. Any other qualifying reason should only be reported if it was taken after {{other_reason_date}}. </p><p>This includes both paid leave (for example: paid vacation or sick days) and unpaid leave (for example: FMLA leave).</p>",
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
  employersWeeklyHoursWorkedRow: {
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
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at <contact-center-phone-link>$t(shared.contactCenterPhoneNumberNoBreak)</contact-center-phone-link>",
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
    attachmentHeading: "If your document is attached to an email:",
    attachmentList:
      "<ul><li>Open the file on your computer or phone</li><li>Save it as a PDF or image, and try uploading again</li></ul>",
    conversionHeading:
      "If your file is not in one of these formats, try one of the following:",
    conversionList:
      "<ul><li>Take a picture of the document</li><li>Take a screenshot of the document</li><li>Save the document as a PDF or image, and try uploading again</li></ul>",
    fileTypesHeading: "This website only accepts:",
    fileTypesList:
      "<ul><li>PDF documents</li><li>Images (.jpg, .jpeg, .png)</li></ul>",
    label: "Tips for uploading images or PDFs",
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
    continueButton: "$t(shared.saveAndContinue)",
    dateInputDayLabel: "Day",
    dateInputExample: "MM / DD / YYYY",
    dateInputMonthLabel: "Month",
    dateInputYearLabel: "Year",
    optional: "(optional)",
  },
  header: {
    appTitle: "Paid Family and Medical Leave",
    settingsLinkText: "Settings",
    skipToContent: "Skip to main content",
  },
  holidayAlert: {
    alertText:
      "Due to the upcoming holiday, payments may be delayed by one business day.",
  },
  inputPassword: {
    toggleLabel: "Show password",
  },
  leaveDatesAlert: {
    heading: "Your leave dates for paid leave from PFML",
    leaveDatesHeading: "Your 7-day waiting period dates",
  },
  maintenanceAlertBar: {
    message_withEndTime:
      "We will be performing some maintenance on our system from <strong>{{start}}</strong> to <strong>{{end}}</strong>.",
    message:
      "We will be performing some maintenance on our system starting <strong>{{start}}</strong>.",
  },
  maintenanceTakeover: {
    noSchedule:
      "We’re performing some maintenance on our system and some features may currently be unavailable. Please check back in a few hours.",
    scheduledWithEndAndNoStart:
      "We're performing some maintenance on our system, so you can't log in or work on any applications right now. The system will be back online and available on <strong>{{end}}</strong>.",
    scheduledWithStartAndEnd:
      "We're performing some maintenance on our system, so you can't log in or work on any applications right now. The system will be offline from <strong>{{start}}</strong> to <strong>{{end}}</strong>.",
    title: "We’re undergoing maintenance",
  },
  mfaSetupSuccessAlert: {
    heading: "Phone number confirmed",
    message:
      "To protect your security, we'll send you a 6-digit code when you log in to verify it's really you.",
  },
  pageNotFound: {
    body: "<p>The page you’re looking for might have been removed, have a new name, or is otherwise unavailable.</p><p>If you typed the URL directly, check your spelling and capitalization. Our URLs look like this: <url-example>{{ url }}</url-example></p>",
    homepageButton: "Visit homepage",
    title: "Page not found",
  },
  pagination: {
    nextLabel: "Next",
    previousLabel: "Previous",
    summary:
      "Viewing {{firstRecordNumber}} to {{lastRecordNumber}} of {{totalRecords}} results",
    summary_empty: "0 results",
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
  statusNavigationTabs: {
    payments: "Payments",
    statusDetails: "Application",
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
  withClaimDocuments: {
    loadingLabel: "$t(shared.loadingDocumentsLabel)",
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
