import React from "react";
import { VerifySMS } from "src/pages/two-factor/sms/verify";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Verify",
  component: VerifySMS,
};

export const Page = (args) => {
  const appLogic = {};
  return <VerifySMS appLogic={appLogic} />;
};

Page.argTypes = {};
