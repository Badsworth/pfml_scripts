/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in a user
 * settings flow.
 */

import routes from "../routes";

export default {
  states: {
    [routes.user.convert]: {
      meta: {},
      on: {
        PREVENT_CONVERSION: routes.applications.getReady,
        /* We cannot move between 2 different flows due to
         * claimant test only using claimant state, therefore,
         * we have no access to redirect to employer pages
         */
        // CONTINUE: routes.employers.organizations,
      },
    },
    [routes.user.consentToDataSharing]: {
      meta: {},
      on: {
        ENABLE_MFA: routes.twoFactor.smsIndex,
        // Route to Applications page to support users who are re-consenting.
        // If they're new users with no claims, the Applications page will
        // handle redirecting them
        CONTINUE: routes.applications.index,
      },
    },
    [routes.user.settings]: {
      on: {
        EDIT_MFA_PHONE: routes.twoFactor.smsSetup,
      },
    },
  },
};
