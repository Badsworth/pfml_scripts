import Claim, { ClaimStatus, LeaveReason } from "src/models/Claim";
import ApplicationCard from "src/components/ApplicationCard";
import React from "react";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
};

export const InProgressClaim = () => {
  const claim = new Claim({
    application_id: "mock-claim-id",
    employer_fein: "00-0000000",
    leave_details: {
      continuous_leave_periods: [
        {
          end_date: "2021-12-30",
          start_date: "2021-09-21",
        },
      ],
      employer_notified: true,
      reason: LeaveReason.medical,
      status: ClaimStatus.started,
    },
  });

  return <ApplicationCard claim={claim} number={1} />;
};

export const EmptyClaim = () => (
  <ApplicationCard
    claim={
      new Claim({
        application_id: "mock-claim-id",
        status: ClaimStatus.started,
      })
    }
    number={1}
  />
);

export const CompletedClaim = () => {
  const claim = new Claim({
    application_id: "mock-claim-id",
    employer_fein: "00-0000000",
    leave_details: {
      continuous_leave_periods: [
        {
          end_date: "2021-12-30",
          start_date: "2021-09-21",
        },
      ],
      employer_notified: true,
      reason: LeaveReason.medical,
      status: ClaimStatus.completed,
    },
  });

  return <ApplicationCard claim={claim} number={1} />;
};
