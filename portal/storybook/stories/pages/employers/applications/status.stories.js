import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import { Status } from "src/pages/employers/applications/status";

export default {
  title: "Pages/Employers/Applications/Status",
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
  let claim = new MockEmployerClaimBuilder().bondingLeaveReason();

  if (retrievedClaim === "Continuous") {
    claim = claim.continuous().create();
  } else if (retrievedClaim === "Intermittent leave") {
    claim = claim.intermittent().create();
  } else if (retrievedClaim === "Reduced schedule") {
    claim = claim.reducedSchedule().create();
  } else if (retrievedClaim === "Hybrid leave") {
    claim = claim.completed().create();
  }

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim,
      load: () => {},
    },
    setAppErrors: () => {},
  };

  const query = { absence_id: "mock-absence-id" };

  return <Status appLogic={appLogic} query={query} retrievedClaim={claim} />;
};
