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
import { fields as addressFields } from "../pages/claims/address";
import { fields as dateOfBirthFields } from "../pages/claims/date-of-birth";
import { fields as dateOfChildFields } from "../pages/claims/date-of-child";
import { fields as employerBenefitDetailsFields } from "../pages/claims/employer-benefit-details";
import { fields as employerBenefitsFields } from "../pages/claims/employer-benefits";
import { fields as employmentStatusFields } from "../pages/claims/employment-status";
import { get } from "lodash";
import { fields as intermittentFrequencyFields } from "../pages/claims/intermittent-frequency";
import { fields as leavePeriodContinuousFields } from "../pages/claims/leave-period-continuous";
import { fields as leavePeriodIntermittentFields } from "../pages/claims/leave-period-intermittent";
import { fields as leavePeriodReducedScheduleFields } from "../pages/claims/leave-period-reduced-schedule";
import { fields as leaveReasonFields } from "../pages/claims/leave-reason";
import { fields as nameFields } from "../pages/claims/name";
import { fields as notifiedEmployerFields } from "../pages/claims/notified-employer";
import { fields as otherIncomesDetailsFields } from "../pages/claims/other-incomes-details";
import { fields as otherIncomesFields } from "../pages/claims/other-incomes";
import { fields as paymentMethodFields } from "../pages/claims/payment-method";
import { fields as previousLeavesDetailsFields } from "../pages/claims/previous-leaves-details";
import { fields as previousLeavesFields } from "../pages/claims/previous-leaves";
import { fields as reasonPregnancyFields } from "../pages/claims/reason-pregnancy";
import routes from "../routes";
import { fields as scheduleFixedFields } from "../pages/claims/schedule-fixed";
import { fields as scheduleRotatingFields } from "../pages/claims/schedule-rotating";
import { fields as scheduleRotatingNumberWeeksFields } from "../pages/claims/schedule-rotating-number-weeks";
import { fields as scheduleVariableFields } from "../pages/claims/schedule-variable";
import { fields as ssnFields } from "../pages/claims/ssn";
import { fields as stateIdFields } from "../pages/claims/state-id";
import { fields as workPatternTypeFields } from "../pages/claims/work-pattern-type";

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
  hasOtherIncomes: ({ claim }) => claim.temp.has_other_incomes === true,
  hasPreviousLeaves: ({ claim }) => claim.temp.has_previous_leaves === true,
  isFixedWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.fixed,
  isRotatingWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.rotating,
  isVariableWorkPattern: ({ claim }) =>
    get(claim, "work_pattern.work_pattern_type") === WorkPatternType.variable,
};

