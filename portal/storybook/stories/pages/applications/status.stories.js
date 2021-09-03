import ClaimDetail, { AbsencePeriod } from "src/models/ClaimDetail";
import { Status, StatusTagMap } from "src/pages/applications/status";
import LeaveReason from "src/models/LeaveReason";
import React from "react";
import { ReasonQualifier } from "src/models/BenefitsApplication";
import faker from "faker";
import { generateClaim } from "tests/test-utils";
import { merge } from "lodash";

/**
 * Maps each of the leave scenario options to a list of partial absence periods.
 */
const LEAVE_SCENARIO_MAP = {
  "Medical-Pregnancy and Bonding": [
    { reason: LeaveReason.pregnancy },
    { reason: LeaveReason.bonding, reason_qualifier_one: "Newborn" },
  ],
  "Medical-Pregnancy": [{ reason: LeaveReason.pregnancy }],
  "Bonding-newborn": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.newBorn,
    },
  ],
  "Bonding-adoption/foster": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.fosterCare,
    },
  ],
  "Medical leave due to illness": [{ reason: LeaveReason.medical }],
  "Caring leave": [{ reason: LeaveReason.care }],
};

/**
 * Creates the claim detail to be used by the Status component.
 * Ensures that all permutations of leave reason and request decision are displayed.
 * @param {string} leaveScenarioSelection - the selected radio option for the
 *    leave scenario in Storybook.
 * @returns {ClaimDetail} a populated ClaimDetail object that contains
 *    absence periods applicable to the provided leave scenario selection.
 */
function createClaimDetail(leaveScenarioSelection) {
  const initialPartials = LEAVE_SCENARIO_MAP[leaveScenarioSelection] || [];
  // ensure that we see all request decisions.
  const allPartials = initialPartials.flatMap((initialPartial) => [
    merge({ request_decision: "Approved" }, initialPartial),
    merge({ request_decision: "Denied" }, initialPartial),
    merge({ request_decision: "Pending" }, initialPartial),
    merge({ request_decision: "Withdrawn" }, initialPartial),
  ]);

  const absence_periods = allPartials.map((partial) =>
    createAbsencePeriod(partial)
  );
  return new ClaimDetail({
    application_id: "my-application-id",
    employer: {
      employer_fein: "123456789",
    },
    absence_periods,
  });
}

/**
 * Create an absence period for use in testing. Any attributes that are not passed
 * in will have a random, faked value provided.
 * @returns {AbsencePeriod} - a filled absence period
 */
function createAbsencePeriod(partialAttrs) {
  const defaultAbsencePeriod = {
    absence_period_end_date: "2021-09-04",
    absence_period_start_date: "2021-04-09",
    fineos_leave_request_id: faker.datatype.uuid(),
    period_type: faker.random.arrayElement(["Continuous", "Reduced"]),
    request_decision: faker.random.arrayElement(Object.keys(StatusTagMap)),
  };

  return new AbsencePeriod(merge(defaultAbsencePeriod, partialAttrs));
}

export default {
  title: `Pages/Applications/Status`,
  component: Status,
  argTypes: {
    "Leave Scenario": {
      defaultValue: "Medical-Pregnancy and Bonding",
      control: {
        type: "radio",
        options: Object.keys(LEAVE_SCENARIO_MAP),
      },
    },
  },
};

export const DefaultStory = (args) => {
  const leaveScenario = args["Leave Scenario"];
  const claimDetail = createClaimDetail(leaveScenario);
  const appLogic = {
    appErrors: { items: [] },
    claims: {
      claimDetail,
      isLoadingClaimDetail: false,
      loadClaimDetail: () => {},
    },
    documents: { download: () => {} },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
      goTo: () => {},
    },
  };

  // Leave reason based on leave scenario control
  const leaveReason = {
    "Medical-Pregnancy and Bonding": "bonding",
    "Medical-Pregnancy": "pregnancy",
    "Bonding-newborn": "bonding",
    "Bonding-adoption/foster": "bonding",
    "Medical leave due to illness": "medical",
    "Caring leave": "caring",
  }[leaveScenario];

  const claim = generateClaim("completed", leaveReason);
  return (
    <Status
      appLogic={appLogic}
      claim={claim}
      query={{ absence_case_id: "NTN-12345-ABS-01" }}
    />
  );
};
