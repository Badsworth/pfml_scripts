import ForgotPassword from "src/pages/forgot-password";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Forgot Password",
  component: ForgotPassword,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();

  return <ForgotPassword appLogic={appLogic} />;
};
