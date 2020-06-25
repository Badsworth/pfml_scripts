import ApplicationCard from "src/components/ApplicationCard";
import Claim from "src/models/Claim";
import LeaveReason from "src/models/LeaveReason";
import React from "react";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
};

export const Default = () => (
  <ApplicationCard
    claim={
      new Claim({
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
        },
      })
    }
    number={1}
  />
);

export const EmptyClaim = () => (
  <ApplicationCard
    claim={
      new Claim({
        application_id: "mock-claim-id",
      })
    }
    number={1}
  />
);
