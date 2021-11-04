import { ConfirmSMS } from "src/pages/two-factor/sms/confirm";
import React from "react";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Confirm",
  component: ConfirmSMS,
};

export const Page = (args) => {
  const appLogic = {};
  return <ConfirmSMS appLogic={appLogic} />;
};

Page.argTypes = {};
