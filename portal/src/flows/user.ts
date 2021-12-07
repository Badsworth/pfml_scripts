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
    [routes.user.settings]: {
      on: {
        ENABLE_MFA: routes.twoFactor.smsIndex,
        EDIT_MFA_PHONE: routes.twoFactor.smsSetup,
      },
    },
    [routes.twoFactor.smsIndex]: {
      on: {
        CONTINUE: routes.twoFactor.smsSetup,
      },
    },
    [routes.twoFactor.smsSetup]: {
      on: {
        CONTINUE: routes.twoFactor.smsConfirm,
      },
    },
    [routes.twoFactor.smsConfirm]: {
      on: {
        CONTINUE: routes.applications.index,
      },
    },
  },
};
