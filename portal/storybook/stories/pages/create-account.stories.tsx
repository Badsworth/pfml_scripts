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

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ auth: { createAccount: () => void; }; appE... Remove this comment to see the full error message
  return <CreateAccount appLogic={appLogic} />;
};
