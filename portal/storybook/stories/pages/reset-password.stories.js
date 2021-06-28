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

export const Page = (args) => {
  const authData = {};

  if (args.scenario === "With cached email") {
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

  return <ResetPassword appLogic={appLogic} />;
};
