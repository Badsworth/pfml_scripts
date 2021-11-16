import { ConfirmSMS } from "src/pages/two-factor/sms/confirm";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Confirm",
  component: ConfirmSMS,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();
  return <ConfirmSMS appLogic={appLogic} />;
};
