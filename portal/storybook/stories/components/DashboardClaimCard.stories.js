import Claim from "src/models/Claim";
import DashboardClaimCard from "src/components/DashboardClaimCard";
import React from "react";

export default {
  title: "Components/DashboardClaimCard",
  component: DashboardClaimCard,
};

export const Default = () => (
  <DashboardClaimCard
    claim={
      new Claim({
        application_id: "mock-claim-id",
      })
    }
    number={1}
  />
);
