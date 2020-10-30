import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockClaimBuilder } from "tests/test-utils";
import React from "react";
import { Status } from "src/pages/employers/claims/status";

export default {
  title: "Pages/Employers/Claims/Status",
  component: Status,
  argTypes: {
    retrievedClaim: {
      defaultValue: "Continuous",
      control: {
        type: "radio",
        options: [
          "Continuous",
          "Intermittent leave",
          "Reduced schedule",
          "Hybrid leave",
        ],
      },
    },
  },
};

export const Default = ({ retrievedClaim }) => {
  let claim = new MockClaimBuilder().verifiedId().bondingBirthLeaveReason();

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim,
      load: () => {},
    },
    setAppErrors: () => {},
  };

  if (retrievedClaim === "Continuous") {
    claim = claim.continuous().create();
  } else if (retrievedClaim === "Intermittent leave") {
    claim = claim.intermittent().create();
  } else if (retrievedClaim === "Reduced schedule") {
    claim = claim.reducedSchedule().create();
  } else if (retrievedClaim === "Hybrid leave") {
    claim = claim.continuous().reducedSchedule().create();
  }

  const query = { absence_id: "mock-absence-id" };

  return <Status appLogic={appLogic} query={query} retrievedClaim={claim} />;
};
