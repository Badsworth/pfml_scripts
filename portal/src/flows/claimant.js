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
import { EmploymentStatus, WorkPatternType } from "../models/Claim";
import { ClaimSteps } from "../models/Step";
import { fields as addressFields } from "../pages/applications/address";
import { fields as dateOfBirthFields } from "../pages/applications/date-of-birth";
import { fields as dateOfChildFields } from "../pages/applications/date-of-child";
import { fields as employerBenefitDetailsFields } from "../pages/applications/employer-benefit-details";
import { fields as employerBenefitsFields } from "../pages/applications/employer-benefits";
import { fields as employmentStatusFields } from "../pages/applications/employment-status";
import { get } from "lodash";
import { fields as intermittentFrequencyFields } from "../pages/applications/intermittent-frequency";
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
import { fields as previousLeavesDetailsFields } from "../pages/applications/previous-leaves-details";
import { fields as previousLeavesFields } from "../pages/applications/previous-leaves";
import { fields as reasonPregnancyFields } from "../pages/applications/reason-pregnancy";
import { fields as reducedLeaveScheduleFields } from "../pages/applications/reduced-leave-schedule";
import routes from "../routes";
import { fields as scheduleFixedFields } from "../pages/applications/schedule-fixed";
import { fields as scheduleVariableFields } from "../pages/applications/schedule-variable";
import { fields as ssnFields } from "../pages/applications/ssn";
import { fields as stateIdFields } from "../pages/applications/state-id";
import { fields as workPatternTypeFields } from "../pages/applications/work-pattern-type";

/**
 * @see https://xstate.js.org/docs/guides/guards.html
 */
export const guards = {
  isMedicalLeave: ({ claim }) => claim.isMedicalLeave,
  isBondingLeave: ({ claim }) => claim.isBondingLeave,
  isEmployed: ({ claim }) =>
    get(claim, "employment_status") === EmploymentStatus.employed,
  isCompleted: ({ claim }) => claim.isCompleted,
  hasStateId: ({ claim }) => claim.has_state_id === true,
  hasEmployerBenefits: ({ claim }) => claim.temp.has_employer_benefits === true,
  hasIntermittentLeavePeriods: ({ claim }) =>
    claim.has_intermittent_leave_periods === true,
  hasReducedScheduleLeavePeriods: ({ claim }) =>
    claim.has_reduced_schedule_leave_periods === true,
  hasOtherIncomes: ({ claim }) => claim.temp.has_other_incomes === true,
  hasPreviousLeaves: ({ claim }) => claim.temp.has_previous_leaves === true,
  // TODO (CP-1447): Remove this guard once the feature flag is obsolete
  showPhone: () => isFeatureEnabled("claimantShowPhone"),
  // TODO (CP-1247): Show previous leaves related questions
  showPreviousLeaves: () => isFeatureEnabled("claimantShowPreviousLeaves"),
  isFixedWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.fixed,
  isVariableWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.variable,
};

export default {
  states: {
    [routes.applications.dashboard]: {
      meta: {},
      on: {
        START: routes.applications.start,
        CONSENT_TO_DATA_SHARING: routes.user.consentToDataSharing,
      },
    },
    [routes.applications.start]: {
      meta: {},
      on: {
        CREATE_CLAIM: routes.applications.checklist,
      },
    },
    [routes.user.consentToDataSharing]: {
      meta: {},
      on: {
        CONTINUE: routes.applications.dashboard,
      },
    },
    [routes.applications.index]: {
      meta: {},
      on: {
        CONTINUE: routes.applications.uploadDocsOptions,
      },
    },
    [routes.applications.checklist]: {
      meta: {},
      on: {
        // These are aids for our unit tests to support
        // navigating the full state machine. Each step
        // in the checklist should have a transition
        // that points to the expected route a user is
        // directed to when they enter the Step.
        VERIFY_ID: routes.applications.name,
        LEAVE_DETAILS: routes.applications.leaveReason,
        OTHER_LEAVE: routes.applications.employerBenefits,
        EMPLOYER_INFORMATION: routes.applications.employmentStatus,
        PAYMENT: routes.applications.paymentMethod,
        REVIEW_AND_CONFIRM: [
          {
            target: routes.applications.bondingLeaveAttestation,
            cond: "isBondingLeave",
          },
          { target: routes.applications.review },
        ],
        UPLOAD_CERTIFICATION: routes.applications.uploadCertification,
        UPLOAD_ID: routes.applications.uploadId,
      },
    },
    [routes.applications.success]: {
      meta: {},
      on: {
        CONTINUE: routes.applications.dashboard,
      },
    },
    [routes.applications.name]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: nameFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.phoneNumber,
            cond: "showPhone",
          },
          {
            target: routes.applications.address,
          },
        ],
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
            cond: "isMedicalLeave",
          },
          {
            target: routes.applications.dateOfChild,
            cond: "isBondingLeave",
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
        CONTINUE: routes.applications.leavePeriodIntermittent,
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
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodContinuousFields,
      },
      on: {
        CONTINUE: routes.applications.leavePeriodReducedSchedule,
      },
    },
    [routes.applications.leavePeriodReducedSchedule]: {
      meta: {
        // This page is after the Continuous page, so on this page is
        // where we can surface validation issues related to the following rules:
        applicableRules: ["disallow_overlapping_leave_periods"],
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
        // This page is after the Continuous and Reduced Schedule pages,
        // so on this page is where we can surface validation issues
        // related to the following rules:
        applicableRules: [
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
        CONTINUE: routes.applications.checklist,
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
            target: routes.applications.employerBenefitDetails,
            cond: "hasEmployerBenefits",
          },
          {
            target: routes.applications.otherIncomes,
          },
        ],
      },
    },
    [routes.applications.employerBenefitDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: employerBenefitDetailsFields,
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
            target: routes.applications.previousLeaves,
            cond: "showPreviousLeaves",
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
        CONTINUE: routes.applications.previousLeaves,
      },
    },
    [routes.applications.previousLeaves]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications.previousLeavesDetails,
            cond: "hasPreviousLeaves",
          },
          {
            target: routes.applications.checklist,
          },
        ],
      },
    },
    [routes.applications.previousLeavesDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesDetailsFields,
      },
      on: {
        CONTINUE: routes.applications.checklist,
      },
    },
    [routes.applications.employmentStatus]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: employmentStatusFields,
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
            target: routes.applications.checklist,
          },
        ],
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
  },
};
