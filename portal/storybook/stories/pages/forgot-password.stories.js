import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import ForgotPassword from "src/pages/forgot-password";
import React from "react";

export default {
  title: "Pages/Auth/Forgot Password",
  component: ForgotPassword,
};

export const Page = () => {
  const appLogic = {
    auth: { forgotPassword: () => {} },
    appErrors: new AppErrorInfoCollection(),
  };

  return <ForgotPassword appLogic={appLogic} />;
};
