import React from "react";
import { Success } from "src/pages/employers/applications/success";

export default {
  title: `Pages/Employers/Applications/Success`,
  component: Success,
};

export const Default = () => {
  const query = {
    absence_id: "NTN-111-ABS-01",
  };
  const appLogic = {
    portalFlow: {
      getNextPageRoute: () => {},
    },
  };
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ portalFlow: { getNextPageRoute: () => void... Remove this comment to see the full error message
  return <Success query={query} appLogic={appLogic} />;
};
