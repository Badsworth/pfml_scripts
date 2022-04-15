/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the application flow.
 *
 * This configuration is used to determine and group pages by
 * its step in the application process. The data provided in `meta`
 * is used to determine which step a page belongs to and whether that step
 * is complete, in progress, or not started
 * @see ../models/Step
 */

import BenefitsApplication, {
  EmploymentStatus,
  WorkPatternType,
} from "../models/BenefitsApplication";

import ChangeRequest from "../models/ChangeRequest";
import ClaimDetail from "src/models/ClaimDetail";
import { ClaimSteps } from "../models/Step";
import { UploadType } from "../pages/applications/upload/index";
import { fields as addressFields } from "../pages/applications/address";
import { fields as concurrentLeavesDetailsFields } from "../pages/applications/concurrent-leaves-details";
import { fields as concurrentLeavesFields } from "../pages/applications/concurrent-leaves";
import { fields as dateOfBirthFields } from "../pages/applications/date-of-birth";
import { fields as dateOfChildFields } from "../pages/applications/date-of-child";
import { fields as departmentFields } from "../pages/applications/department";
import { fields as employerBenefitsDetailsFields } from "../pages/applications/employer-benefits-details";
import { fields as employerBenefitsFields } from "../pages/applications/employer-benefits";
import { fields as employmentStatusFields } from "../pages/applications/employment-status";
import { fields as familyMemberDateOfBirthFields } from "../pages/applications/family-member-date-of-birth";
import { fields as familyMemberNameFields } from "../pages/applications/family-member-name";
import { fields as familyMemberRelationshipFields } from "../pages/applications/family-member-relationship";
import { fields as genderFields } from "../pages/applications/gender";
import { get } from "lodash";
import { fields as intermittentFrequencyFields } from "../pages/applications/intermittent-frequency";
import isBlank from "src/utils/isBlank";
import { isFeatureEnabled } from "../services/featureFlags";
import { fields as leavePeriodContinuousFields } from "../pages/applications/leave-period-continuous";
import { fields as leavePeriodIntermittentFields } from "../pages/applications/leave-period-intermittent";
import { fields as leavePeriodReducedScheduleFields } from "../pages/applications/leave-period-reduced-schedule";
import { fields as leaveReasonFields } from "../pages/applications/leave-reason";
import { fields as nameFields } from "../pages/applications/name";
import { fields as notifiedEmployerFields } from "../pages/applications/notified-employer";
import { fields as otherIncomesDetailsFields } from "../pages/applications/other-incomes-details";
import { fields as otherIncomesFields } from "../pages/applications/other-incomes";
import { fields as paymentMethodFields } from "../pages/applications/payment-method";
import { fields as phoneNumberFields } from "../pages/applications/phone-number";
import { fields as previousLeavesOtherReasonDetailsFields } from "../pages/applications/previous-leaves-other-reason-details";
import { fields as previousLeavesOtherReasonFields } from "../pages/applications/previous-leaves-other-reason";
import { fields as previousLeavesSameReasonDetailsFields } from "../pages/applications/previous-leaves-same-reason-details";
import { fields as previousLeavesSameReasonFields } from "../pages/applications/previous-leaves-same-reason";
import { fields as reasonPregnancyFields } from "../pages/applications/reason-pregnancy";
import { fields as reducedLeaveScheduleFields } from "../pages/applications/reduced-leave-schedule";
import routes from "../routes";
import { fields as scheduleFixedFields } from "../pages/applications/schedule-fixed";
import { fields as scheduleVariableFields } from "../pages/applications/schedule-variable";
import { fields as ssnFields } from "../pages/applications/ssn";
import { fields as stateIdFields } from "../pages/applications/state-id";
import { fields as taxWithholdingFields } from "../pages/applications/tax-withholding";
import { fields as workPatternTypeFields } from "../pages/applications/work-pattern-type";

export interface ClaimantFlowContext {
  claim?: BenefitsApplication;
  isAdditionalDoc?: boolean;
  changeRequest?: ChangeRequest;
  claimDetail?: ClaimDetail;
}

interface CondMeta {
  cond: { guardKeys: string[] };
}

export type ClaimFlowGuardFn = (
  context: ClaimantFlowContext,
  event: { type: string },
  condMeta: CondMeta
) => boolean;

/**
 *
 * @see https://xstate.js.org/docs/guides/guards.html#custom-guards
 * @see https://github.com/statelyai/xstate/issues/414#issuecomment-480664208
 * Custom guard that requires multiple guards to be true
 */
const every = (...guardKeys: string[]) => ({
  type: "every",
  guardKeys,
});

