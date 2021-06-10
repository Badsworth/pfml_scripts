/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the auth flow.
 */

import routes from "../routes";

export default {
  states: {
    [routes.auth.createAccount]: {
      on: {
        CREATE_ACCOUNT: routes.auth.verifyAccount,
      },
    },
    [routes.auth.forgotPassword]: {
      on: {
        SEND_CODE: routes.auth.resetPassword,
      },
    },
    [routes.auth.adminLogin]: {
      on: {
        LOG_IN: routes.admin.users,
        UNAUTHORIZED_USER: routes.auth.login,
      }
    },
    [routes.auth.login]: {
      on: {
        LOG_IN: routes.applications.index,
        UNCONFIRMED_ACCOUNT: routes.auth.verifyAccount,
      },
    },
    [routes.auth.resetPassword]: {
      on: {
        SET_NEW_PASSWORD: routes.auth.login,
      },
    },
    [routes.auth.verifyAccount]: {
      on: {
        SUBMIT: routes.auth.login,
      },
    },
  },
};
