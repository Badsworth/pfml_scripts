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
  currentUser: {
    failedToFind:
      "Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  },
  invalidFileType:
    "Only PDF and image files may be uploaded. See the tips below for suggestions on how to convert them to an image file. These files that you selected will not be uploaded: {{disallowedFileNames}}",
  network:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
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
  claimsFileUploadTitle: "Verify your identity",
  claimsLeaveDetailsTitle: "Leave Details",
  claimsLeaveDurationTitle: "Leave duration",
  claimsOtherLeaveTitle: "Other income and benefits",
  claimsTakingLeaveTitle: "Verify your identity",
  leaveReasonActiveDutyFamily: "Active duty",
  leaveReasonBonding: "Bonding leave",
  leaveReasonMedical: "Medical leave",
  leaveReasonServiceMemberFamily: "Military family",
  multipleEmployerAppAlert:
    "You need to complete a separate application for each employer you are taking leave from.",
  networkError:
    "Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
  passwordHint:
    "Your password must be at least 8 characters long and include numbers and letters.",
  passwordLabel: "Password",
  pregnancyOrRecentBirthLabel:
    "Are you pregnant or have you recently given birth?",
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
    createAccountLink: "Or create an account",
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
  claimsChecklist: {
    backButtonLabel: "Back to Dashboard",
    completedText: "Completed",
    editText: "Edit",
    resumeText: "Resume",
    screenReaderNumberPrefix: "Step",
    startText: "Start",
    stepHTMLDescription_employerInformation:
      "We’ll ask you for:<ul class='usa-list'><li>The date you told your employer you were taking leave.</li></ul>",
    stepHTMLDescription_leaveDetails:
      "You will need:<ul class='usa-list'><li>A completed Healthcare Provider Form if you are taking medical leave because you can’t work due to an injury, illness, or pregnancy.</li></ul>",
    stepHTMLDescription_otherLeave:
      "We’ll ask you for:<ul class='usa-list'><li>Time off for qualifying condition since January 1, 2021.</li><li>If you have or will receive Unemployment Insurance or Worker’s Compensation.</li><li>If you have or will file under the Family and Medical Leave Act (FMLA).</li></ul>",
    stepHTMLDescription_payment:
      "You will need:<ul class='usa-list'><li>Your bank account information, if you want to be paid through Direct Deposit.</li></ul>",
    stepHTMLDescription_verifyId:
      "You will need:<ul class='usa-list'><li>Proof of your identity, like a driver’s license. See the full list of accepted identity documents.</li><li>Your Social Security Number or Individual Taxpayer Identification Number.</li><ul>",
    stepListTitle: "Create a new application",
    stepTitle_employerInformation: "Enter employment information",
    stepTitle_leaveDetails: "Enter leave details",
    stepTitle_otherLeave: "Report other leave and benefits",
    stepTitle_payment: "Add payment information",
    stepTitle_verifyId: "Verify your identity",
    submitButtonText: "Review and submit application",
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
    title: "$t(shared.claimsTakingLeaveTitle)",
  },
  claimsDuration: {
    avgWeeklyHoursWorkedHint:
      "Tell us how many hours you typically worked before going on leave. We need to know this so we can calculate your benefit amount.",
    avgWeeklyHoursWorkedLabel:
      "How many hours do you work in a week, on average?",
    continuousHint: "$t(shared.claimDurationTypeContinuous)",
    continuousLabel: "Take off work completely",
    hoursOffNeededHint:
      "This can be an approximate. You can change this after your claim is approved.",
    hoursOffNeededLabel: "How many hours do you need to take off each week?",
    intermittentHint: "$t(shared.claimDurationTypeIntermittent)",
    intermittentLabel: "Work on a reduced schedule",
    sectionLabel:
      "Do you need to take off work completely or work on a reduced schedule?",
    title: "$t(shared.claimsLeaveDurationTitle)",
  },
  claimsEmployerBenefitDetails: {
    addButton: "Add another",
    amountHint: "For example, $250 every month",
    amountLabel: "How much will you receive?",
    cardHeadingPrefix: "Benefit",
    choiceHint_familyOrMedicalLeave:
      "For example, a paid maternity leave policy",
    choiceHint_paidLeave:
      "For example, vacation time, sick leave, or personal time",
    choiceHint_permanentDisability:
      "Also known as a permanent disability policy",
    choiceHint_shortTermDisability:
      "Also known as temporary disability insurance",
    choiceLabel_familyOrMedicalLeave: "Family or medical leave insurance",
    choiceLabel_paidLeave: "Accrued paid Leave",
    choiceLabel_permanentDisability: "Permanent disability insurance",
    choiceLabel_shortTermDisability: "Short-term disability insurance",
    endDateLabel: "When will you stop using the benefit?",
    removeButton: "Remove",
    sectionLabel: "Tell us about benefits you will receive from your employer.",
    startDateLabel: "When will you start using the benefit?",
    title: "$t(shared.claimsOtherLeaveTitle)",
    typeLabel: "What kind of benefit is it?",
  },
  claimsEmployerBenefits: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    detailsHeader: "Employer-sponsored benefits you must report are:",
    detailsList: [
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
    furloughAnswer:
      'If your hours have been cut or significantly reduced but you have not been laid off, select "$t(pages.claimsEmploymentStatus.choiceLabel_employed)"',
    furloughQuestion: "What if I've been furloughed?",
    multipleEmployerAppAlert: "$t(shared.multipleEmployerAppAlert)",
    sectionLabel: "What is your employment status?",
    title: "Employment information",
  },
  claimsLeaveDates: {
    endDateLabel: "When do you expect your leave will end?",
    startDateHint: "Your leave begins the day you stopped working.",
    startDateLabel: "When do you expect your leave to begin?",
    title: "$t(shared.claimsLeaveDurationTitle)",
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
    title: "$t(shared.claimsTakingLeaveTitle)",
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
  claimsReasonPregnancy: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    pregnancyOrRecentBirthLabel: "$t(shared.pregnancyOrRecentBirthLabel)",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsReview: {
    confirmationAction: "Confirm information is correct",
    editLink: "Edit",
    employerNotifiedLabel: "Notified employer",
    employerNotifiedValue: "No",
    employerNotifiedValue_true: "Notified employer on {{date}}",
    employmentSectionHeading: "Employment information",
    employmentStatusLabel: "Employment status",
    employmentStatusValue_employed: "Currently employed",
    employmentStatusValue_selfEmployed: "Self-employed",
    employmentStatusValue_unemployed: "Unemployed",
    leaveDurationLabel: "Leave duration",
    leaveDurationTypeLabel: "Leave duration type",
    leaveDurationTypeValue_continuous: "$t(shared.claimDurationTypeContinuous)",
    leaveDurationTypeValue_intermittent:
      "$t(shared.claimDurationTypeIntermittent)",
    leaveReasonLabel: "Leave type",
    leaveReasonValue_activeDutyFamily: "$t(shared.leaveReasonActiveDutyFamily)",
    leaveReasonValue_bonding: "$t(shared.leaveReasonBonding)",
    leaveReasonValue_medical: "$t(shared.leaveReasonMedical)",
    leaveReasonValue_serviceMemberFamily:
      "$t(shared.leaveReasonServiceMemberFamily)",
    leaveSectionHeading: "$t(shared.claimsLeaveDetailsTitle)",
    pregnancyChoiceNo: "$t(shared.choiceNo)",
    pregnancyChoiceYes: "$t(shared.choiceYes)",
    pregnancyOrRecentBirthLabel: "$t(shared.pregnancyOrRecentBirthLabel)",
    title: "Check your answers before sending your application",
    userDateOfBirthLabel: "Date of birth",
    userNameLabel: "Full name",
    userSectionHeading: "Verify your identity",
    userSsnLabel: "Social security number",
    userStateIdLabel: "Massachusetts driver's license or ID",
  },
  claimsSsn: {
    lead:
      "Don't have an SSN? Use your Individual Taxpayer Identification Number (ITIN).",
    sectionLabel: "What's your Social Security Number?",
    title: "$t(shared.claimsTakingLeaveTitle)",
  },
  claimsStateId: {
    choiceNo: "$t(shared.choiceNo)",
    choiceYes: "$t(shared.choiceYes)",
    hasStateIdLabel: "Do you have a Massachusetts driver's license or ID card?",
    idLabel: "Enter your license or ID number",
    title: "$t(shared.claimsTakingLeaveTitle)",
  },
  claimsSuccess: {
    body:
      "We are reviewing your application. You can check the status of your application anytime in the portal.",
    dashboardLink: "Return to dashboard",
    title: "Your leave application was submitted successfully",
  },
  claimsUploadHealthcareForm: {
    addAnotherFileButtonText: "Choose another file",
    addFirstFileButtonText: "Choose a file",
    fileHeadingPrefix: "File",
    lead:
      "You need to upload a copy of the PFML Healthcare Provider Form to prove that you need to take medical leave. You can upload a completed Family and Medical Leave Act (FMLA) form instead if your provider filled out.",
    sectionLabel: "Upload your Healthcare Provider form",
    title: "$t(shared.claimsLeaveDetailsTitle)",
  },
  claimsUploadOtherId: {
    addAnotherFileButtonText: "Choose another file",
    addFirstFileButtonText: "Choose a file",
    // @todo: CP-496 update this with the real documents users can use to ID proof
    documentList: ["Document 1", "Document 2, or", "Document 3"],
    fileHeadingPrefix: "File",
    lead: "Upload one of the following:",
    sectionLabel: "Upload an identification document",
    title: "$t(shared.claimsFileUploadTitle)",
  },
  claimsUploadStateId: {
    addAnotherFileButtonText: "Choose another file",
    addFirstFileButtonText: "Choose a file",
    fileHeadingPrefix: "File",
    lead:
      "In order to verify your identity, upload a copy of both the front and the back of your ID card.",
    sectionLabel: "Upload your Massachusetts driver’s license or ID card",
    title: "$t(shared.claimsFileUploadTitle)",
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
    createClaimButtonText: "Create an application",
    needForApplyingHeading: "What you need to apply",
    needForApplyingList: [
      "Proof of your identity, like a driver’s license.",
      "Your Social Security Number or Individual Taxpayer Identification Number.",
      "Why you are taking leave",
      "Your Healthcare Provider Form, which your healthcare provider has completed",
      "Your employer FEIN",
      "When you are planning to take leave or when you started on leave",
      "Your bank account information",
    ],
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
      "To find out more about how the Commonwealth might use the information you share with DFML, please read the DFML Informed Consent Agreement and the <a href='https://www.mass.gov/privacypolicy'>Privacy Policy for Mass.gov</a>.",
    fullUserAgreementHeading: "Full user agreements",
    intro:
      "The information you provide on this website will be used to administer the Department of Family and Medical Leave (DFML) program.",
    title: "How this website uses your information",
  },
};

const components = {
  amplifyForgotPassword: {
    // TODO: Remove these after the CustomForgotPassword component is obsolete
    // https://lwd.atlassian.net/browse/CP-485
    codeLabel: "$t(shared.verificationCodeLabel)",
    leadCreatePasswordView:
      "If an account exists for {{emailAddress}}, we emailed a 6-digit verification code to it. Enter the code below to confirm your email and reset your password.",
    leadSendView:
      "If an account exists for the email you provide, we will email a 6-digit verification code to it.",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "New password",
    resendCodeLink: "$t(shared.resendVerificationCodeLink)",
    signInFooterLink: "$t(shared.backToLoginLink)",
    submitEmailButton: "Send code",
    submitPasswordButton: "Set new password",
    titleCreatePasswordView: "Create a new password",
    titleSendView: "Forgot your password?",
  },
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
  errorBoundary: {
    message:
      "Sorry, we encountered an unexpected error. If this continues to happen, you may call the Paid Family Leave Contact Center at $t(shared.callCenterPhoneNumber)",
    reloadButton: "Reload this page",
  },
  errorsSummary: {
    genericHeading: "An error was encountered",
    genericHeading_plural: "{{count}} errors were encountered",
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
  signUp: {
    createAccountButton: "Create account",
    haveAnAccountFooterLabel: "Have an account?",
    passwordHint: "$t(shared.passwordHint)",
    passwordLabel: "$t(shared.passwordLabel)",
    signInFooterLink: "Log in",
    title: "Create an account",
    usernameLabel: "$t(shared.usernameLabel)",
  },
  spinner: {
    label: "Loading",
  },
};

const englishLocale = {
  translation: Object.assign({}, { components, errors, pages, shared }),
};

export default englishLocale;
