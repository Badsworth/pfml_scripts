import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import CreateAccount from "src/pages/employers/create-account";
import React from "react";

export default {
  title: "Pages/Employers/Auth/Create Account",
  component: CreateAccount,
};

export const Default = () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    auth: {
      createEmployerAccount: () => {},
    },
    portalFlow: { goTo: () => {} },
  };
  return <CreateAccount appLogic={appLogic} />;
};
