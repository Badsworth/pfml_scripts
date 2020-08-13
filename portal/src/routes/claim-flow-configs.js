/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the application flow.
 *
 * This configuration is also used to determine and group pages by
 * its step in the application process. The data provided in `meta`
 * is used to determine which step a page belongs to and whether that step
 * is complete, in progress, or not started
 * @see ../models/Step
 */
import { EmploymentStatus, LeaveReason } from "../models/Claim";
import { ClaimSteps } from "../models/Step";
import { fields as averageWorkHoursFields } from "../pages/claims/average-work-hours";
import { fields as dateOfBirthFields } from "../pages/claims/date-of-birth";
import { fields as dateOfChildFields } from "../pages/claims/bonding/date-of-child";
import { fields as durationFields } from "../pages/claims/duration";
import { fields as employerBenefitDetailsFields } from "../pages/claims/employer-benefit-details";
import { fields as employerBenefitsFields } from "../pages/claims/employer-benefits";
import { fields as employmentStatusFields } from "../pages/claims/employment-status";
import { get } from "lodash";
import { fields as leaveDatesFields } from "../pages/claims/leave-dates";
import { fields as leaveReasonFields } from "../pages/claims/leave-reason";
import { fields as nameFields } from "../pages/claims/name";
import { fields as notifiedEmployerFields } from "../pages/claims/notified-employer";
import { fields as otherIncomesDetailsFields } from "../pages/claims/other-incomes-details";
import { fields as otherIncomesFields } from "../pages/claims/other-incomes";
import { fields as paymentMethodFields } from "../pages/claims/payment-method";
import { fields as previousLeavesDetailsFields } from "../pages/claims/previous-leaves-details";
import { fields as previousLeavesFields } from "../pages/claims/previous-leaves";
import { fields as reasonPregnancyFields } from "../pages/claims/reason-pregnancy";
import routes from "./index";
import { fields as ssnFields } from "../pages/claims/ssn";

/**
 * @see https://xstate.js.org/docs/guides/guards.html
 */
export const guards = {
  isMedicalClaim: ({ claim }) =>
    get(claim, "leave_details.reason") === LeaveReason.medical,
  isBondingClaim: ({ claim }) =>
    get(claim, "leave_details.reason") === LeaveReason.bonding,
  isEmployed: ({ claim }) =>
    get(claim, "employment_status") === EmploymentStatus.employed,
  hasStateId: ({ user }) => user.has_state_id === true,
  hasEmployerBenefits: ({ claim }) => claim.has_employer_benefits === true,
  hasOtherIncomes: ({ claim }) => claim.has_other_incomes === true,
  hasPreviousLeaves: ({ claim }) => claim.has_previous_leaves === true,
  isIntermittentOrReduced: ({ claim }) =>
    claim.isIntermittent || claim.isReducedSchedule,
};

export default {
  id: "claim-flow",
  initial: routes.claims.dashboard,
  states: {
    [routes.claims.dashboard]: {
      meta: {},
      on: {
        CREATE_CLAIM: routes.claims.checklist,
        CONSENT_TO_DATA_SHARING: routes.user.consentToDataSharing,
      },
    },
    [routes.user.consentToDataSharing]: {
      meta: {},
      on: {
        CONTINUE: routes.claims.dashboard,
      },
    },
    [routes.claims.checklist]: {
      meta: {},
      on: {
        VERIFY_ID: routes.claims.name,
        LEAVE_DETAILS: routes.claims.leaveReason,
        OTHER_LEAVE: routes.claims.employerBenefits,
        EMPLOYER_INFORMATION: routes.claims.employmentStatus,
        PAYMENT: routes.claims.paymentMethod,
        CONFIRM: routes.claims.confirm,
      },
    },
    [routes.claims.confirm]: {
      meta: {},
      on: {
        CONTINUE: routes.claims.success,
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
        // user fields are not currently evaluated
        // when determining step completeness
        fields: [],
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.uploadStateId,
            cond: "hasStateId",
          },
          {
            target: routes.claims.uploadOtherId,
          },
        ],
      },
    },
    [routes.claims.uploadStateId]: {
      meta: {
        step: ClaimSteps.verifyId,
        // user fields are not currently evaluated
        // when determining step completeness
        fields: [],
      },
      on: {
        CONTINUE: routes.claims.ssn,
      },
    },
    [routes.claims.uploadOtherId]: {
      meta: {
        step: ClaimSteps.verifyId,
        // user fields are not currently evaluated
        // when determining step completeness
        fields: [],
      },
      on: {
        CONTINUE: routes.claims.ssn,
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
            cond: "isMedicalClaim",
          },
          {
            target: routes.claims.bonding.dateOfChild,
            cond: "isBondingClaim",
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
        CONTINUE: routes.claims.uploadCertification,
      },
    },
    [routes.claims.uploadCertification]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: [],
      },
      on: {
        CONTINUE: routes.claims.duration,
      },
    },
    [routes.claims.duration]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: durationFields,
      },
      on: {
        CONTINUE: [
          {
            target: routes.claims.averageWorkHours,
            cond: "isIntermittentOrReduced",
          },
          {
            target: routes.claims.leaveDates,
          },
        ],
      },
    },
    [routes.claims.bonding.dateOfChild]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: dateOfChildFields,
      },
      on: {
        CONTINUE: routes.claims.uploadCertification,
      },
    },
    [routes.claims.averageWorkHours]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: averageWorkHoursFields,
      },
      on: {
        CONTINUE: routes.claims.leaveDates,
      },
    },
    [routes.claims.leaveDates]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leaveDatesFields,
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
        CONTINUE: routes.claims.checklist,
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
  },
};
