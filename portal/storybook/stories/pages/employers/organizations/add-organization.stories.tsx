import { AddOrganization } from "src/pages/employers/organizations/add-organization";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";

export default {
  title: "Pages/Employers/Organizations/Add Organization",
  component: AddOrganization,
};

export const Default = () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    portalFlow: {
      goTo: () => {},
    },
    employers: {
      addEmployer: () => {},
    },
  };
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; portalF... Remove this comment to see the full error message
  return <AddOrganization appLogic={appLogic} />;
};
