import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import CreateAccount from "src/pages/create-account";
import React from "react";

export default {
  title: "Pages/Auth/Create Account",
  component: CreateAccount,
};

export const Page = () => {
  const appLogic = {
    auth: { createAccount: () => {} },
    appErrors: new AppErrorInfoCollection(),
    portalFlow: { goTo: () => {} },
  };

  return <CreateAccount appLogic={appLogic} />;
};
