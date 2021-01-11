import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyBusiness from "src/pages/employers/verify-business";

export default {
  title: "Pages/Employers/Auth/Verify Business",
  component: VerifyBusiness,
};

export const Default = () => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
  };
  return <VerifyBusiness appLogic={appLogic} />;
};