/**
 * @see https://xstate.js.org/docs/guides/guards.html
 */
export const guards: { [guardName: string]: ClaimFlowGuardFn } = {
  // claimants upload additional docs after the claim is completed.
  // claimants will either be routed to the status page vs. the checklist
  // if they are uploading an additional doc.
  isAdditionalDoc: ({ isAdditionalDoc }) => isAdditionalDoc === true,
  isCaringLeave: ({ claim, claimDetail }) =>
    claim?.isCaringLeave === true || claimDetail?.isCaringLeave === true,
  isNonPregnancyMedicalLeave: ({ claimDetail }) =>
    claimDetail?.isNonPregnancyMedicalLeave === true,
  isPregnancyLeave: ({ claimDetail }) => claimDetail?.isPregnancyLeave === true,
  isMedicalOrPregnancyLeave: ({ claim }) =>
    claim?.isMedicalOrPregnancyLeave === true,
  isBondingLeave: ({ claim }) => claim?.isBondingLeave === true,
  // TODO (PFMLPB-3195): Remove isFeatureEnabled check once feature flag is obsolete
  hasEmployerWithDepartments: ({ claim }) =>
    get(claim, "employment_status") === EmploymentStatus.employed &&
    get(claim, "employer_organization_units", []).length > 0,
  isEmployed: ({ claim }) =>
    get(claim, "employment_status") === EmploymentStatus.employed,
  isCompleted: ({ claim }) => claim?.isCompleted === true,
  hasStateId: ({ claim }) => claim?.has_state_id === true,
  hasConcurrentLeave: ({ claim }) => claim?.has_concurrent_leave === true,
  hasEmployerBenefits: ({ claim }) => claim?.has_employer_benefits === true,
  hasIntermittentLeavePeriods: ({ claim }) =>
    claim?.has_intermittent_leave_periods === true,
  hasPreviousLeavesOtherReason: ({ claim }) =>
    claim?.has_previous_leaves_other_reason === true,
  hasPreviousLeavesSameReason: ({ claim }) =>
    claim?.has_previous_leaves_same_reason === true,
  hasReducedScheduleLeavePeriods: ({ claim }) =>
    claim?.has_reduced_schedule_leave_periods === true,
  hasOtherIncomes: ({ claim }) => claim?.has_other_incomes === true,
  isFixedWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.fixed,
  isVariableWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.variable,
  doLeaveDatesCrossBenefitYears: ({ claim }) =>
    isFeatureEnabled("splitClaimsAcrossBY") &&
    claim !== undefined &&
    claim.computed_application_split !== null,
  isSubmittedApplicationSplit: ({ claim }) =>
    !isBlank(claim?.split_into_application_id),
  isExtendingModification: ({ changeRequest, claimDetail }) =>
    changeRequest?.isExtension(claimDetail?.endDate || "") === true,
  every: (ctx, event, condMeta) => {
    const {
      cond: { guardKeys },
    } = condMeta;
    return guardKeys.every((key) => guards[key](ctx, event, condMeta));
  },
};

/**
 * Events shared by checklist and review
 */
const checklistEvents = {
  VERIFY_ID: routes.applications.name,
  LEAVE_DETAILS: routes.applications.leaveReason,
  OTHER_LEAVE: routes.applications.previousLeavesIntro,
  EMPLOYER_INFORMATION: routes.applications.employmentStatus,
  PAYMENT: routes.applications.paymentMethod,
  TAX_WITHHOLDING: routes.applications.taxWithholding,
  UPLOAD_CERTIFICATION: routes.applications.uploadCertification,
  UPLOAD_ID: routes.applications.uploadId,
};

/**
 * Events shared by all upload docs pages
 */
const uploadDocEvents = {
  CONTINUE: [
    {
      target: routes.applications.status.claim,
      cond: "isAdditionalDoc",
    },
    {
      target: routes.applications.checklist,
    },
  ],
};

interface ConditionalEvent {
  target: string;
  cond?: string | { type: string; guardKeys: string[] };
}

export interface ClaimantFlowState {
  meta?: {
    applicableRules?: string[];
    fields?: string[];
    step?: string;
  };
  on: { [event: string]: string | ConditionalEvent[] };
}

