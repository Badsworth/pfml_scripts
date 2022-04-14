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
        VERIFY_ORG: routes.employers.organizations,
        VIEW_CLAIM: routes.employers.status,
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
    [routes.employers.status]: {
      on: {
        REDIRECT_REVIEWABLE_CLAIM: routes.employers.review,
      },
    },
    [routes.employers.success]: {
      on: {
        BACK: routes.employers.dashboard,
      },
    },
    [routes.employers.newApplication]: {
      on: {
        REDIRECT: routes.employers.status,
      },
    },
    [routes.employers.verificationSuccess]: {},
    [routes.employers.verifyContributions]: {
      on: {
        CONTINUE: routes.employers.verificationSuccess,
      },
    },
    [routes.employers.welcome]: {},
  },
};
