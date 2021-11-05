import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import ResetPassword from "src/pages/reset-password";

export default {
  title: "Pages/Auth/Reset Password",
  component: ResetPassword,
  argTypes: {
    scenario: {
      defaultValue: "With cached email",
      control: {
        type: "radio",
        options: ["With cached email", "Without cached email"],
      },
    },
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Page = (args) => {
  const authData = {};

  if (args.scenario === "With cached email") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'resetPasswordUsername' does not exist on... Remove this comment to see the full error message
    authData.resetPasswordUsername = "test@example.com";
  }

  const appLogic = {
    auth: {
      authData,
      resetPassword: () => {},
      resendForgotPasswordCode: () => {},
    },
    appErrors: new AppErrorInfoCollection(),
  };

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ auth: { authData: {}; resetPassword: () =>... Remove this comment to see the full error message
  return <ResetPassword appLogic={appLogic} />;
};
