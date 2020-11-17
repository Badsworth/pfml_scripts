import React from "react";
import UserFeedback from "src/components/UserFeedback";
import routes from "src/routes";

export default {
  title: "Components/UserFeedback",
  component: UserFeedback,
};

export const Default = () => {
  return <UserFeedback url={routes.external.massgov.feedbackClaimant} />;
};
