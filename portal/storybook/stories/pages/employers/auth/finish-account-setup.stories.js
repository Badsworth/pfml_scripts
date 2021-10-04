import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import FinishAccountSetup from "src/pages/employers/finish-account-setup";
import React from "react";

export default {
  title: "Pages/Employers/Auth/Finish Account Setup",
  component: FinishAccountSetup,
};

export const Default = () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
  };
  return <FinishAccountSetup appLogic={appLogic} />;
};
