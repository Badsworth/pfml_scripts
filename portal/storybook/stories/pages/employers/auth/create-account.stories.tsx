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
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; auth: {... Remove this comment to see the full error message
  return <CreateAccount appLogic={appLogic} />;
};
