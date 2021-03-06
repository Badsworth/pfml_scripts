// @ts-check

/**
 * Feature flags. A feature flag can be enabled/disabled at the environment level.
 * Its value will either be true or false. Environments can override this value.
 * See: ../../docs/portal/feature-flags.md
 * @type {Record<string, Record<string, boolean>>}
 */
const flagsConfig = {
  // Define a default or all feature flags here.
  // Environments will fallback to these default values.
  defaults: {
    // When this flag is enabled, the user can see the "Employment status"
    // question in the claimant flow (CP-1204)
    // TODO (CP-1281): Show employment status question when Portal supports other employment statuses
    claimantShowEmploymentStatus: false,

    // When this flag is enabled optional MFA will be enabled for claimant users.
    claimantShowMFA: false,
    claimantSyncCognitoPreferences: false,

    // When this flag is enabled, a claimant can request modifications to their leave
    // TODO (PORTAL-2064) Remove flag
    claimantShowModifications: false,

    // When this flag is enabled, the military leave options are selectable on
    // the Leave Reason page in the claimant flow (CP-1145)
    // TODO (CP-534): Show all options when portal supports activeDutyFamily, serviceMemberFamily
    claimantShowMilitaryLeaveTypes: false,

    // When this flag is enabled payment status phase three work will be displayed.
    // Phase 3 work encompasses detailed information on payment table Delays and Holiday Alerts
    // TODO (PORTAL-1934): remove flag
    claimantShowPaymentsPhaseThree: true,

    // When this flag is enabled logic in code will account for new payment schedule post FINEOS deploy
    // TODO (PORTAL-1915) Remove flag
    claimantUseFineosNewPaymentSchedule: false,

    // When enabled, collect leave admin phone, first name, and last name
    // TODO (PORTAL-2089) Remove flag
    employerCollectNameAndPhone: false,

    // When this flag true, you can BYPASS maintenance pages that are currently present.
    // See docs/portal/maintenance-pages.md for more details.
    noMaintenance: false,

    // When this flag is enabled, the user can see the site.
    // To immediately hide the site from people who previously overrode this
    // flag in a cookie, you can rename this flag to something else (and also
    // update the reference to it in _app.js), but try to keep it prefixed with pfml.
    // https://lwd.atlassian.net/browse/CP-459
    pfmlTerriyay: false,

    // TODO (PORTAL-1893) remove feature flag
    // When this flag is enabled the holiday alert will be displayed on the payments pages.
    showHolidayAlert: true,

    // When this flag is true, claims that would span multiple benefit years
    // are split into separate claims
    // See: https://lwd.atlassian.net/wiki/spaces/DD/pages/2194014380/Tech+Spec+-+Claims+spanning+two+benefit+years
    splitClaimsAcrossBY: false,
  },
  // Environments can optionally override a default feature flag below.
  // The environment keys should use the same envName defined in
  // environment config files.
  "cps-preview": {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  development: {
    example: true,
    pfmlTerriyay: true,
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  test: {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  stage: {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  training: {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  performance: {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  uat: {
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  local: {
    pfmlTerriyay: true,
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
  prod: {
    pfmlTerriyay: true,
    claimantShowMFA: true,
    claimantShowPaymentsPhaseThree: true,
    showHolidayAlert: true,
  },
};

/**
 * Merges the default feature flags with any environment-specific overrides
 * @param {string} env - Environment name
 * @returns {string} Stringified JSON representation of the feature flags for the given environment
 */
function featureFlags(env) {
  const envFlags = Object.assign({}, flagsConfig.defaults, flagsConfig[env]);

  // This gets passed into the app as an environment variable, which *must* be a string.
  return JSON.stringify(envFlags);
}

module.exports = featureFlags;
