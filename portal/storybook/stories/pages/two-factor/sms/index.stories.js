import React from "react";
import { SetupMFA } from "src/pages/two-factor/sms/index";

export default {
  title: "Pages/Auth/Two-Factor/SMS",
  component: SetupMFA,
};

export const Page = (args) => {
  const appLogic = {};
  return <SetupMFA appLogic={appLogic} />;
};

Page.argTypes = {};
