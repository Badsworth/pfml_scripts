import Lead from "./Lead";
import React from "react";

export default {
  title: "Components|Lead",
  component: Lead,
};

export const Default = () => (
  <Lead>
    Before you create a claim, we need to verify that you have earned at least
    $5,100 in the past twelve months.
  </Lead>
);

export const Multiple = () => (
  <React.Fragment>
    <Lead>
      According to our records, you’ve worked for 2 Massachusetts employers and
      have earned at least $5,100 in the past twelve months. You can create a
      claim.
    </Lead>

    <Lead>
      Please review the employment information in the table below to confirm.
    </Lead>
  </React.Fragment>
);
