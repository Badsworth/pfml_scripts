import CreateAccount from "src/pages/create-account";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Create worker account",
  component: CreateAccount,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();

  return <CreateAccount appLogic={appLogic} />;
};
