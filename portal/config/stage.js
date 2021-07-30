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
  maintenancePageRoutes: ["/*"],
  maintenanceStart: "2021-08-08T03:59:00-04:00",
  maintenanceEnd: "2021-08-08T05:00:00-04:00",
};
