/**
 * Stage environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  // Not finding what you're looking for? Check default.js
  envName: "stage",
  domain: "paidleave-stage.mass.gov",
  newRelicAppId: "847043861",
  // See docs/portal/maintenance-pages.md
  maintenancePageRoutes: ["/*"], // required
  maintenanceStart: "2021-06-06T03:59:00-04:00", // optional ISO 8601 datetime
  maintenanceEnd: "2021-06-06T05:00:00-04:00", // optional ISO 8601 datetime
};
