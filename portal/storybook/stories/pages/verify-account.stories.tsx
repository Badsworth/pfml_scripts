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
  const authData = {};

  if (args.scenario === "Claimant post-signup") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'createAccountUsername' does not exist on... Remove this comment to see the full error message
    authData.createAccountUsername = "me-claimant@gmail.com";
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'createAccountFlow' does not exist on typ... Remove this comment to see the full error message
    authData.createAccountFlow = "claimant";
  } else if (args.scenario === "Employer post-signup") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'createAccountUsername' does not exist on... Remove this comment to see the full error message
    authData.createAccountUsername = "me-employer@acme.com";
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'createAccountFlow' does not exist on typ... Remove this comment to see the full error message
    authData.createAccountFlow = "employer";
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'employerIdNumber' does not exist on type... Remove this comment to see the full error message
    authData.employerIdNumber = "12-3456789";
  }

  const appLogic = useMockableAppLogic({
    auth: { authData },
  });

  return <VerifyAccount appLogic={appLogic} />;
};
