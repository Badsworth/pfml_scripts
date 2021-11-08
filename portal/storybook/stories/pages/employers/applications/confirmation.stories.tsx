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
      loadClaim: () => {},
    },
    portalFlow: {
      goToNextPage: () => {},
      goToPageFor: () => {},
    },
    setAppErrors: () => {},
  };
  return (
    <Confirmation
      query={query}
      // @ts-expect-error ts-migrate(2322) FIXME: Type '{ query: { absence_id: string; follow_up_dat... Remove this comment to see the full error message
      appLogic={appLogic}
      claim={new MockEmployerClaimBuilder()
        .completed()
        .reviewable(true)
        .create()}
    />
  );
};
