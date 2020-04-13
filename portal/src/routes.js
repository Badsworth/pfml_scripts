/**
 * @file Routes to various pages in the application are defined here rather than being
 * hard-coded into various files.
 */

const routes = {
  home: "/",
  claims: {
    dateOfBirth: "/claims/date-of-birth",
    name: "/claims/name",
    ssn: "/claims/ssn",
    stateId: "/claims/state-id",
  },
};

export default routes;
