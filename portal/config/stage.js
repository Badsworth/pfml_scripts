/**
 * Stage environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  // Not finding what you're looking for? Check default.js
  envName: "stage",
  domain: "paidleave-stage.mass.gov",
  // See docs/portal/maintenance-pages.md
  maintenancePageRoutes: ["/*"], // required
  maintenanceStart: "2021-03-27T00:00:00-04:00",
  // maintenanceEnd: null, // optional ISO 8601 datetime
  newRelicAppId: "847043861",
};
