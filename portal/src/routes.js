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
    success: "/claims/success",
    // For routes that don't have a page to point to yet, we can route them
    // to a placeholder page. This allows us to search our code for routes.claims.todo,
    // which is less confusing than seeing routes.claims.success
    todo: "/claims/success",
  },
};

export default routes;
