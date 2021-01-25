import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "src/pages/verify-account";

export default {
  title: "Pages/Auth/Verify Account",
  component: VerifyAccount,
  argTypes: {
    scenario: {
      defaultValue: "Claimant post-signup",
      control: {
        type: "radio",
        options: [
          "Claimant post-signup",
          "Employer post-signup",
          "After page reload",
        ],
      },
    },
  },
};

export const Page = (args) => {
  const authData = {};
  const query = {};

  if (args.scenario === "Claimant post-signup") {
    authData.createAccountUsername = "me-claimant@gmail.com";
    authData.createAccountFlow = "claimant";
  } else if (args.scenario === "Employer post-signup") {
    authData.createAccountUsername = "me-employer@acme.com";
    authData.createAccountFlow = "employer";
    authData.employerIdNumber = "12-3456789";
  }

  const appLogic = {
    auth: { authData },
    appErrors: new AppErrorInfoCollection(),
  };

  return <VerifyAccount appLogic={appLogic} query={query} />;
};
