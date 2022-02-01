import CreateAccount from "src/pages/employers/create-account";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Create employer account",
  component: CreateAccount,
};

export const Default = () => {
  const appLogic = useMockableAppLogic();

  return <CreateAccount appLogic={appLogic} />;
};
