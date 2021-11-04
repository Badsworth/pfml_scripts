import React from "react";
import { SetupSMS } from "src/pages/two-factor/sms/index";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Index",
  component: SetupSMS,
};

export const Page = (args) => {
  const appLogic = {};
  return <SetupSMS appLogic={appLogic} />;
};

Page.argTypes = {};
