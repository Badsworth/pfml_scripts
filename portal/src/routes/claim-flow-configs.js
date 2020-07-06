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
import { ClaimSteps } from "../models/Step";
import { fields as durationFields } from "../pages/claims/duration";
import { fields as employmentStatusFields } from "../pages/claims/employment-status";
import { fields as leaveDatesFields } from "../pages/claims/leave-dates";
import { fields as leaveReasonFields } from "../pages/claims/leave-reason";
import { fields as nameFields } from "../pages/claims/name";
import { fields as notifiedEmployerFields } from "../pages/claims/notified-employer";
import { fields as reasonPregnancyFields } from "../pages/claims/reason-pregnancy";
import routes from "./index";
import { fields as ssnFields } from "../pages/claims/ssn";

export default {
  id: "leave-application-routing",
  initial: routes.claims.checklist,
  states: {
    [routes.claims.checklist]: {
      meta: {},
      on: {
        VERIFY_ID: routes.claims.name,
        LEAVE_DETAILS: routes.claims.leaveReason,
        EMPLOYER_INFORMATION: routes.claims.employmentStatus,
        // TODO: remove once conditional routing for leaveReason exists
        TEMP_TEST_PREGNANCY_PATH: routes.claims.reasonPregnancy,
      },
    },
    [routes.claims.name]: {
      meta: {
        step: ClaimSteps.verifyId,
        fields: nameFields,
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
        // TODO make conditional to reason-pregnancy if leave_details.reason is medical
        CONTINUE: routes.claims.leaveDates,
      },
    },
    [routes.claims.leaveDates]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: leaveDatesFields,
      },
      on: {
        CONTINUE: routes.claims.duration,
      },
    },
    [routes.claims.reasonPregnancy]: {
      meta: {
        step: ClaimSteps.leaveDetails,
        fields: reasonPregnancyFields,
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
        CONTINUE: routes.claims.checklist,
      },
    },
    [routes.claims.employmentStatus]: {
      meta: {
        step: ClaimSteps.employerInformation,
        fields: employmentStatusFields,
      },
      on: {
        // TODO: Make conditional to checklist if employment_status is not employed
        CONTINUE: routes.claims.notifiedEmployer,
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
  },
};
