import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "src/pages/verify-account";

export default {
  title: "Pages/Auth/Verify Account",
  component: VerifyAccount,
};

export const Page = (args) => {
  const authData = {};

  if (args.scenario === "After signup") {
    authData.createAccountUsername = "test@example.com";
  }

  const appLogic = {
    auth: { authData },
    appErrors: new AppErrorInfoCollection(),
  };

  return <VerifyAccount appLogic={appLogic} />;
};

Page.argTypes = {
  scenario: {
    defaultValue: "After signup",
    control: {
      type: "radio",
      options: ["After signup", "After page refresh"],
    },
  },
};
