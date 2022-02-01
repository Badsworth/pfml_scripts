import { AbsencePeriodRequestDecision } from "src/models/AbsencePeriod";
import AbsencePeriodStatusTag from "src/components/AbsencePeriodStatusTag";
import React from "react";

export default {
  title: "Components/AbsencePeriodStatusTag",
  component: AbsencePeriodStatusTag,
};

export const Default = () => {
  const decisions = Object.values(AbsencePeriodRequestDecision);

  return (
    <React.Fragment>
      {decisions.map((decision) => (
        <p key={decision}>
          {decision}
          <br />
          <AbsencePeriodStatusTag request_decision={decision} />
        </p>
      ))}
    </React.Fragment>
  );
};
