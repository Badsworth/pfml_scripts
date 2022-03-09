/**
 * @file Configuration for building an xstate state machine for routing
 * @see https://xstate.js.org/docs/about/concepts.html#finite-state-machines
 * Each state represents a page in the portal application, keyed by the
 * page's url route. The CONTINUE transition represents the next page in the
 * the application flow.
 */
import routes from "../routes";

export interface EmployerFlowContext {
  employerShowMultiLeaveDashboard?: boolean;
}
type GuardFn = (context: EmployerFlowContext) => boolean;

export const guards: { [guardName: string]: GuardFn } = {
  isEmployerShowMultiLeaveDashboardEnabled: (context: EmployerFlowContext) => {
    return !!context.employerShowMultiLeaveDashboard;
  },
};

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
        // This page handles conditional routing for claims, because the logic
        // is dependent on fetching additional claim data from Fineos first
        VIEW_CLAIM: [
          {
            // TODO (PORTAL-1560): Remove the conditional routing and always route to the status page.
            cond: "isEmployerShowMultiLeaveDashboardEnabled",
            target: routes.employers.status,
          },
          {
            target: routes.employers.newApplication,
          },
        ],
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
        // TODO (PORTAL-1560): Remove these transitions once the page is just a redirect
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
