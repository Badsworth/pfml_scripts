import { AddOrganization } from "src/pages/employers/organizations/add-organization";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";

export default {
  title: "Pages/Employers/Organizations/Add Organization",
  component: AddOrganization,
};

export const Default = () => {
  const appLogic = {
    portalFlow: {
      appErrors: new AppErrorInfoCollection(),
      goTo: () => {},
    },
  };
  return <AddOrganization appLogic={appLogic} />;
};
