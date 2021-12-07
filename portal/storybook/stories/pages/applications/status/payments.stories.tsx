import { Payments } from "src/pages/applications/status/payments";
import { Props } from "storybook/types";
import React from "react";
import User from "src/models/User";
// TODO (PORTAL-1148) Update to use createMockClaim instead of createMockBenefitsApplication when ready
import { createMockBenefitsApplication } from "tests/test-utils/createMockBenefitsApplication";
import { createMockPayment } from "tests/test-utils/createMockPayment";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const LEAVE_TYPES = {
  continuous: "Continuous",
  continuousReduced: "Continuous with reduced schedule",
  intermittent: "Intermittent",
  reduced: "Reduced schedule",
};

export default {
  title: "Pages/Applications/Status/Payments",
  component: Payments,
  args: {
    "Leave type": LEAVE_TYPES.continuous,
  },
  argTypes: {
    "Leave type": {
      control: {
        type: "radio",
        options: [
          LEAVE_TYPES.continuous,
          LEAVE_TYPES.continuousReduced,
          LEAVE_TYPES.intermittent,
          LEAVE_TYPES.reduced,
        ],
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Payments> & {
    "Leave type": keyof typeof LEAVE_TYPES;
  }
) => {
  // Claim type is selected control
  // TODO (PORTAL-1148) Update to use createMockClaim instead of createMockBenefitsApplication when ready
  const claimType = {
    [LEAVE_TYPES.continuous]: createMockBenefitsApplication("continuous"),
    [LEAVE_TYPES.continuousReduced]: createMockBenefitsApplication(
      "continuous",
      "reducedSchedule"
    ),
    [LEAVE_TYPES.intermittent]: createMockBenefitsApplication("intermittent"),
    [LEAVE_TYPES.reduced]: createMockBenefitsApplication("reducedSchedule"),
  }[args["Leave type"]];

  const appLogic = useMockableAppLogic({
    claims: {
      ...claimType,
      claimDetail: {
        absence_periods: [
          {
            absence_period_start_date: "2021-10-23",
            absence_period_end_date: "2021-11-30",
            fineos_leave_request_id: "fineos_id",
            period_type: "Continuous",
            reason: "Child Bonding",
            reason_qualifier_one: "Bonding",
            reason_qualifier_two: "",
            request_decision: "Approved",
          },
        ],
        payments: [
          createMockPayment({
            payment_method: "Elec Funds Transfer",
            status: "Sent to bank",
          }),
          createMockPayment({
            sent_to_bank_date: null,
            payment_method: "Check",
            status: "Pending",
          }),
          createMockPayment({
            sent_to_bank_date: null,
            payment_method: "Check",
            status: "Delayed",
          }),
          createMockPayment({
            sent_to_bank_date: null,
            payment_method: "Check",
            status: "Cancelled",
          }),
        ],
      },
      isLoadingClaimDetail: false,
    },
  });

  return (
    <Payments
      appLogic={appLogic}
      query={{ absence_id: "mock-absence-case-id" }}
      user={new User({})}
    />
  );
};