const claimantFlow: {
  states: { [route: string]: ClaimantFlowState };
} = {
  states: {
    [routes.applications.getReady]: {
      meta: {},
      on: {
        IMPORT_APPLICATION: routes.applications.importClaim,
        START_APPLICATION: routes.applications.start,
        SHOW_APPLICATIONS: routes.applications.index,
      },
    },
    [routes.applications.start]: {
      meta: {},
      on: {
        CREATE_CLAIM: routes.applications.checklist,
      },
    },
    [routes.applications.importClaim]: {
      on: {
        CONTINUE: routes.applications.index,
        EDIT_PHONE: routes.user.settings,
        ENABLE_MFA: routes.twoFactor.smsSetup,
        VERIFY_PHONE: routes.twoFactor.smsConfirm,
      },
    },
    [routes.applications.index]: {
      meta: {},
      on: {
        CONTINUE: routes.applications.uploadDocsOptions,
        IMPORT_APPLICATION: routes.applications.importClaim,
        NEW_APPLICATION: routes.applications.getReady,
        PAYMENT: routes.applications.status.payments,
        STATUS: routes.applications.status.claim,
      },
    },
    [routes.applications.checklist]: {
      meta: {},
      on: {
        REVIEW_AND_CONFIRM: [
          {
            target: routes.applications.bondingLeaveAttestation,
            cond: "isBondingLeave",
          },
          {
            target: routes.applications.caringLeaveAttestation,
            cond: "isCaringLeave",
          },
          { target: routes.applications.review },
        ],
        ...checklistEvents,
      },
    },
    [routes.applications.success]: {
      meta: {},
      on: {
        CONTINUE: routes.applications.getReady,
      },
    },
    [routes.applications.name]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: nameFields,
      },
      on: {
        CONTINUE: routes.applications.gender,
      },
    },
    [routes.applications.gender]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: genderFields,
      },
      on: {
        CONTINUE: routes.applications.phoneNumber,
      },
    },
    [routes.applications.phoneNumber]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: phoneNumberFields,
      },
      on: {
        CONTINUE: routes.applications.address,
      },
    },
    [routes.applications.address]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: addressFields,
      },
      on: {
        CONTINUE: routes.applications.dateOfBirth,
      },
    },
    [routes.applications.dateOfBirth]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: dateOfBirthFields,
      },
      on: {
        CONTINUE: routes.applications.stateId,
      },
    },
    [routes.applications.stateId]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: stateIdFields,
      },
      on: {
        CONTINUE: routes.applications.ssn,
      },
    },
    [routes.applications.uploadId]: {
      meta: {
        step: ClaimSteps.uploadId,
        // user fields are not currently evaluated
        // when determining step completeness
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.index,
            cond: "isCompleted",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.ssn]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: ssnFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.leaveReason]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leaveReasonFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.reasonPregnancy,
            cond: "isMedicalOrPregnancyLeave",
          },
          {
            target: routes.applications.dateOfChild,
            cond: "isBondingLeave",
          },
          {
            target: routes.applications.familyMemberRelationship,
            cond: "isCaringLeave",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.reducedLeaveSchedule]: {
      meta: {
        applicableRules: ["min_reduced_leave_minutes"],
        step: ClaimSteps.leaveDetails,
        fields: reducedLeaveScheduleFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.leaveSpansBenefitYearsReduced,
            cond: "doLeaveDatesCrossBenefitYears",
          },
          {
            target: routes.applications.leavePeriodIntermittent,
          },
        ],
      },
    },
    [routes.applications.reasonPregnancy]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: reasonPregnancyFields,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodContinuous,
      },
    },
    [routes.applications.uploadCertification]: {
      meta: {
        step: ClaimSteps.uploadCertification,
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.index,
            cond: "isCompleted",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.upload.index]: {
      on: {
        [UploadType.mass_id]: routes.applications.upload.stateId,
        [UploadType.non_mass_id]: routes.applications.upload.otherId,
        [UploadType.medical_certification]:
          routes.applications.upload.medicalCertification,
        [UploadType.proof_of_birth]:
          routes.applications.upload.bondingProofOfBirth,
        [UploadType.proof_of_placement]:
          routes.applications.upload.bondingProofOfPlacement,
        [UploadType.pregnancy_medical_certification]:
          routes.applications.upload.pregnancyCertification,
        [UploadType.caring_leave_certification]:
          routes.applications.upload.caringCertification,
      },
    },
    [routes.applications.upload.stateId]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.otherId]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.medicalCertification]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.bondingProofOfBirth]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.bondingProofOfPlacement]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.pregnancyCertification]: {
      on: uploadDocEvents,
    },
    [routes.applications.upload.caringCertification]: {
      on: uploadDocEvents,
    },
    [routes.applications.dateOfChild]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: dateOfChildFields,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodContinuous,
      },
    },
    [routes.applications.leavePeriodContinuous]: {
      meta: {
        applicableRules: [
          "disallow_12mo_continuous_leave_period",
          "disallow_caring_leave_before_july",
        ],
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodContinuousFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.leaveSpansBenefitYearsContinuous,
            cond: "doLeaveDatesCrossBenefitYears",
          },
          {
            target: routes.applications.leavePeriodReducedSchedule,
          },
        ],
      },
    },
    [routes.applications.leavePeriodReducedSchedule]: {
      meta: {
        applicableRules: [
          "disallow_12mo_reduced_leave_period",
          "disallow_caring_leave_before_july",
        ],
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodReducedScheduleFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.reducedLeaveSchedule,
            cond: "hasReducedScheduleLeavePeriods",
          },
          {
            target: routes.applications.leavePeriodIntermittent,
          },
        ],
      },
    },
    [routes.applications.leavePeriodIntermittent]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodIntermittentFields,
        applicableRules: [
          "disallow_12mo_intermittent_leave_period",
          "disallow_caring_leave_before_july",
          // This page is after the Continuous and Reduced Schedule pages,
          // so on this page is where we can surface validation issues
          // related to the following rules:
          "disallow_hybrid_intermittent_leave",
          "min_leave_periods",
        ],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.intermittentFrequency,
            cond: "hasIntermittentLeavePeriods",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.intermittentFrequency]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: intermittentFrequencyFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.leaveSpansBenefitYearsIntermittent,
            cond: "doLeaveDatesCrossBenefitYears",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.leaveSpansBenefitYearsContinuous]: {
      meta: {
        step: ClaimSteps.leaveDetails,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodReducedSchedule,
      },
    },
    [routes.applications.leaveSpansBenefitYearsIntermittent]: {
      meta: {
        step: ClaimSteps.leaveDetails,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.leaveSpansBenefitYearsReduced]: {
      meta: {
        step: ClaimSteps.leaveDetails,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodIntermittent,
      },
    },
    [routes.applications.previousLeavesIntro]: {
      meta: {
        step: ClaimSteps.otherLeave,
      },
      on: {
        CONTINUE: routes.applications.previousLeavesSameReason,
      },
    },
    [routes.applications.previousLeavesSameReason]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesSameReasonFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.previousLeavesSameReasonDetails,
            cond: "hasPreviousLeavesSameReason",
          },
          {
            target: routes.applications.previousLeavesOtherReason,
          },
        ],
      },
    },
    [routes.applications.previousLeavesSameReasonDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesSameReasonDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.previousLeavesOtherReason,
      },
    },
    [routes.applications.previousLeavesOtherReason]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesOtherReasonFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.previousLeavesOtherReasonDetails,
            cond: "hasPreviousLeavesOtherReason",
          },
          { target: routes.applications.concurrentLeavesIntro },
        ],
      },
    },
    [routes.applications.previousLeavesOtherReasonDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesOtherReasonDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.concurrentLeavesIntro,
      },
    },
    [routes.applications.concurrentLeavesIntro]: {
      meta: {
        step: ClaimSteps.otherLeave,
      },
      on: {
        CONTINUE: routes.applications.concurrentLeaves,
      },
    },
    [routes.applications.concurrentLeaves]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: concurrentLeavesFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.concurrentLeavesDetails,
            cond: "hasConcurrentLeave",
          },
          { target: routes.applications.employerBenefitsIntro },
        ],
      },
    },
    [routes.applications.concurrentLeavesDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: concurrentLeavesDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.employerBenefitsIntro,
      },
    },
    [routes.applications.employerBenefitsIntro]: {
      meta: {
        step: ClaimSteps.otherLeave,
      },
      on: {
        CONTINUE: routes.applications.employerBenefits,
      },
    },
    [routes.applications.employerBenefits]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: employerBenefitsFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.employerBenefitsDetails,
            cond: "hasEmployerBenefits",
          },
          {
            target: routes.applications.otherIncomes,
          },
        ],
      },
    },
    [routes.applications.employerBenefitsDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: employerBenefitsDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.otherIncomes,
      },
    },
    [routes.applications.otherIncomes]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: otherIncomesFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.otherIncomesDetails,
            cond: "hasOtherIncomes",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.otherIncomesDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: otherIncomesDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.employmentStatus]: {
      meta: {
        applicableRules: [
          // Show this error after we've gathered SSN and EIN
          "require_employee",
        ],
        step: ClaimSteps.employerInformation,
        fields: employmentStatusFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.department,
            cond: "hasEmployerWithDepartments",
          },
          {
            target: routes.applications.notifiedEmployer,
            cond: "isEmployed",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.department]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: departmentFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.notifiedEmployer,
            cond: "isEmployed",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.notifiedEmployer]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: notifiedEmployerFields,
      },
      on: {
        CONTINUE: routes.applications.workPatternType,
      },
    },
    [routes.applications.paymentMethod]: {
      meta: {
        step: ClaimSteps.payment,
        fields: paymentMethodFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.taxWithholding]: {
      meta: {
        step: ClaimSteps.taxWithholding,
        fields: taxWithholdingFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.bondingLeaveAttestation]: {
      meta: {
        step: ClaimSteps.reviewAndConfirm,
        fields: [],
      },
      on: {
        CONTINUE: routes.applications.review,
      },
    },
    [routes.applications.review]: {
      meta: {
        step: ClaimSteps.reviewAndConfirm,
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.success,
            cond: "isCompleted",
          },
          {
            target: routes.applications.index,
            cond: "isSubmittedApplicationSplit",
          },
          {
            target: routes.applications.checklist,
          },
        ],
        CHECKLIST: routes.applications.checklist,
        ...checklistEvents,
      },
    },
    [routes.applications.uploadDocsOptions]: {
      meta: {},
      on: {
        UPLOAD_ID: routes.applications.uploadId,
        UPLOAD_MASS_ID: routes.applications.uploadId,
        UPLOAD_CERTIFICATION: routes.applications.uploadCertification,
      },
    },
    [routes.applications.workPatternType]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: workPatternTypeFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.scheduleFixed,
            cond: "isFixedWorkPattern",
          },
          {
            target: routes.applications.scheduleVariable,
            cond: "isVariableWorkPattern",
          },
        ],
      },
    },
    [routes.applications.scheduleFixed]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleFixedFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.scheduleVariable]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleVariableFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.familyMemberDateOfBirth]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: familyMemberDateOfBirthFields,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodContinuous,
      },
    },
    [routes.applications.familyMemberName]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: familyMemberNameFields,
      },
      on: {
        CONTINUE: routes.applications.familyMemberDateOfBirth,
      },
    },
    [routes.applications.familyMemberRelationship]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: familyMemberRelationshipFields,
      },
      on: {
        CONTINUE: routes.applications.familyMemberName,
      },
    },
    [routes.applications.caringLeaveAttestation]: {
      meta: {
        step: ClaimSteps.reviewAndConfirm,
        fields: [],
      },
      on: {
        CONTINUE: routes.applications.review,
      },
    },
    [routes.applications.status.claim]: {
      on: {
        UPLOAD_PROOF_OF_BIRTH: routes.applications.upload.bondingProofOfBirth,
        UPLOAD_PROOF_OF_PLACEMENT:
          routes.applications.upload.bondingProofOfPlacement,
        UPLOAD_DOC_OPTIONS: routes.applications.upload.index,
        VIEW_PAYMENTS: routes.applications.status.payments,
        START_MODIFICATION: routes.applications.modify.index,
        CONTINUE_MODIFICATION: routes.applications.modify.type,
      },
    },
    [routes.applications.status.payments]: {
      on: {
        STATUS: routes.applications.status.claim,
      },
    },
    [routes.applications.modify.index]: {
      on: {
        CONTINUE: routes.applications.modify.type,
      },
    },
    [routes.applications.modify.type]: {
      on: {
        CONTINUE: [
          {
            target: routes.applications.upload.modify.pregnancyCertification,
            cond: every("isExtendingModification", "isPregnancyLeave"),
          },
          {
            target: routes.applications.upload.modify.caringCertification,
            cond: every("isExtendingModification", "isCaringLeave"),
          },
          {
            target: routes.applications.upload.modify.medicalCertification,
            cond: every(
              "isExtendingModification",
              "isNonPregnancyMedicalLeave"
            ),
          },
          {
            target: routes.applications.modify.review,
          },
        ],
      },
    },
    [routes.applications.modify.review]: {
      on: {
        CONTINUE: [
          {
            target: routes.applications.modify.success,
            cond: "isExtendingModification",
          },
          {
            target: routes.applications.status.claim,
          },
        ],
      },
    },
    [routes.applications.modify.success]: {
      on: {
        VIEW_STATUS: routes.applications.status.claim,
      },
    },
    [routes.applications.upload.modify.medicalCertification]: {
      on: {
        CONTINUE: routes.applications.modify.review,
      },
    },
    [routes.applications.upload.modify.pregnancyCertification]: {
      on: {
        CONTINUE: routes.applications.modify.review,
      },
    },
    [routes.applications.upload.modify.caringCertification]: {
      on: {
        CONTINUE: routes.applications.modify.review,
      },
    },
  },
};

export default claimantFlow;
