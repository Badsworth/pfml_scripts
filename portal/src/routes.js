/**
 * @file Routes to various pages in the application are defined here rather than being
 * hard-coded into various files.
 */
const routes = {
  home: "/",
  claims: {
    dateOfBirth: "/claims/date-of-birth",
    duration: "/claims/duration",
    leaveDates: "/claims/leave-dates",
    leaveType: "/claims/leave-type",
    name: "/claims/name",
    notifiedEmployer: "/claims/notified-employer",
    ssn: "/claims/ssn",
    stateId: "/claims/state-id",
  },
};

export default routes;
