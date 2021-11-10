import { AddOrganization } from "src/pages/employers/organizations/add-organization";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Organizations/Add Organization",
  component: AddOrganization,
};

export const Default = () => {
  const appLogic = useMockableAppLogic();

  return <AddOrganization appLogic={appLogic} />;
};
