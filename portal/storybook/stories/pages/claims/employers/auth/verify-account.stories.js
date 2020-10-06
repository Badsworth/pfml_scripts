import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "src/pages/employers/verify-account";

export default {
  title: "Pages/Employers/Auth/Verify Account",
  component: VerifyAccount,
};

export const Default = () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
  };
  return <VerifyAccount appLogic={appLogic} />;
};
