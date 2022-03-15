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
    [routes.auth.login]: {
      on: {
        ENABLE_MFA: routes.twoFactor.smsIndex,
        VERIFY_CODE: routes.twoFactor.smsVerify,
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
    [routes.twoFactor.smsVerify]: {
      on: {
        LOG_IN: routes.applications.index,
      },
    },
    [routes.twoFactor.smsIndex]: {
      on: {
        CONTINUE: routes.applications.index,
        EDIT_MFA_PHONE: routes.twoFactor.smsSetup,
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
        RETURN_TO_SETTINGS: routes.user.settings,
      },
    },
  },
};
