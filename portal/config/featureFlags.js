/**
 * Feature flags. A feature flag can be enabled/disabled at the environment level.
 * Its value will either be true or false. Environments can override this value.
 * @see ../../docs/portal/feature-flags.md
 */
const flagsConfig = {
  // Define a default or all feature flags here.
  // Environments will fallback to these default values.
  defaults: {
    // When this flag is enabled, the user can see the "Employment status"
    // question in the claimant flow (CP-1204)
    // TODO (CP-1281): Show employment status question when Portal supports other employment statuses
    claimantShowEmploymentStatus: false,

    // When this flag is enabled, the military leave options are selectable on
    // the Leave Reason page in the claimant flow (CP-1145)
    // TODO (CP-534): Show all options when portal supports activeDutyFamily, serviceMemberFamily
    claimantShowMilitaryLeaveTypes: false,

    // When this flag is enabled, the "Other leave, income, and benefits" step of
    // the Claim flow becomes visible, and its validation rules are applied via
    // a X-FF-Require-Other-Leaves header on API requests.
    // TODO (CP-1346): Show this step once it's been integrated w/ the API.
    claimantShowOtherLeaveStep: false,

    // When this flag is enabled, the Leave Admin dashboard shows filter functionality
    // TODO (EMPLOYER-1412): Remove flag
    employerShowDashboardFilters: false,

    // When this flag is enabled, file upload is visible on the Review page
    // TODO (EMPLOYER-665): Show file upload once the endpoint is available
    employerShowFileUpload: false,

    // When this flag is enabled, the "Previous leaves" section on Review page is visible
    // TODO (EMPLOYER-718): Remove flag
    employerShowPreviousLeaves: false,

    // When this flag true, you can BYPASS maintenance pages that are currently present.
    // See docs/portal/maintenance-pages.md for more details.
    noMaintenance: false,

    // When this flag is enabled, the user can see the site.
    // To immediately hide the site from people who previously overrode this
    // flag in a cookie, you can rename this flag to something else (and also
    // update the reference to it in _app.js), but try to keep it prefixed with pfml.
    // https://lwd.atlassian.net/browse/CP-459
    pfmlTerriyay: false,

    // When this flag is enabled, the user can apply to take leave to
    // "Care for a family member with a serious health condition" and
    // Leave Admins can review Caring Leave claims
    // TODO (CP-2311): Remove showCaringLeaveType flag once caring leave is made available in Production
    showCaringLeaveType: true,

    // When this flag is enabled, the medical leave question numbers for leave periods
    // are updated to reflect the new "Certification of Your Serious Health Condition"
    // TODO (CP-2205): Remove this flag once updated medical leave form is effective
    updateMedicalCertForm: false,

    // When this flag is enabled, the document upload and listing/download features will use
    // the new plan proofs in FINEOS, expected to roll out on 6/25
    // TODO (CP-2306): Remove or disable this feature flag to coincide with FINEOS 6/25 udpate
    useNewPlanProofs: true,
  },
  // Environments can optionally override a default feature flag below.
  // The environment keys should use the same envName defined in
  // environment config files.
  "cps-preview": {
    employerShowDashboardFilters: true,
  },
  development: {
    example: true,
    employerShowDashboardFilters: true,
    pfmlTerriyay: true,
  },
  test: {
    employerShowDashboardFilters: true,
  },
  stage: { employerShowDashboardFilters: true },
  training: { employerShowDashboardFilters: true },
  performance: { employerShowDashboardFilters: true },
  uat: { employerShowDashboardFilters: true },
  prod: { employerShowDashboardFilters: true, pfmlTerriyay: true },
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
