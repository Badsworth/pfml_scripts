import React from "react";
import { SetupSMS } from "src/pages/two-factor/sms/index";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Index",
  component: SetupSMS,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();
  return <SetupSMS appLogic={appLogic} />;
};
