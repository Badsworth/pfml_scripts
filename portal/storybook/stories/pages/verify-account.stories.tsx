import { Props } from "storybook/types";
import React from "react";
import VerifyAccount from "src/pages/verify-account";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

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

export const Page = (
  args: Props<typeof VerifyAccount> & { scenario: string }
) => {
  const authData: { [key: string]: string } = {};

  if (args.scenario === "Claimant post-signup") {
    authData.createAccountUsername = "me-claimant@gmail.com";
    authData.createAccountFlow = "claimant";
  } else if (args.scenario === "Employer post-signup") {
    authData.createAccountUsername = "me-employer@acme.com";
    authData.createAccountFlow = "employer";
    authData.employerIdNumber = "12-3456789";
  }

  const appLogic = useMockableAppLogic({
    auth: { authData },
  });

  return <VerifyAccount appLogic={appLogic} />;
};
