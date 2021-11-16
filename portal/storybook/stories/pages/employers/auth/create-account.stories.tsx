import CreateAccount from "src/pages/employers/create-account";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Auth/Create Account",
  component: CreateAccount,
};

export const Default = () => {
  const appLogic = useMockableAppLogic();

  return <CreateAccount appLogic={appLogic} />;
};
