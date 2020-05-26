import Claim from "../models/Claim";
import DashboardClaimCard from "./DashboardClaimCard";
import React from "react";

export default {
  title: "Screens/Dashboard/DashboardClaimCard",
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
