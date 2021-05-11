import { MockClaimBuilder } from "tests/test-utils";

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
  "Other incomes": {
    defaultValue: "None",
    control: {
      type: "radio",
      options: ["None", "Unemployment income"],
    },
  },
  "Previous leave": {
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
  let claim = new MockClaimBuilder();

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

  switch (args["Other incomes"]) {
    case "Unemployment income":
      claim = claim.otherIncomeFromUnemployment();
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
