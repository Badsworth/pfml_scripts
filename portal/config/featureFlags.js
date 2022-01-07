/**
 * Feature flags. A feature flag can be enabled/disabled at the environment level.
 * Its value will either be true or false. Environments can override this value.
 * @see ../../docs/portal/feature-flags.md
 */
const flagsConfig = {
  // Define a default or all feature flags here.
  // Environments will fallback to these default values.
  defaults: {
    // When enabled, the "Find my application" flow is displayed.
    // TODO (PORTAL-1327): Remove channelSwitching flag once enabled everywhere.
    channelSwitching: false,

    // When this flag is enabled, the user can see the "Employment status"
    // question in the claimant flow (CP-1204)
    // TODO (CP-1281): Show employment status question when Portal supports other employment statuses
    claimantShowEmploymentStatus: false,

    // When this flag is enabled optional MFA will be enabled for claimant users.
    claimantShowMFA: false,

    // When this flag is enabled, the military leave options are selectable on
    // the Leave Reason page in the claimant flow (CP-1145)
    // TODO (CP-534): Show all options when portal supports activeDutyFamily, serviceMemberFamily
    claimantShowMilitaryLeaveTypes: false,

    // When this flag is false, you can bypass the deparment capture form when applying
    claimantShowOrganizationUnits: false,

    // When this flag is enabled, the claim payments section for claimants will show
    claimantShowPayments: true,

    // When this flag is enabled payment status phase two work will be displayed.
    claimantShowPaymentsPhaseTwo: false,

    // Show multiple leave request UI updates to leave admins.
    // TODO (PORTAL-1151) Remove flag
    employerShowMultiLeave: false,

    // When this flag true, you can BYPASS maintenance pages that are currently present.
    // See docs/portal/maintenance-pages.md for more details.
    noMaintenance: false,

    // When this flag is enabled, the user can see the site.
    // To immediately hide the site from people who previously overrode this
    // flag in a cookie, you can rename this flag to something else (and also
    // update the reference to it in _app.js), but try to keep it prefixed with pfml.
    // https://lwd.atlassian.net/browse/CP-459
    pfmlTerriyay: false,

    // When this flag is true, PDF files up to 10mb are sent to the API.
    sendLargePdfToApi: false,
  },
  // Environments can optionally override a default feature flag below.
  // The environment keys should use the same envName defined in
  // environment config files.
  "cps-preview": {},
  development: {
    example: true,
    pfmlTerriyay: true,
    claimantShowPayments: true,
  },
  test: {
    claimantShowPayments: true,
  },
  stage: {
    claimantShowPayments: true,
  },
  training: {
    claimantShowPayments: true,
  },
  performance: {
    claimantShowPayments: true,
  },
  uat: {
    claimantShowPayments: true,
  },
  local: {
    pfmlTerriyay: true,
    claimantShowPayments: true,
  },
  prod: {
    pfmlTerriyay: true,
    claimantShowPayments: true,
  },
};

/**
 * Merges the default feature flags with any environment-specific overrides
 * @param {string} env - Environment name
 * @returns {object} Feature flags for the given environment
 */
function featureFlags(env) {
  return Object.assign({}, flagsConfig.defaults, flagsConfig[env]);
}

module.exports = featureFlags;
