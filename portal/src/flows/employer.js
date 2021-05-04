/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the application flow.
 */
import routes from "../routes";

export default {
  states: {
    [routes.employers.addOrganization]: {
      on: {
        CONTINUE: routes.employers.verifyContributions,
      },
    },
    [routes.employers.confirmation]: {},
    [routes.employers.createAccount]: {
      on: {
        CREATE_ACCOUNT: routes.auth.verifyAccount,
      },
    },
    [routes.employers.dashboard]: {
      on: {
        // New Application page handles conditional routing for claims, because the logic
        // is dependent on fetching additional claim data from Fineos first
        VIEW_CLAIM: routes.employers.newApplication,
      },
    },
    [routes.employers.finishAccountSetup]: {
      on: {
        SEND_CODE: routes.auth.resetPassword,
      },
    },
    [routes.employers.organizations]: {
      on: {
        BACK: routes.employers.dashboard,
      },
    },
    [routes.employers.review]: {
      on: {
        CONTINUE: routes.employers.success,
      },
    },
    [routes.employers.status]: {},
    [routes.employers.success]: {},
    [routes.employers.newApplication]: {
      on: {
        CLAIM_NOT_REVIEWABLE: routes.employers.status,
        CONFIRMATION: routes.employers.confirmation,
        CONTINUE: routes.employers.review,
      },
    },
    [routes.employers.verificationSuccess]: {},
    [routes.employers.verifyContributions]: {
      on: {
        CONTINUE: routes.employers.verificationSuccess,
      },
    },
    [routes.employers.verificationSuccess]: {},
    [routes.employers.welcome]: {},
  },
};
