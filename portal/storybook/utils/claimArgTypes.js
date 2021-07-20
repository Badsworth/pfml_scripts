import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import { PreviousLeaveReason } from "src/models/PreviousLeave";

/**
 * Storybook argTypes providing granular controls for
 * different aspects of an Application
 */
export const claimArgTypes = {
  Status: {
    defaultValue: "Part 1 not submitted",
    control: {
      type: "radio",
      options: ["Part 1 not submitted", "Part 1 and 2 are submitted"],
    },
  },
  "Has state ID": {
    defaultValue: true,
    control: {
      type: "boolean",
    },
  },
  "Employer notified": {
    defaultValue: true,
    control: {
      type: "boolean",
    },
  },
  "Work pattern": {
    defaultValue: "fixed",
    control: {
      type: "radio",
      options: ["fixed", "variable"],
    },
  },
  "Leave reason": {
    defaultValue: "Medical",
    control: {
      type: "radio",
      options: [
        "Medical",
        "Family - Birth",
        "Family - Adoption",
        "Family - Foster care",
        "Caring",
        "Pregnancy",
      ],
    },
  },
  "Leave period": {
    defaultValue: "continuous",
    control: {
      type: "radio",
      options: ["continuous", "reduced", "intermittent", "hybrid"],
    },
  },
  "Previous leaves same reason": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: ["None", "From current employer", "From other employer"],
    },
  },
  "Previous leaves other reason": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: [
        "None",
        "Medical leave from current employer",
        "Pregnancy leave from other employer",
      ],
    },
  },

  "Concurrent leave": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: ["None", "From current employer"],
    },
  },
  "Employer-sponsored benefit": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: ["None", "Yes (array)"],
    },
  },
  "Other income": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: ["None", "From other employer"],
    },
  },
  Payment: {
    defaultValue: "Deposit",
    control: {
      type: "radio",
      options: ["Deposit", "Check"],
    },
  },
};

/**
 * Create a claim using the args passed into a Story. The args
 * are based on the claimArgTypes.
 * @param {object} args
 * @returns {BenefitsApplication}
 */
export function createClaimFromArgs(args) {
  let claim = new MockBenefitsApplicationBuilder();

  if (args.Status === "Part 1 and 2 are submitted") {
    claim = claim.submitted();
  }

  // Set defaults for aspects of a claim that will always be present.
  // These can be overridden by custom args below.
  claim = claim.verifiedId().employed();

  if (args["Has state ID"]) {
    claim = claim.hasStateId();
  } else {
    claim = claim.hasOtherId();
  }

  if (args["Employer notified"]) {
    claim = claim.notifiedEmployer();
  } else {
    claim = claim.notNotifiedEmployer();
  }

  if (args["Work pattern"] === "fixed") {
    claim = claim.fixedWorkPattern();
  } else {
    claim = claim.variableWorkPattern();
  }

  switch (args["Leave reason"]) {
    case "Medical":
      claim = claim.medicalLeaveReason();
      break;
    case "Family - Birth":
      claim = claim.bondingBirthLeaveReason();
      break;
    case "Family - Adoption":
      claim = claim.bondingAdoptionLeaveReason();
      break;
    case "Family - Foster care":
      claim = claim.bondingFosterCareLeaveReason();
      break;
    case "Caring":
      claim.caringLeaveReason();
      break;
    case "Pregnancy":
      claim.pregnancyLeaveReason();
      break;
  }

  switch (args["Leave period"]) {
    case "continuous":
      claim = claim.continuous();
      break;
    case "reduced":
      claim = claim.reducedSchedule();
      break;
    case "intermittent":
      claim = claim.intermittent();
      break;
    case "hybrid":
      claim = claim.continuous().reducedSchedule();
      break;
  }

  switch (args["Previous leaves same reason"]) {
    case "From current employer":
      claim = claim.previousLeavesSameReason([
        {
          is_for_current_employer: true,
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-07-01",
          leave_minutes: 5000,
          worked_per_week_minutes: 10000,
        },
      ]);
      break;
    case "From other employer":
      claim = claim.previousLeavesSameReason([
        {
          is_for_current_employer: false,
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-07-01",
          leave_minutes: 5000,
          worked_per_week_minutes: 10000,
        },
      ]);
      break;
  }

  switch (args["Previous leaves other reason"]) {
    case "Medical leave from current employer":
      claim = claim.previousLeavesOtherReason([
        {
          is_for_current_employer: true,
          leave_reason: PreviousLeaveReason.medical,
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-07-01",
          leave_minutes: 5000,
          worked_per_week_minutes: 10000,
        },
      ]);
      break;
    case "Pregnancy leave from other employer":
      claim = claim.previousLeavesOtherReason([
        {
          is_for_current_employer: false,
          leave_reason: PreviousLeaveReason.pregnancy,
          leave_start_date: "2021-05-01",
          leave_end_date: "2021-07-01",
          leave_minutes: 5000,
          worked_per_week_minutes: 10000,
        },
      ]);
      break;
  }

  switch (args["Concurrent leave"]) {
    case "From current employer":
      claim = claim.concurrentLeave();
      break;
  }

  switch (args["Employer-sponsored benefit"]) {
    case "Yes (array)":
      claim = claim.employerBenefit();
      break;
  }

  switch (args["Other income"]) {
    case "From other employer":
      claim = claim.otherIncome();
      break;
    default:
      claim = claim.noOtherIncomes();
      break;
  }

  if (args.Payment === "deposit") {
    claim = claim.directDeposit();
  } else {
    claim = claim.check();
  }

  return claim.create();
}
