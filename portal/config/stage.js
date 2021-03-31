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
  maintenancePageRoutes: ["/*"], // required
  maintenanceStart: "2021-03-31T23:59:00-04:00", // optional ISO 8601 datetime
  maintenanceEnd: "2021-04-01T05:00:00-04:00", // optional ISO 8601 datetime
};
