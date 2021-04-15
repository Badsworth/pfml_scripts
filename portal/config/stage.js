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
  maintenanceStart: "2021-04-16T19:59:00-04:00", // optional ISO 8601 datetime
};
