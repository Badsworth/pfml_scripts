import Step from "../models/Step";
import StepDefinition from "../models/StepDefinition";

import { fields as durationFields } from "../pages/claims/duration";
import { fields as leaveDatesFields } from "../pages/claims/leave-dates";
import { fields as leaveReasonFields } from "../pages/claims/leave-reason";
import { fields as nameFields } from "../pages/claims/name";
import { fields as notifiedEmployerFields } from "../pages/claims/notified-employer";
import routes from "../routes";
import { fields as ssnFields } from "../pages/claims/ssn";

const verifyId = new StepDefinition({
  name: "verifyId",
  pages: [
    {
      route: routes.claims.name,
      fields: nameFields,
    },
    {
      route: routes.claims.ssn,
      fields: ssnFields,
    },
    // TODO: handle state-id and date-of-birth fields?
    // TODO: add upload doc pages
  ],
});

const leaveDetails = new StepDefinition({
  name: "leaveDetails",
  dependsOn: [verifyId],
  pages: [
    {
      route: routes.claims.leaveReason,
      fields: leaveReasonFields,
    },
    {
      route: routes.claims.leaveDates,
      fields: leaveDatesFields,
    },
    {
      route: routes.claims.duration,
      fields: durationFields,
    },
  ],
});

const employerInformation = new StepDefinition({
  name: "employerInformation",
  dependsOn: [verifyId, leaveDetails],
  pages: [
    {
      route: routes.claims.notifiedEmployer,
      fields: notifiedEmployerFields,
    },
  ],
});

const otherLeave = new StepDefinition({
  name: "otherLeave",
  dependsOn: [verifyId, leaveDetails],
});

const payment = new StepDefinition({
  name: "payment",
  dependsOn: [verifyId, leaveDetails],
});

export const stepDefinitions = [
  verifyId,
  leaveDetails,
  employerInformation,
  otherLeave,
  payment,
];

export const createSteps = (claim, warnings) => {
  return Step.createStepsFromDefinitions(stepDefinitions, claim, warnings);
};
