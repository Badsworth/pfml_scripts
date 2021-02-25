import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { Confirmation } from "src/pages/employers/applications/confirmation";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: "Pages/Employers/Applications/Confirmation",
  component: Confirmation,
};

export const Default = () => {
  const query = {
    absence_id: "NTN-1315-ABS-01",
    follow_up_date: "2022-01-01",
  };
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim: new MockEmployerClaimBuilder()
        .completed()
        .reviewable(true)
        .create(),
      loadClaim: () => {},
    },
    portalFlow: {
      goToNextPage: () => {},
      goToPageFor: () => {},
    },
    setAppErrors: () => {},
  };
  return <Confirmation query={query} appLogic={appLogic} />;
};
