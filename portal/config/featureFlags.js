/**
 * Feature flags. A feature flag can be enabled/disabled at the environment level.
 * Its value will either be true or false. Environments can override this value.
 * @see ../../docs/portal/feature-flags.md
 */
const flagsConfig = {
  // Define a default or all feature flags here.
  // Environments will fallback to these default values.
  defaults: {
    // When this flag is enabled, claimant login and account creation options
    // are visible and content reflects workers can apply for leave.
    // TODO (CP-1407): Enable claimant auth once Portal is open for claims
    claimantShowAuth: false,

    // When this flag is enabled, the user can see the "Employment status"
    // question in the claimant flow (CP-1204)
    // TODO (CP-1281): Show employment status question when Portal supports other employment statuses
    claimantShowEmploymentStatus: false,

    // When this flag is enabled, claimant can see the leave types available to them on Jan 1.
    // TODO (CP-1496): Show Jan 1 application instructions when portal supports
    // bonding pre/post birth/placement and medical leave
    claimantShowJan1ApplicationInstructions: false,

    // When this flag is enabled, the medical leave option is selectable on
    // the Leave Reason page in the claimant flow (CP-1245)
    // TODO (CP-1246): Show this option when portal supports medical leave
    claimantShowMedicalLeaveType: false,

    // When this flag is enabled, the military leave options are selectable on
    // the Leave Reason page in the claimant flow (CP-1145)
    // TODO (CP-534): Show all options when portal supports activeDutyFamily, serviceMemberFamily
    claimantShowMilitaryLeaveTypes: false,

    // When this flag is enabled, the user can see the "Have you taken paid or unpaid leave since January 1,
    // 2021 for a qualifying reason?" question.
    // TODO (CP-1247): Show previous leaves related questions
    claimantShowPreviousLeaves: false,

    // Hide the entire "Other leave, income, and benefits" step of the Claim flow.
    // TODO (CP-1346): Show this step once it's been integrated w/ the API.
    claimantShowOtherLeaveStep: false,

    // When this flag is enabled, adjudication status is visible on the Status page
    // TODO (EMPLOYER-656): Show adjudication status once it is retrieved from FINEOS
    employerShowAdjudicationStatus: false,

    // When this flag is enabled, the "Previous leaves" section on Review page is visible
    // TODO (EMPLOYER-657): Show this section after 1/1
    employerShowPreviousLeaves: false,

    // When this flag is enabled, the user can see the site.
    // To immediately hide the site from people who previously overrode this
    // flag in a cookie, you can rename this flag to something else (and also
    // update the reference to it in _app.js), but try to keep it prefixed with pfml.
    // https://lwd.atlassian.net/browse/CP-459
    pfmlTerriyay: false,
  },
  // Environments can optionally override a default feature flag below.
  // The environment keys should use the same envName defined in
  // environment config files.
  development: {
    example: true,
    pfmlTerriyay: true,
    claimantShowAuth: true,
  },
  test: {
    claimantShowAuth: true,
  },
  stage: {
    claimantShowAuth: true,
  },
  training: {
    claimantShowAuth: true,
  },
  performance: {
    claimantShowAuth: true,
  },
  prod: {
    pfmlTerriyay: true,
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
