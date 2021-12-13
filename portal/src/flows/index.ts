/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the flow.
 * @see docs/portal/development.md
 */
import claimant, {
  ClaimantFlowContext,
  guards as claimantGuards,
} from "./claimant";
import user, { UserFlowContext, guards as userGuards } from "./user";
import auth from "./auth";
import employer from "./employer";
import routes from "../routes";

export type FlowContext = ClaimantFlowContext | UserFlowContext;

export const guards = {
  ...claimantGuards,
  ...userGuards,
};

export default {
  id: "portal-flow",
  initial: routes.applications.index,
  states: {
    ...auth.states,
    ...claimant.states,
    ...employer.states,
    ...user.states,
  },
  context: {},
};