export default {
  states: {
    [routes.claims.dashboard]: {
      meta: {},
      on: {
        START: routes.claims.start,
        CONSENT_TO_DATA_SHARING: routes.user.consentToDataSharing,
      },
    },
    [routes.claims.start]: {
      meta: {},
      on: {
        CREATE_CLAIM: routes.claims.checklist,
      },
    },
    [routes.user.consentToDataSharing]: {
      meta: {},
      on: {
        CONTINUE: routes.claims.dashboard,
      },
    },
    [routes.applications]: {
      meta: {},
      on: {
        CONTINUE: routes.claims.uploadDocsOptions,
      },
    },
    [routes.claims.checklist]: {
      meta: {},
      on: {
        // These are aids for our unit tests to support
        // navigating the full state machine. Each step
        // in the checklist should have a transition
        // that points to the expected route a user is
        // directed to when they enter the Step.
        VERIFY_ID: routes.claims.name,
        LEAVE_DETAILS: routes.claims.leaveReason,
        OTHER_LEAVE: routes.claims.employerBenefits,
        EMPLOYER_INFORMATION: routes.claims.employmentStatus,
        PAYMENT: routes.claims.paymentMethod,
        REVIEW_AND_CONFIRM: routes.claims.review,
        UPLOAD_CERTIFICATION: routes.claims.uploadCertification,
        UPLOAD_ID: routes.claims.uploadId,
      },
    },
    [routes.claims.success]: {
      meta: {},
      on: {
        CONTINUE: routes.claims.dashboard,
      },
    },
    [routes.claims.name]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: nameFields,
      },
      on: {
        CONTINUE: routes.claims.address,
      },
    },
    [routes.claims.address]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: addressFields,
      },
      on: {
        CONTINUE: routes.claims.dateOfBirth,
      },
    },
    [routes.claims.dateOfBirth]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: dateOfBirthFields,
      },
      on: {
        CONTINUE: routes.claims.stateId,
      },
    },
    [routes.claims.stateId]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: stateIdFields,
      },
      on: {
        CONTINUE: routes.claims.ssn,
      },
    },
    [routes.claims.uploadId]: {
      meta: {
        step: ClaimSteps.uploadId,
        // user fields are not currently evaluated
        // when determining step completeness
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications,
            cond: "isCompleted",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.ssn]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: ssnFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.leaveReason]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leaveReasonFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.reasonPregnancy,
            cond: "isMedicalLeave",
          },
          {
            target: routes.claims.dateOfChild,
            cond: "isBondingLeave",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.reasonPregnancy]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: reasonPregnancyFields,
      },
      on: {
        CONTINUE: routes.claims.leavePeriodContinuous,
      },
    },
    [routes.claims.uploadCertification]: {
      meta: {
        step: ClaimSteps.uploadCertification,
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.applications,
            cond: "isCompleted",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.dateOfChild]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: dateOfChildFields,
      },
      on: {
        CONTINUE: routes.claims.leavePeriodContinuous,
      },
    },
    [routes.claims.leavePeriodContinuous]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodContinuousFields,
      },
      on: {
        CONTINUE: routes.claims.leavePeriodReducedSchedule,
      },
    },
    [routes.claims.leavePeriodReducedSchedule]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leavePeriodReducedScheduleFields,
      },
      on: {
        CONTINUE: routes.claims.leavePeriodIntermittent,
      },
    },
    [routes.claims.leavePeriodIntermittent]: {
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
            target: routes.claims.intermittentFrequency,
            cond: "hasIntermittentLeavePeriods",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.intermittentFrequency]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: intermittentFrequencyFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.employerBenefits]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: employerBenefitsFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.employerBenefitDetails,
            cond: "hasEmployerBenefits",
          },
          {
            target: routes.claims.otherIncomes,
          },
        ],
      },
    },
    [routes.claims.employerBenefitDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: employerBenefitDetailsFields,
      },
      on: {
        CONTINUE: routes.claims.otherIncomes,
      },
    },
    [routes.claims.otherIncomes]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: otherIncomesFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.otherIncomesDetails,
            cond: "hasOtherIncomes",
          },
          {
            target: routes.claims.previousLeaves,
          },
        ],
      },
    },
    [routes.claims.otherIncomesDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: otherIncomesDetailsFields,
      },
      on: {
        CONTINUE: routes.claims.previousLeaves,
      },
    },
    [routes.claims.previousLeaves]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.previousLeavesDetails,
            cond: "hasPreviousLeaves",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.previousLeavesDetails]: {
      meta: {
        step: ClaimSteps.otherLeave,
        fields: previousLeavesDetailsFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.employmentStatus]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: employmentStatusFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.notifiedEmployer,
            cond: "isEmployed",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.notifiedEmployer]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: notifiedEmployerFields,
      },
      on: {
        CONTINUE: routes.claims.workPatternType,
      },
    },
    [routes.claims.paymentMethod]: {
      meta: {
        step: ClaimSteps.payment,
        fields: paymentMethodFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.review]: {
      meta: {
        step: ClaimSteps.reviewAndConfirm,
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.success,
            cond: "isCompleted",
          },
          {
            target: routes.claims.checklist,
          },
        ],
      },
    },
    [routes.claims.uploadDocsOptions]: {
      meta: {},
      on: {
        UPLOAD_ID: routes.claims.uploadId,
        UPLOAD_MASS_ID: routes.claims.uploadId,
        UPLOAD_CERTIFICATION: routes.claims.uploadCertification,
      },
    },
    [routes.claims.workPatternType]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: workPatternTypeFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.scheduleRotatingNumberWeeks,
            cond: "isRotatingWorkPattern",
          },
          {
            target: routes.claims.scheduleFixed,
            cond: "isFixedWorkPattern",
          },
          {
            target: routes.claims.scheduleVariable,
            cond: "isVariableWorkPattern",
          },
          {
            target: routes.claims.hoursWorkedPerWeek,
          },
        ],
      },
    },
    [routes.claims.scheduleFixed]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleFixedFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.scheduleRotatingNumberWeeks]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleRotatingNumberWeeksFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.scheduleVariable,
            cond: "isVariableWorkPattern",
          },
          {
            target: routes.claims.scheduleRotating,
          },
        ],
      },
    },
    [routes.claims.scheduleRotating]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleRotatingFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.scheduleVariable]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: scheduleVariableFields,
      },
      on: {
        CONTINUE: routes.claims.checklist,
      },
    },
  },
};
