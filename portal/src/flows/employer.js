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
    [routes.employers.dashboard]: {},
    [routes.employers.verifyAccount]: {
      on: {
        SEND_CODE: routes.auth.resetPassword,
      },
    },
  },
};
