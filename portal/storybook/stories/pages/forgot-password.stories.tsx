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

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ auth: { forgotPassword: () => void; }; app... Remove this comment to see the full error message
  return <ForgotPassword appLogic={appLogic} />;
};
